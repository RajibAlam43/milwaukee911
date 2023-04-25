#!/usr/bin/env python
# coding: utf-8

# In[49]:


import pandas as pd
import pymysql
from sqlalchemy import create_engine
import numpy as np

ColumnNames = ['ID','Call Number','Date/Time','Location','Police District','Nature of Call','Status','Last Updated'] #Names of columsn in database, ID is autoincrement primary key

connection = pymysql.connect(host='pascal.mscsnet.mu.edu',user='project1',password='ThisIsATest',db='MPD')
myCursor = connection.cursor()

#Pull a max of 100 records which do not exist (have their ID) in the BINS table (10 records)
myCursor.execute("SELECT c.*  FROM MPD.MPDCOS c LEFT JOIN MPD.BINS q ON q.ID = c.ID WHERE q.ID IS NULL ORDER BY RAND() LIMIT 10;")

result = myCursor.fetchall() #brings results of query into python
df = pd.DataFrame(result,columns = ColumnNames)


# In[50]:


dayColumn = pd.to_datetime(df['Date/Time']).dt.dayofweek
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def getDay(p):
    return days[p]


# In[51]:


times = ["Early Night", "Late Night", "Early Morning", "Late Morning", "Early Afternoon", "Late Afternoon", "Early Evening", "Late Evening"]
timeColumn = pd.to_datetime(df['Date/Time']).dt.time

    
def getTime(p):
    return p


# In[52]:


import openpyxl

nc = []
nvc = []
vc = []

workbook = openpyxl.load_workbook('call type.xlsx')
worksheet = workbook.active

for row in worksheet.iter_rows(values_only=True):
    value1 = row[0]
    value2 = row[2]
    
    if value2 == "NC":
        nc.append(value1)
    if value2 == "NVC":
        nvc.append(value1)
    if value2 == "VC":
        vc.append(value1)


# In[53]:


callColumn = df.astype({'Nature of Call':'string'})
callColumn = df["Nature of Call"]
callColumn

def getCallType(p):
    if p in nc:
        return "Non Crime"
    if p in nvc:
        return "Non-violent Crime"
    if p in vc:
        return "Violent Crime"


# In[54]:


#Combines relevant fields into a pandas dataframe
SendToDatabase = pd.DataFrame(np.column_stack([df.ID, dayColumn.apply(getDay), timeColumn.apply(getTime), callColumn.apply(getCallType),]),
    columns= ["ID","Day","Time", "Crime Type"])


engine = create_engine("mysql+pymysql://{user}:{pw}@pascal.mscsnet.mu.edu/{db}" # create sqlalchemy engine
            .format(user="project1", pw="ThisIsATest",db="MPD"))

#Inserts dataframe into MPD.GEOCODED table in the database
SendToDatabase.to_sql("BINS", con = engine, if_exists = 'append', chunksize = 1000,index= False)


#Disconnects from database
connection.commit()
connection.close()

