
#Libraries
from bs4 import BeautifulSoup
import pandas as pd
import pymysql
from sqlalchemy import create_engine

#Loading HTML file
r = open("MPDCOS.html", "r").read() #Opens HTML file
BSParsedWebsite = BeautifulSoup(r, 'html.parser').find('table') #Parse HTML file and locates the table

#Creates list of column names
ColumnNamesList = []
for i in BSParsedWebsite.find('thead').find_all('tr')[1].findAll('th'): #Locates header of table and selects the correct lines, then iterates through them
    ColumnNamesList.append(i.text) #Appends the text contents (Column Names) to a list
ColumnNamesList.append('Last Updated')

DateTime = BSParsedWebsite.find('thead').find_all('input',type="submit",value="Refresh")[0].text[10:-8] #Records the "Last Updated" field from the website

#Creates a dataframe from website
NewData = []
for DataTable in BSParsedWebsite.find('tbody').find_all('tr'): #Iterates through all rows of the table
    row = [tr.text for tr in DataTable.find_all('td')] #Iterates through the columns of the row
    row.append(DateTime) #Inserts "Last Updated" data
    NewData.append(row) #Adds row to Data
Data = pd.DataFrame(NewData, columns =ColumnNamesList) #Converts list to pandas df

#Connects to database
connection = pymysql.connect(host='localhost',user='root',password='newPass',db='TestDataBase_INDSDS')
my_cursor = connection.cursor()

engine = create_engine("mysql+pymysql://{user}:{pw}@localhost/{db}" # create sqlalchemy engine
                       .format(user="root", pw="newPass",db="TestDataBase_INDSDS"))

#Removes entries that would be duplicates
#my_cursor.execute("SELECT * from MPDCOS") #Pulls all data from database
my_cursor.execute("SELECT *, left(MPDCOS.`Last Updated`,10) FROM MPDCOS RIGHT JOIN (SELECT DATE_FORMAT(DATE_SUB(STR_TO_DATE(SUBSTRING(MAX(`Last Updated`), 1, 10),'%m/%d/%Y'),INTERVAL 1 DAY),'%m/%d/%Y') as PrevDay, SUBSTRING(MAX(`Last Updated`), 1, 10) as CurrentDay FROM MPDCOS) a ON (a.CurrentDay = left(MPDCOS.`Last Updated`,10) OR a.PrevDay = left(MPDCOS.`Last Updated`,10));") #Pulls only the last 2 days of data from the database
result = my_cursor.fetchall()
DataBaseData = pd.DataFrame(result,columns = ColumnNamesList) #Creates Dataframe with all data in database
SendToDatabase = (pd.merge(Data,DataBaseData, indicator=True, how='outer') #removes any values in Data that already exist in database
         .query('_merge=="left_only"')
         .drop('_merge', axis=1))

#Inserts remaining entries into database
#DataTest = pd.DataFrame([["a","a","a","a","a","a","a"]],columns=ColumnNamesList)
SendToDatabase.to_sql("MPDCOS", con = engine, if_exists = 'append', chunksize = 1000,index= False)

#Disconnects from database?
connection.close()
 
