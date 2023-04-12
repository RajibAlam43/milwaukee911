import re
import pandas as pd
import pymysql
from sqlalchemy import create_engine
import geopy
from geopy.geocoders import Nominatim
from shapely.geometry import Polygon, LineString, multipoint,point
from sklearn.linear_model import LinearRegression
import numpy as np
from python_tsp.distances import great_circle_distance_matrix
from python_tsp.heuristics import solve_tsp_simulated_annealing


ColumnNames = ['ID','Call Number','Date/Time','Location','Police District','Nature of Call','Status','Last Updated'] #Names of columsn in database, ID is autoincrement primary key

connection = pymysql.connect(host='pascal.mscsnet.mu.edu',user='project1',password='ThisIsATest',db='MPD')
my_cursor = connection.cursor()

#Pull a max of 100 records which do not exist (have their ID) in the GEOCODED table
my_cursor.execute("SELECT c.*  FROM MPD.MPDCOS c LEFT JOIN MPD.GEOCODED q ON q.ID = c.ID WHERE q.ID IS NULL ORDER BY RAND() LIMIT 10;") 
#my_cursor.execute("SELECT c.*  FROM MPD.MPDCOS c LEFT JOIN MPD.GEOCODED q ON q.ID = c.ID WHERE q.ID IS NULL AND c.`Nature of Call` = 'SHOTSPOTTER' ORDER BY RAND() LIMIT 300;")

result = my_cursor.fetchall() #brings results of query into python
Data = pd.DataFrame(result,columns = ColumnNames) #Converts query results into a pandas dataframe

OriginalLocation = list(Data.iloc[:,3]) #Saves the Location column before we clean it


def getLat(p): #Retrieves the Latitude for any of the possible output types we get
    if(isinstance(p, multipoint.MultiPoint)):
        return(p.geoms[0].y)  
    if(isinstance(p, point.Point)):
        return(p.y)
    if(isinstance(p, geopy.Location)):
        return(p.latitude)

def getLong(p): #Retrieves the Longitude for any of the possible output types we get
    if(isinstance(p, multipoint.MultiPoint)):
        return(p.geoms[0].x)  
    if(isinstance(p, point.Point)):
        return(p.x)
    if(isinstance(p, geopy.Location)):
        return(p.longitude)

geolocator = Nominatim(user_agent="GeoSpatialMPDCOS") #We are using the Nominatim goecoder

