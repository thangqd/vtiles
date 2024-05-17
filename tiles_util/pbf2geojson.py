import geopandas as gpd
import gzip
from io import BytesIO
import mapbox_vector_tile as mvt
import json
import sqlite3

# connect to tiles
MBTILES = "../data/districtZZZ.mbtiles"
con = sqlite3.connect(MBTILES)
cursor = con.cursor()

# tile coordinates
zoom = 6
col = 45
row = 35

cursor.execute(
    """SELECT tile_data FROM tiles 
    WHERE zoom_level=:zoom 
    AND tile_column=:column AND tile_row=:row;""",
    {"zoom": zoom, "column": col, "row": row},
)
data = cursor.fetchall()
tile_data = data[0][0]
print(tile_data)

raw_data = BytesIO(tile_data)

with gzip.open(raw_data, "rb") as f:
 tile = f.read()
decoded_data = mvt.decode(tile)


# get tile as geodataframe

# unpack layers
layers = [{'name': key, **decoded_data[key]} for key in decoded_data]

# this list will contain features ready to be stored in a geojson dict
features = []

# unpack features for each layer into the list
for layer in layers:
    for feature in layer['features']:
        features.append({'layer': layer['name'],
                         'geometry': feature['geometry'],
                         'id': feature['id'],
                         'properties': {'layer': layer['name'],'id': feature['id'], **feature['properties']},
                         'type': 'Feature'})
with open('mytile.json', 'w') as file:
    data = json.dumps({'type': 'FeatureCollection', 'features': features})
    file.write(data)
feature_df = gpd.read_file('mytile.json', driver='GeoJSON')
print (feature_df)