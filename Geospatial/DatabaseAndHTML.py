from flask import Flask, render_template, jsonify
import json
from flask_caching import Cache
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import time
from flask_cors import CORS
import datetime
import pandas as pd

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://mpdcscapstone.cs.mu.edu:5000"}})


app = Flask(__name__, template_folder='./')
app.logger.debug('Flask Is Running')

CallTypesDict = pd.read_csv('Geospatial/CallType2.csv')
classifications = CallTypesDict.iloc[:,1]
CallTypeClassMap = dict(zip(CallTypesDict.iloc[:,0], classifications))

engine = create_engine("mysql+pymysql://{user}:{pw}@pascal.mscsnet.mu.edu/{db}" # create sqlalchemy engine
            .format(user="project1", pw="ThisIsATest",db="MPD"), pool_size=20, max_overflow=0)

cache = Cache(app, config={'CACHE_TYPE': 'simple'})
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

@app.route('/data')
@cache.cached(timeout=300)
def get_data():
    app.logger.debug("request made")
    start_time = time.time()
    session = db_session()
    cursor = session.execute("SELECT g.*, q.`Call Number`,q.`Date/Time`,q.`Police District`,q.`Nature of Call`,q.`Status`,q.`Last Updated`, q.`Actual District`,q.`Call Density`,q.`Bar Proximity`,q.`Is Administrative Location`,q.`ZipCode`  FROM MPD.GEOCODED g  LEFT JOIN (SELECT c.*, v.`Actual District`,v.`Call Density`,v.`Bar Proximity`,v.`Is Administrative Location`,v.`ZipCode` FROM MPD.MPDCOS c LEFT JOIN MPD.GEOSPATIAL_VIEW v on v.ID = c.ID) q on g.ID = q.ID WHERE g.Latitude IS NOT NULL AND q.`Call Density` IS NOT NULL;")
    db_data = cursor.fetchall()
    middle_time = time.time()
    geocoded = [(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14],row[15]) for row in db_data]
    #TODO Create bins for  Day of Week, & time of day,Crime Type
    call_density_scaling = 1 / max([float(row[12]) for row in db_data])
    DateTime = [row[6] for row in geocoded]
    DateTimeObject = [datetime.datetime.strptime(x, "%m/%d/%Y %I:%M:%S %p") for x in DateTime]
    NatureOfCall = [row[8] for row in geocoded]
    DayOfWeek = list(map(lambda x: x.strftime("%A"), DateTimeObject))
    TimeOfDay = list(map(lambda x: x.strftime("%H:%M:%S"), DateTimeObject))
    CallType = [CallTypeClassMap.get(call_type, 'NC') for call_type in NatureOfCall]
    geocoded = [(*row, day, time, call) for row, day, time, call in zip(geocoded, DayOfWeek, TimeOfDay, CallType)]
    end_time = time.time()
    dataExtractTime =  middle_time - start_time
    elapsed_time = end_time - start_time
    app.logger.debug("Optimized method took {:.3f} seconds to run.".format(elapsed_time))
    app.logger.debug(dataExtractTime)
    response =jsonify({"Geocoded": geocoded, "Constants": (call_density_scaling)})
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


# #Called 3 times, ApplyFilters()
# #PlotRelPoints(ApplyFilters())
# #PlotRelPoints(UpdateConstraints()) Caching means we don't have fetch the data for these next 2?

@app.route('/geojson')
def get_geojson():
    with open("./Geospatial/static/modified_mpd.geojson") as file:    
        geojson = json.load(file)
    return jsonify(geojson)


@app.route('/geojsonZIPCODES')
def get_geojsonZIPCODE():
    with open("Geospatial/static/ZIPCODES.geojson") as file: 
        geojson = json.load(file)
    return jsonify(geojson)

@app.route('/bars')
def get_bars():
    with open("./Geospatial/static/barsexhaustive.geojson") as file: 
        geojson = json.load(file)
    return jsonify(geojson)

@app.route('/')
@app.route('/Geospatial_Visualization.html')
def Geospatial_Visualization():
    app.logger.debug("Navigating to Geospatial_Visualization in Flask")
    return render_template('Geospatial_Visualization.html')

@app.route('/Aboutus.html')
def about_us():
    return render_template('Aboutus.html')

@app.route('/index.html')
def index():
    return render_template('index.html')

@app.route('/Essay.html')
def essay():
    return render_template('Essay.html')

if __name__ == '__main__':
     app.run(debug=True)#,host='0.0.0.0', port=None)




# ColumnNames = ['ID','Call Number','Date/Time','Location','Police District','Nature of Call','Status','Last Updated'] #Names of columsn in database, ID is autoincrement primary key

# connection = pymysql.connect(host='pascal.mscsnet.mu.edu',user='project1',password='ThisIsATest',db='MPD')
# my_cursor = connection.cursor()

# my_cursor.execute("SELECT * FROM MPDCOS;") #Put SQL statement here
# result = my_cursor.fetchall()
# Data = pd.DataFrame(result,columns = ColumnNames) #Converts into a pandas dataframe