def FixIntersection(x): #Takes in a row of the dataset
    [FirstStreet,SecondStreet] = ["",""] #initialize Variables for our streets
    Output = "" #Initialize output variable
    BugFixingDict = {} #Initialize a dictionary that is used to help make our execute statements work 
    x_Location = x[3] #Extracts Location column from the row
    if(" / " in x_Location):    #Checks if it is an intersection - intersections contain a " / "
        [FirstStreet,SecondStreet] = x_Location.split(' / ')    #Splits Location into the two streets
        FirstStreet = FirstStreet + ", MILWAUKEE, WI"       #Adds the City & Country to the first street since it is only listed with the second
        ListLocations1 = geolocator.geocode(FirstStreet,exactly_one=False)  #list of all Locations associated with the first street
        ListLocations2 = geolocator.geocode(SecondStreet,exactly_one=False)    #list of all Locations associated with the second street
        if(ListLocations1 is None or ListLocations2 is None): #Checks to make sure both streets can be found - if one or both cannot be found then we do not need to run the rest of the function
            Output = LineString([(1,0), (1,2)]).intersection(LineString((1,4),(1,6))) #Sets it to 2 lines that do not intersect, this keeps our unmapped values syntax consistent
            if(ListLocations1 is None):
                print(ListLocations1) #If this occurs we will not get a point and so this will print the unmapped location to our logs
            if(ListLocations1 is None):
                print(ListLocations2) #If this occurs we will not get a point and so this will print the unmapped location to our logs
        else:
            #The first approach looks for an intersection between street data that exits in a common neighborhood between the 2 streets
            #Locates common neighborhood(s) for the two streets if it exists
            CommonNeighborhood = (set([i.address.split("Milwaukee, Milwaukee County ")[0].split(", ")[1] for i in ListLocations1]).intersection([i.address.split("Milwaukee, Milwaukee County ")[0].split(", ")[1] for i in ListLocations2]))
            if(len(CommonNeighborhood) != 0 ): #If a common neighborhood exists
                CorrectLocation1 = [s for s in ListLocations1 if (str(next(iter(CommonNeighborhood)))) in s.address][0] #Finds the full address for the street in the common neighborhood 
                CorrectLocation2 = [s for s in ListLocations2 if (str(next(iter(CommonNeighborhood)))) in s.address][0]
                GeoText1 = geolocator.geocode(CorrectLocation1.address, geometry ='wkt').raw["geotext"] #pulls the latitude and logitude coordinates (in the form of a Polygon, Linestring or Point) for the street at that full address
                GeoText2 = geolocator.geocode(CorrectLocation2.address, geometry ='wkt').raw["geotext"]
                #The .raw["geotext"] for Location object is pretty easy to rework into executable code that saves all the lat/long as a list of tuples - this is definitely not the most optimal way to do this, will maybe fix later
                exec(GeoText1.replace("LINESTRING(","LS1=[(").replace("POLYGON((","LS1=[(").replace("POINT(","LS2=[(").replace("))","]").replace(")",")]").replace(" ",";").replace(",","), (").replace(";",", "),globals(),BugFixingDict)
                exec(GeoText2.replace("LINESTRING(","LS2=[(").replace("POLYGON((","LS2=[(").replace("POINT(","LS2=[(").replace("))",")").replace(")",")]").replace(" ",";").replace(",","), (").replace(";",", "),globals(),BugFixingDict)
                LS1 = BugFixingDict["LS1"] #This process is required in order to deal with exec() inside of a python function
                LS2 = BugFixingDict["LS2"] #It is basically just saving the Latitude & Longitude from the .raw["geotext"] as a list of tuples
            else: #There is no common neighborhood
                LS1 = [(1,0), (1,2)] #sets the lat/ lng to 2 lines that will not intersect so that it will try the next method
                LS2 = [(1,4),(1,6)]
            #If common neighborhood approach doesn't work either because an intersection couldn't be found or there was no common neighborhood
            #Then we try using all the listed location objects for the street at once
            if(LineString(LS1).intersects(LineString(LS2)) == False):  #checks to see if common neighborhood approach worked
                LS1 = [] #Reset our lists of lat/lng
                LS2 = []
                for i in ListLocations1: #For every Location we found:
                    GeoText1 = geolocator.geocode(i.address, geometry ='wkt').raw["geotext"] #< pull out the .raw["geotext"], \/ Turns that it into a list of tuples
                    exec(GeoText1.replace("LINESTRING(","LS1=[(").replace("POLYGON((","LS1=[(").replace("POINT(","LS1=[(").replace("))",")").replace(")",")]").replace(" ",";").replace(",","), (").replace(";",", "),globals(),BugFixingDict)
                    LS1add = BugFixingDict["LS1"] 
                    LS1 = LS1 + LS1add #Each loop adds all the lat/lng values we found to the list
                #The lines connecting lat/ lng data for each street will not be perfectly straight, this means that if we take the points "out of order" we may get an incorrect intersection point
                #To deal with this we can use an approximate solver for the traveling salesman problem (TSP) in order to connect the points
                distance_matrix = great_circle_distance_matrix(np.array(LS1)) #creates a distance matrix so we can solve TSP
                permutation = solve_tsp_simulated_annealing(distance_matrix)[0] #Solves TSP using a metaheuristic
                LS1 = [tuple(S) for S in np.array(LS1)[permutation]] #Rearranges the data so that it is "in order", lines connecting the points should now follow the actual path of the street better
                for j in ListLocations2: #repeats process for the second street
                    GeoText2 = geolocator.geocode(j.address, geometry ='wkt').raw["geotext"]
                    exec(GeoText2.replace("LINESTRING(","LS2=[(").replace("POLYGON((","LS2=[(").replace("POINT(","LS2=[(").replace("))",")").replace(")",")]").replace(" ",";").replace(",","), (").replace(";",", "),globals(),BugFixingDict)
                    LS2add = BugFixingDict["LS2"]
                    LS2 = LS2 + LS2add
                distance_matrix = great_circle_distance_matrix(np.array(LS2))
                permutation = solve_tsp_simulated_annealing(distance_matrix)[0]
                LS2 = [tuple(S) for S in np.array(LS2)[permutation]]
                LS1Out = pd.DataFrame(LS1,columns = ['Lng','Lat'])
                LS2Out = pd.DataFrame(LS2,columns = ['Lng','Lat'])
            #if using all listed locations at once does not find an intersection then the issue may be that our lat/lng data does not extend through the point where the streets will intersect
            #this is especially common if a street ends at the interection
            #To address this we can create 2 linear regression models to predict where the streets would extend to
            #One flaw with this method is it assumes that streets will be vaguely straight which is not always the case
            if(LineString(LS1).intersects(LineString(LS2)) == False): #Checks to see if using all listed locations at once does not work
                MinLng = min(LS1Out["Lng"].min(),LS2Out["Lng"].min()) -.05 #Creates a lng value that is significantly below any of our values
                MaxLng = max(LS1Out["Lng"].max(),LS2Out["Lng"].max()) +.05 #Creates a lng value that is significantly above any of our values
                MinLat = min(LS1Out["Lat"].min(),LS2Out["Lat"].min()) -.05 #Creates a lat value that is significantly to the left of any of our values
                MaxLat = max(LS1Out["Lat"].max(),LS2Out["Lat"].max()) +.05 #Creates a lat value that is significantly to the right of any of our values
                model1 = LinearRegression() #Initializes model for street 1
                if(np.std(LS1Out["Lat"]) > np.std(LS1Out["Lng"])): #if the data for the street is going mostly EAST-WEST then we want to predict a Lng value with Lat
                    model1.fit(np.array(LS1Out["Lat"]).reshape(-1,1),LS1Out["Lng"]) #trains the model
                    EstMin1 = model1.predict(np.array(MinLat).reshape(-1,1)) #Predicts a lng value at our significantly distanced lat point
                    EstMax1 = model1.predict(np.array(MaxLat).reshape(-1,1))
                    ForcedLS1 = [(EstMin1[0],MinLat),(EstMax1[0],MaxLat)] #Creates a list of our 2 significantly distanced points predicted using the linear regression model
                else:   #if the data for the street is going mostly NORTH-SOUTH then we want to predict a lat value with lng
                    model1.fit(np.array(LS1Out["Lng"]).reshape(-1,1),LS1Out["Lat"])
                    EstMin1 = model1.predict(np.array(MinLng).reshape(-1,1)) #Predicts a lat value at our significantly distanced lng point
                    EstMax1 = model1.predict(np.array(MaxLng).reshape(-1,1))
                    ForcedLS1 = [(MinLng,EstMin1[0]),(MaxLng,EstMax1[0])]
                #Repeats the process for the second street
                model2 = LinearRegression()
                if(np.std(LS2Out["Lat"]) > np.std(LS2Out["Lng"])):
                    model2.fit(np.array(LS2Out["Lat"]).reshape(-1,1),LS2Out["Lng"])
                    EstMin2 = model2.predict(np.array(MinLat).reshape(-1,1))
                    EstMax2 = model2.predict(np.array(MaxLat).reshape(-1,1))
                    ForcedLS2 = [(EstMin2[0],MinLat),(EstMax2[0],MaxLat)]
                else:
                    model2.fit(np.array(LS2Out["Lng"]).reshape(-1,1),LS2Out["Lat"])
                    EstMin2 = model2.predict(np.array(MinLng).reshape(-1,1))
                    EstMax2 = model2.predict(np.array(MaxLng).reshape(-1,1))
                    ForcedLS2 = [(MinLng,EstMin2[0]),(MaxLng,EstMax2[0])]
                Output = LineString(ForcedLS1).intersection(LineString(ForcedLS2)) #saves the output as the intersection of the 2 lines constructed using the 4 distanced/predicted points
            else: #if Common Neighborhood or using all listed locatiosn worked
                Output = LineString(LS1).intersection(LineString(LS2)) #save the output as the intersection between the two lines we found
        return Output



