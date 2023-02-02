import pandas as pd
import requests
import bs4
import csv
from bs4 import BeautifulSoup
import pymysql
from sqlalchemy import create_engine
import os
import datetime

def tableDataText(table2):    
    """Parses a html segment started with tag <table> followed 
    by multiple <tr> (table rows) and inner <td> (table data) tags. 
    It returns a list of rows with inner columns. 
    Accepts only one <th> (table header/data) in the first row.
    """
    def rowgetDataText(tr, coltag='td'): # td (data) or th (header)       
        return [td.get_text(strip=True) for td in tr.find_all(coltag)]  
    rows = []
    trs = table[0].find_all('tr')
    headerow = rowgetDataText(trs[0], 'th')
    if headerow: # if there is a header row include first
        rows.append(headerow)
        trs = trs[2:]
    for tr in trs: # for every table row
        rows.append(rowgetDataText(tr, 'td') ) # data row       
    return rows


url = "https://itmdapps.milwaukee.gov/MPDCallData/index.jsp?district=All"

response = requests.get(url) 
filename_format = "mpd_call_data_{}.html".format(datetime.datetime.now().strftime("%m-%d-%Y_%H-%M-%S"))        
with open(filename_format, "w") as f:         
    f.write(response.text)  

soup = bs4.BeautifulSoup(response.content, 'lxml')
table = soup.find_all('tbody')

list_table = tableDataText(table)
blank_row = [['','','','','','']]

# field names 
fields = ['Call Number', 'Date/Time', 'Location', 'Police District', 'Nature of Call', 'Status'] 

# data rows of csv file 
rows = list_table

dir = os.path.dirname(__file__)

with open(dir+'/police_scrape_data.csv', 'a', newline='') as f:
    # using csv.writer method from CSV package
    write = csv.writer(f) 
    write.writerows(blank_row)
    write.writerows(rows)

###PARSING AND UPLOAD

#Loading HTML file
BSParsedWebsite = BeautifulSoup(response.content, 'html.parser').find('table') #Parse HTML file and locates the table

#Creates list of column names
ColumnNamesList = []
for i in BSParsedWebsite.find('thead').find_all('tr')[1].findAll('th'): #Locates header of table and selects the correct lines, then iterates through them
    ColumnNamesList.append(i.text.replace("'", '"')) #Appends the text contents (Column Names) to a list


DateTime = BSParsedWebsite.find('thead').find_all('input',type="submit",value="Refresh")[0].text[10:-8] #Records the "Last Updated" field from the website

#Creates a dataframe from website
NewData = []
for DataTable in BSParsedWebsite.find('tbody').find_all('tr'): #Iterates through all rows of the table
    NewData.append([tr.text for tr in DataTable.find_all('td')]) #Iterates through the columns of the row
Data = pd.DataFrame(NewData, columns =ColumnNamesList) #Converts list to pandas df

#Connects to database
connection = pymysql.connect(host='pascal.mscsnet.mu.edu',user='project1',password='ThisIsATest',db='MPD')
my_cursor = connection.cursor()

engine = create_engine("mysql+pymysql://{user}:{pw}@pascal.mscsnet.mu.edu/{db}" # create sqlalchemy engine
            .format(user="project1", pw="ThisIsATest",db="MPD"))

#Removes entries that would be duplicates
my_cursor.execute("SELECT * FROM MPDCOS RIGHT JOIN (SELECT DATE_FORMAT(DATE_SUB(STR_TO_DATE(SUBSTRING(MAX(`Last Updated`), 1, 10),'%m/%d/%Y'),INTERVAL 1 DAY),'%m/%d/%Y') as PrevDay, SUBSTRING(MAX(`Last Updated`), 1, 10) as CurrentDay FROM MPDCOS) a ON (a.CurrentDay = left(MPDCOS.`Last Updated`,10) OR a.PrevDay = left(MPDCOS.`Last Updated`,10));") #Pulls only the last 2 days of data from the database
result = my_cursor.fetchall()
DataBaseData = pd.DataFrame(result,columns = ["Delete1"] + ColumnNamesList + ["Last Updated","Delete2","Delete3"]) #Creates Dataframe with all data in database

SendToDatabase = (pd.merge(Data,DataBaseData.drop(["Delete1","Delete2","Delete3","Last Updated"],axis =1), indicator=True, how='outer') #removes any values in Data that already exist in database
    .query('_merge=="left_only"')
    .drop('_merge', axis=1))

SendToDatabase["Last Updated"] = DateTime #Adds Last Updated Column

#Inserts remaining entries into database
SendToDatabase.to_sql("MPDCOS", con = engine, if_exists = 'append', chunksize = 1000,index= False)

#Disconnects from database?
connection.close()
