import json
import pyproj

with open('./static/mpd.geojson', 'r') as f:
    geojson_data = json.load(f)

utm_zone = pyproj.Proj("+proj=lcc +lat_0=42 +lon_0=-90 +lat_1=42.7333333333333 +lat_2=44.0666666666667 +x_0=609601.219202438 +y_0=0 +ellps=clrk66 +units=us-ft +no_defs +type=crs")
wgs84 = pyproj.Proj("+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs")


# Convert the UTM coordinates to lat/long for each feature
for feature in geojson_data['features']:
    geometry = feature['geometry']
    if geometry['type'] == 'Point':
        geometry['coordinates'] = pyproj.transform(utm_zone, wgs84, geometry['coordinates'])
    elif geometry['type'] == 'LineString' or geometry['type'] == 'Polygon':
        #[[print(coord) for coord in part] for part in geometry['coordinates']]
        geometry['coordinates'] = [[pyproj.transform(utm_zone, wgs84, coord[0],coord[1]) for coord in part] for part in geometry['coordinates']]
    elif geometry['type'] == 'MultiPolygon':
        geometry['coordinates'] = [[[pyproj.transform(utm_zone, wgs84, coord[0],coord[1]) for coord in part] for part in poly] for poly in geometry['coordinates']]

# Write the modified GeoJSON file back to disk
with open('modified_mpd.geojson', 'w') as f:
    json.dump(geojson_data, f)