#Some Data cleaning

Data.loc[Data.iloc[:,3] == "GALLS","Location"] = "500 E OAK ST, OAK CREEK, WI" #GALLS is Police equipment store in oak creek
Data.loc[Data.iloc[:,3] == "GALLS, OAK CREEK","Location"] = "500 E OAK ST, OAK CREEK, WI"
Data.loc[Data.iloc[:,3] == "GALL'S UNIFORM - OAK CREEK","Location"] = "500 E OAK ST, OAK CREEK, WI"
Data.loc[Data.iloc[:,3] == "GALL'S - OAK CREEK","Location"] = "500 E OAK ST, OAK CREEK, WI"
Data.loc[Data.iloc[:,3] == "STREICHERS","Location"] = "4777 N 124th ST, BUTLER, WI" #STREICHERS is Police equipment store in Butler  


Data.loc[Data.iloc[:,3] == "FRANKLIN POLICE DEPT","Location"] = "455 W Loomis Rd, Franklin, WI"

Data.loc[Data.iloc[:,3] == "D1","Location"] = "749 W STATE ST,MKE"  #There records appear to be police stations for each district based on "nature of call" column
Data.loc[Data.iloc[:,3] == "D2","Location"] = "245 W LINCOLN AV,MKE"
Data.loc[Data.iloc[:,3] == "D3","Location"] = "2333 N 49TH ST,MKE"   
Data.loc[Data.iloc[:,3] == "D4","Location"] = "6929 W SILVER SPRING DR,MKE"   
Data.loc[Data.iloc[:,3] == "D5","Location"] = "2920 N VEL R PHILLIPS AV,MKE"   
Data.loc[Data.iloc[:,3] == "D6","Location"] = "3006 S 27TH ST,MKE"
Data.loc[Data.iloc[:,3] == "D7","Location"] = "3626 W FOND DU LAC AV,MKE"

