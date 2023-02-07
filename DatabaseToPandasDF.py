import pandas as pd
import pymysql
from sqlalchemy import create_engine

ColumnNames = ['ID','Call Number','Date/Time','Location','Police District','Nature of Call','Status','Last Updated'] #Names of columsn in database, ID is autoincrement primary key

connection = pymysql.connect(host='pascal.mscsnet.mu.edu',user='project1',password='ThisIsATest',db='MPD')
my_cursor = connection.cursor()
engine = create_engine("mysql+pymysql://{user}:{pw}@pascal.mscsnet.mu.edu/{db}" # create sqlalchemy engine
            .format(user="project1", pw="ThisIsATest",db="MPD"))


my_cursor.execute("SELECT * FROM MPDCOS;") #Put SQL statement here
result = my_cursor.fetchall()
Data = pd.DataFrame(result,columns = ColumnNames) #Converts into a pandas dataframe

print(Data)