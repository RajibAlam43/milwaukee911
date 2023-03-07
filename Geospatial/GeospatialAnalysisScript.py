
import pandas as pd
import pymysql
from sqlalchemy import create_engine
import numpy as np
import json
import shapely.geometry as sh
from sklearn.neighbors import KernelDensity


ColumnNames = ['ID','Location','Latitude','Longitude','Processed Location'] #Names of columsn in database, ID is autoincrement primary key

connection = pymysql.connect(host='pascal.mscsnet.mu.edu',user='project1',password='ThisIsATest',db='MPD')
my_cursor = connection.cursor()

#Pull all non-null records that have been geocoded but have not been put into the view table
my_cursor.execute("SELECT c.* FROM MPD.GEOCODED c LEFT JOIN MPD.GEOSPATIAL_VIEW q ON q.ID = c.ID WHERE q.ID IS NULL AND c.Latitude IS NOT NULL;") 

result = my_cursor.fetchall() #brings results of query into python
Data = pd.DataFrame(result,columns = ColumnNames) #Converts query results into a pandas dataframe

with open("Geospatial\static\modified_mpd.geojson") as f:
  DistrictFeatures = json.load(f)["features"]

Districts = [[feature["properties"]["POLICE"],sh.shape(feature["geometry"]).buffer(0)] for feature in DistrictFeatures]

def ActualDistrict(x):
    output = 0
    LongLatPoint = sh.Point((x.Longitude,x.Latitude))
    for i in range(0,len(Districts)):
        if(Districts[i][1].contains(LongLatPoint)):
            output = Districts[i][0]
    return output


#Creating Column
ActualDistrictsList = Data.apply(ActualDistrict,axis = 1)
DummyCallDensityList = [np.nan] * len(Data.Latitude)
BarProximityList =  [np.nan] * len(Data.Latitude)


#Send to database
SendToGeoView = pd.DataFrame(np.column_stack([Data.ID, ActualDistrictsList, DummyCallDensityList, BarProximityList,]),
    columns= ["ID","Actual District","Call Density","Bar Proximity"])

engine = create_engine("mysql+pymysql://{user}:{pw}@pascal.mscsnet.mu.edu/{db}" # create sqlalchemy engine
            .format(user="project1", pw="ThisIsATest",db="MPD"))

#Inserts dataframe into MPD.GEOCODED table in the database
SendToGeoView.to_sql("GEOSPATIAL_VIEW", con = engine, if_exists = 'append', chunksize = 1000,index= False)

#Call Density
my_cursor.execute("SELECT * FROM MPD.GEOCODED WHERE Latitude IS NOT NULL;")  #Pulls all geocoded records to update density

result = my_cursor.fetchall() #brings results of query into python
AllGeocoded = pd.DataFrame(result,columns = ColumnNames) #Converts query results into a pandas dataframe

Lat = (pd.to_numeric(AllGeocoded.Latitude)-43) * 100
Long = (pd.to_numeric(AllGeocoded.Longitude)+87) * 100

DensityFunc = KernelDensity(kernel="gaussian", bandwidth=.35)
LatLong = np.vstack([Lat, Long]).T
DensityFunc.fit(LatLong)

CallDensityList = np.exp(DensityFunc.score_samples(LatLong)).tolist()

SendToGeoView2 = pd.DataFrame(np.column_stack([AllGeocoded.ID,CallDensityList]), columns= ['ID', 'Call Density'])
SendToGeoView2.to_sql("DENSITY_LANDING", con = engine, if_exists = 'append', chunksize = 1000, index= False)

my_cursor.execute("UPDATE MPD.GEOSPATIAL_VIEW GSV INNER JOIN MPD.DENSITY_LANDING DL ON GSV.ID = DL.ID SET GSV.`Call Density` = DL.`Call Density`;")  #Joins Updated Density with GEOSPATIAL_VIEW
my_cursor.execute("DELETE FROM MPD.DENSITY_LANDING;")  #Deletes Landing Table Data
connection.commit()
connection.close()