Data.iloc[:,3] = Data.iloc[:,3].str.replace(",MKE", ", MILWAUKEE, WI") #replaces occurances of  ",MKE" with  ", MILWAUKEE, WI" in the Location column
Data.iloc[:,3] = Data.iloc[:,3].str.replace(",BUT", ", BUTLER, WI")
Data.iloc[:,3] = Data.iloc[:,3].str.replace("OAKCREEK", "OAK CREEK, WI")
Data.iloc[:,3] = Data.iloc[:,3].str.replace("GFD", " GREENFIELD, WI")
Data.iloc[:,3] = Data.iloc[:,3].str.replace("WMW", " MILWAUKEE, WI")
#for Location records that end in ",WAU" replaces occurances of  ",WAU" with  ", WAUWATOSA, WI" in the Location column
Data.loc[Data["Location"].apply(lambda x: x.endswith(",WAU")),"Location"] =Data.loc[Data["Location"].apply(lambda x: x.endswith(",WAU")),"Location"].str.replace(",WAU", ", WAUWATOSA, WI")
Data.loc[Data["Location"].apply(lambda x: x.endswith(", WAU")),"Location"] =Data.loc[Data["Location"].apply(lambda x: x.endswith(", WAU")),"Location"].str.replace(", WAU", ", WAUWATOSA, WI")
Data.loc[Data["Location"].apply(lambda x: x.endswith(",WA")),"Location"] =Data.loc[Data["Location"].apply(lambda x: x.endswith(",WA")),"Location"].str.replace(",WA", ", WEST ALLIS, WI")
Data.loc[Data["Location"].apply(lambda x: x.endswith(", WA")),"Location"] =Data.loc[Data["Location"].apply(lambda x: x.endswith(", WA")),"Location"].str.replace(", WA", ", WEST ALLIS, WI")
Data.iloc[:,3] = Data.iloc[:,3].str.replace(",BD", ", BROWN DEER, WI")
Data.iloc[:,3] = Data.iloc[:,3].str.replace(",STF", ", SAINT FRANCIS, WI")
Data.iloc[:,3] = Data.iloc[:,3].str.replace(",MF", ", MENOMONEE FALLS, WI")
Data.iloc[:,3] = Data.iloc[:,3].str.replace("OCR", " OAK CREEK, WI")
Data.iloc[:,3] = Data.iloc[:,3].str.replace(", SHOREWOOD", ", SHOREWOOD, WI")
Data.iloc[["," not in x for x in Data.iloc[:,3]],3] = Data.iloc[["," not in x for x in Data.iloc[:,3]],3] + ", MILWAUKEE, WI" #adds city + state to any record that doesn't have
Data.iloc[:,3] = Data.iloc[:,3].str.replace("-BLK", "") #removes -BLK prefix so we just find "first" address on the block
Data.iloc[:,3] = Data.iloc[:,3].str.replace(" BL,", " BLVD,")
Data.iloc[:,3] = Data.iloc[:,3].str.replace(" BL ", " BLVD ")
Data.iloc[:,3] = Data.iloc[:,3].str.replace(" CR,", " CIR,")
Data.iloc[:,3] = Data.iloc[:,3].str.replace(" CR ", " CIR ")
Data.iloc[:,3] = Data.iloc[:,3].str.replace("BLUE MOUND", "BLUEMOUND")
Data.iloc[:,3] = Data.iloc[:,3].str.replace(" TR,", " TERRACE")
Data.iloc[:,3] = Data.iloc[:,3].str.replace(" TR ", " TERRACE ")
Data.iloc[:,3] = Data.iloc[:,3].str.replace("ALLYN CT", "ALLYN ST,") #bad data quality
Data.iloc[:,3] = Data.iloc[:,3].str.replace(" MC ", " MC") #Fixes prefix MC (ex: MC DONALDS -> MCDONALDS)
Data.iloc[:,3] = Data.iloc[:,3].str.replace(" WA,", " WAY,")
Data.iloc[:,3] = Data.iloc[:,3].str.replace(" WA ", " WAY ")
Data.iloc[:,3] = Data.iloc[:,3].str.replace("N MARTIN L KING JR DR", "N 3RD ST") #The name of N MARTIN L KING JR DR is outdated in the nominatim database
Data.iloc[:,3] = Data.iloc[:,3].str.replace("LINWAL AV", " LINWAL LANE") #bad data quality



