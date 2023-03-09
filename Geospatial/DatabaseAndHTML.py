from flask import Flask, render_template, jsonify
import json

import mysql.connector

app = Flask(__name__)

# connect to the database
db = mysql.connector.connect(host='pascal.mscsnet.mu.edu',user='project1',password='ThisIsATest',db='MPD')


@app.route('/data')
def get_data():
    cursor = db.cursor()
    #cursor.execute("SELECT * FROM MPD.GEOCODED WHERE Latitude IS NOT NULL;")
    cursor.execute("SELECT g.*, q.`Call Number`,q.`Date/Time`,q.`Police District`,q.`Nature of Call`,q.`Status`,q.`Last Updated`, q.`Actual District`,q.`Call Density`,q.`Bar Proximity`,q.`Is Administrative Location`  FROM MPD.GEOCODED g  LEFT JOIN (SELECT c.*, v.`Actual District`,v.`Call Density`,v.`Bar Proximity`,v.`Is Administrative Location` FROM MPD.MPDCOS c LEFT JOIN MPD.GEOSPATIAL_VIEW v on v.ID = c.ID) q on g.ID = q.ID WHERE g.Latitude IS NOT NULL;")
    DBdata = cursor.fetchall()
    GEOCODED = [(row[0],row[1],row[2],row[3],row[7],row[8],row[12]) for row in DBdata]
    return jsonify(GEOCODED)

@app.route('/geojson')
def get_geojson():
    with open("./Geospatial/static/modified_mpd.geojson") as file:
        geojson = json.load(file)
    return jsonify(geojson)

@app.route('/bars')
def get_bars():
    with open("./Geospatial/static/barsexhaustive.geojson") as file:
        geojson = json.load(file)
    return jsonify(geojson)


@app.route('/')
def Geospatial_Visualization():
    return render_template('Geospatial Visualization.html')

if __name__ == '__main__':
     app.run(debug=True)



# ColumnNames = ['ID','Call Number','Date/Time','Location','Police District','Nature of Call','Status','Last Updated'] #Names of columsn in database, ID is autoincrement primary key

# connection = pymysql.connect(host='pascal.mscsnet.mu.edu',user='project1',password='ThisIsATest',db='MPD')
# my_cursor = connection.cursor()

# my_cursor.execute("SELECT * FROM MPDCOS;") #Put SQL statement here
# result = my_cursor.fetchall()
# Data = pd.DataFrame(result,columns = ColumnNames) #Converts into a pandas dataframe