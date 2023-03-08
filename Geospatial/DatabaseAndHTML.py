from flask import Flask, render_template, jsonify
import json

import mysql.connector

app = Flask(__name__)

# connect to the database
db = mysql.connector.connect(host='pascal.mscsnet.mu.edu',user='project1',password='ThisIsATest',db='MPD')


@app.route('/data')
def get_data():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM MPD.GEOCODED WHERE Latitude IS NOT NULL LIMIT 3000;")
    #cursor.execute("SELECT c.* FROM MPD.GEOCODED c LEFT JOIN MPD.MPDCOS q ON q.ID = c.ID WHERE q.`Nature of Call` = 'SHOTSPOTTER'  AND c.Latitude IS NOT NULL LIMIT 3000;")
    DBdata = cursor.fetchall()
    GEOCODED = [(row[0],row[1],row[2],row[3]) for row in DBdata]
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