BroadwayLocation = geolocator.geocode("N BROADWAY, MILWAUKEE, WI",geometry ='wkt')
CenterLocation = geolocator.geocode("W CENTER ST, North Division, MILWAUKEE, WI",geometry ='wkt')
MartinLutherLocation =  geolocator.geocode("N 3RD ST, MILWAUKEE, WI",geometry ='wkt')

def AdjustedGeocoding(Address):
    GeoLocation= geolocator.geocode(Address, geometry ='wkt')
    if(GeoLocation is not None):
        if(GeoLocation == BroadwayLocation):
            return geolocator.geocode(Address.replace("BROADWAY","BROADWAY ST"),geometry ='wkt')
        elif('geotext' in GeoLocation.raw):
            if(GeoLocation.raw["geotext"] == CenterLocation.raw["geotext"]):
                return FixIntersection(["Dummy1","Dummy2","Dummy3",re.match(r'^(\d+)', Address).group(1)[:-2] + "TH ST / W CENTER ST, MILWAUKEE, WI"])
            elif(GeoLocation.raw["geotext"] == MartinLutherLocation.raw["geotext"]):
                return geolocator.geocode(Address.replace("3RD ST", "DOCTOR MARTIN LUTHER KING JUNIOR DR"),geometry ='wkt')
            else:
                return GeoLocation
        else:
            return GeoLocation
    else:
        return GeoLocation

Intersections = Data.apply(FixIntersection,axis = 1) #calls the FixIntersections funciton of the Data we retreived from SQL, saves the fixed intersections as "Intersections"

geolocate_column = Data.iloc[:,3].apply(AdjustedGeocoding) #finds the Location object for every entry in the location column (This will not work on the intersections)

geolocate_column[geolocate_column.apply(lambda x: x is None)] = Intersections[geolocate_column.apply(lambda x: x is None)] #Inserts the fixed intersections in with the Location data

#TODO
#Fix Stacks:
#380 W CAPITOL DR,MKE 
#3300 W CENTER ST,MKE
#220 S 1ST ST,MKE




#Combines relevant fields into a pandas dataframe
SendToDatabase = pd.DataFrame(np.column_stack([Data.ID, OriginalLocation, geolocate_column.apply(getLat), geolocate_column.apply(getLong),Data.Location,]),
    columns= ["ID","Location","Latitude","Longitude","Processed Location"])


engine = create_engine("mysql+pymysql://{user}:{pw}@pascal.mscsnet.mu.edu/{db}" # create sqlalchemy engine
            .format(user="project1", pw="ThisIsATest",db="MPD"))

#Inserts dataframe into MPD.GEOCODED table in the database
SendToDatabase.to_sql("GEOCODED", con = engine, if_exists = 'append', chunksize = 1000,index= False)

# print(SendToDatabase)
# print(SendToDatabase.iloc[92,4])
# print(SendToDatabase.iloc[91,3])

#Copies the Geocoded Data into MPD.GEOCODED for any MPD.MPDCOS entries with a Location that has been checked already
my_cursor.execute("INSERT INTO MPD.GEOCODED (ID, Location, Latitude, Longitude, `Processed Location`) SELECT  DISTINCT(q.ID), c.Location, c.Latitude, c.Longitude, c.`Processed Location` FROM MPD.GEOCODED c LEFT JOIN (SELECT a.*  FROM MPD.MPDCOS a LEFT JOIN MPD.GEOCODED b ON b.ID = a.ID WHERE b.ID IS NULL) q ON q.Location = c.Location WHERE q.ID IS NOT NULL LIMIT 100;")


#Disconnects from database
connection.commit()
connection.close()