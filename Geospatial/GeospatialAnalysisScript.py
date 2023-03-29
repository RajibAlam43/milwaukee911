
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

with open(r"Geospatial\static\modified_mpd.geojson") as f: #this needs to be used for SSH to understand it when we upload this script to run on crontab
#with open("Geospatial\static\modified_mpd.geojson") as f:
  DistrictFeatures = json.load(f)["features"]

Districts = [[feature["properties"]["POLICE"],sh.shape(feature["geometry"]).buffer(0)] for feature in DistrictFeatures]

def ActualDistrict(x):
    output = 0
    LongLatPoint = sh.Point((x.Longitude,x.Latitude))
    for i in range(0,len(Districts)):
        if(Districts[i][1].contains(LongLatPoint)):
            output = Districts[i][0]
    return output

def isAdmin(x):
    #TODO ADD CHECK TO MAKE SURE IT IS ADMINISTRATIVE CALL
    if(x["Processed Location"] in ["6929 W SILVER SPRING DR, MILWAUKEE, WI", '749 W STATE ST, MILWAUKEE, WI', '4715 W VLIET ST, MILWAUKEE, WI', '6929 W SILVER SPRING DR, MILWAUKEE, WI',
                                    '3626 W FOND DU LAC AV, MILWAUKEE, WI', '2333 N 49TH ST, MILWAUKEE, WI','2920 N VEL R PHILLIPS AV, MILWAUKEE, WI','245 W LINCOLN AV, MILWAUKEE, WI',
                                    '3006 S 27TH ST, MILWAUKEE, WI']):
        return "HQ"
    if(x["Processed Location"] in ["500 E OAK ST, OAK CREEK, WI", "4777 N 124TH ST, BUTLER, WI"]):
        return "Equipment"
    if(x["Processed Location"] in ["949 N 9TH ST, MILWAUKEE, WI"]):
        return "Jail"
    if(x["Processed Location"] in ["901 N 9TH ST, MILWAUKEE, WI","951 N JAMES LOVELL ST, MILWAUKEE, WI"]):
        return "Courthouse"
    if(x["Processed Location"] in ["6680 N TEUTONIA AV, MILWAUKEE, WI"]):
        return "Training"
    if(x["Processed Location"] in ["933 W HIGHLAND AV, MILWAUKEE, WI"]):
        return "Medical Examiner"
    else:
        return False
    
    
    
    

#Creating Column
ActualDistrictsList = Data.apply(ActualDistrict,axis = 1)
DummyCallDensityList = [np.nan] * len(Data.Latitude)
BarProximityList =  [np.nan] * len(Data.Latitude)
AdministrativeLocationList = Data.apply(isAdmin, axis = 1)


#Send to database
SendToGeoView = pd.DataFrame(np.column_stack([Data.ID, ActualDistrictsList, DummyCallDensityList, BarProximityList,AdministrativeLocationList]),
    columns= ["ID","Actual District","Call Density","Bar Proximity","Is Administrative Location"])

engine = create_engine("mysql+pymysql://{user}:{pw}@pascal.mscsnet.mu.edu/{db}" # create sqlalchemy engine
            .format(user="project1", pw="ThisIsATest",db="MPD"))

#Inserts dataframe into MPD.GEOCODED table in the database
SendToGeoView.to_sql("GEOSPATIAL_VIEW", con = engine, if_exists = 'append', chunksize = 1000,index= False)
connection.commit()

#Call Density
my_cursor.execute("SELECT g.* FROM MPD.GEOCODED g LEFT JOIN MPD.GEOSPATIAL_VIEW v on v.ID = g.ID WHERE g.Latitude IS NOT NULL AND v.`Is Administrative Location` = '0';")  #Pulls all geocoded records (-Admin) to update density

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
my_cursor.execute("UPDATE MPD.GEOSPATIAL_VIEW K RIGHT JOIN (SELECT g.ID FROM MPD.GEOCODED g LEFT JOIN MPD.GEOSPATIAL_VIEW v on v.ID = g.ID WHERE g.Latitude IS NOT NULL AND v.`Is Administrative Location` != '0') J on J.ID = K.ID SET K.`Call Density` = 0;")
connection.commit()
connection.close()

