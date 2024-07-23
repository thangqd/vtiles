import json
import mercantile
from .mapbox_vector_tile import encode
import sqlite3
import argparse
from shapely.wkt import loads as wkt_loads, dumps as wkt_dumps
from shapely.geometry import shape, box


def geojson_to_custom_format(geojson):
    layers = {}
    # Process each feature
    for feature in geojson['features']:
        layer_name = 'my_layer'  # Customize layer name if needed
        if layer_name not in layers:
            layers[layer_name] = []

        # Convert GeoJSON feature geometry to WKT format
        geom = shape(feature['geometry'])  # Convert GeoJSON to Shapely geometry
        geom_wkt = wkt_dumps(geom)  # Convert Shapely geometry to WKT

        # Prepare feature dictionary
        feature_dict = {
            "geometry": geom_wkt,
            "properties": feature["properties"]
        }

        # Add feature to the appropriate layer
        layers[layer_name].append(feature_dict)

    # Convert layers dictionary to the desired format
    formatted_layers = [
        {
            "name": layer_name,
            "features": features
        }
        for layer_name, features in layers.items()
    ]
    # formatted_layers = [{'name': 'my_layer', 'features': [{'geometry': 'POLYGON ((11834838.0505347177386284 1211292.9252088242210448, 11833637.9057463649660349 1212264.4709898722358048, 11835889.6059683244675398 1212893.1182599624153227, 11837546.9487712886184454 1210584.2682861764915287, 11835192.3789960406720638 1210641.4180380033794791, 11835192.3789960406720638 1210641.4180380033794791, 11834838.0505347177386284 1211292.9252088242210448))', 'properties': {'name': '1'}}, {'geometry': 'POLYGON ((11837455.5091683678328991 1209909.9012146256864071, 11838267.0356443021446466 1211327.2150599195156246, 11839615.7697874046862125 1211167.1957548058126122, 11839832.9388443436473608 1210172.7900730269029737, 11838369.9051975868642330 1209452.7032000147737563, 11837455.5091683678328991 1209909.9012146256864071))', 'properties': {'name': '1'}}, {'geometry': 'POLYGON ((11834864.5771230701357126 1209201.3277407283894718, 11836524.3525836132466793 1209498.7441527340561152, 11836015.8664598632603884 1208616.0889945253729820, 11836015.8664598632603884 1208616.0889945253729820, 11834864.5771230701357126 1209201.3277407283894718))', 'properties': {'name': '2'}}]}]
    # formatted_layers =[{"name": "water", "features": [{"geometry": "POLYGON((3257.6188764017343 1924.195788997867, 3257.4962116230354 1924.0964889389206, 3257.7263541125944 1924.032235959602, 3257.8957483307977 1924.2682196290993, 3257.65509171735 1924.2623784491611, 3257.65509171735 1924.2623784491611, 3257.6188764017343 1924.195788997867))", "properties": {"name": "1"}}]}]

    # formatted_layers = [{
    #     "name": "water",
    #     "features": [
    #       {
    #         "geometry":"POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))",
    #         "properties":{
    #           "uid":123,
    #           "foo":"bar",
    #           "cat":"flew"
    #         }
    #       }
    #     ]
    #   }]

    formatted_layers =[{"name": "water", "features": [{"geometry": "LineString(658 2624, 1135 2476)", "properties": {"name": "1"}}]}]
    return formatted_layers

def geojson_to_mvt(geojson, z, x, y):
    """
    Convert GeoJSON to Mapbox Vector Tile format for a specific zoom, x, and y tile coordinate.
    """
    # Encode GeoJSON into MVT format
    geojson_formatted = geojson_to_custom_format(geojson)
    print (geojson_formatted)
    encoded = encode(geojson_formatted)
    return encoded


def insert_tile_to_mbtiles(mbtile_file, z, x, y, mvt_data):
    """
    Insert MVT data into an MBTiles file.
    """
    conn = sqlite3.connect(mbtile_file)
    cursor = conn.cursor()

    # Ensure the tiles table exists
    cursor.execute('''CREATE TABLE IF NOT EXISTS tiles (
                        zoom_level INTEGER,
                        tile_column INTEGER,
                        tile_row INTEGER,
                        tile_data BLOB,
                        PRIMARY KEY (zoom_level, tile_column, tile_row)
                    )''')

    # Convert tile row to the correct order (MBTiles uses inverted Y axis)
    tile_row = (1 << z) - 1 - y

    # Insert tile data
    # aaaa = b'\x1f\x8b\x08\x00\x0ef\x9ef\x02\xff\x93\xef\xe6`\x00\x01&\xe6\xc9Ek\x12\x1e%\xe9z\xea\xea\x19^\xc9\x08\x98\x90t\xcagb\xd2I\xef3\xbe\xa1IA\t!I\xcf\x92LD\x82&$\x88%%&$\xa4\x84\x08=\x8ey`1?\xb0\xfba\xc3\xe5\x1a\xf7\xb6\x9f=<<\xbf\xe7\x8a\x19\x18}`f\xf8\x12\xfam\x963\xd0<\x00\xfd\x7f\x08\xf7X\x00\x00\x00'
    cursor.execute('INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)',
                (z, x, y, sqlite3.Binary(mvt_data)))
    conn.commit()
    conn.close()

def create_metadata_table(mbtile_file):
    """
    Create metadata table in the MBTiles file and insert metadata.
    """
    conn = sqlite3.connect(mbtile_file)
    cursor = conn.cursor()

    # Create metadata table if it doesn't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS metadata (
                        name TEXT PRIMARY KEY,
                        value TEXT
                    )''')

    # Insert metadata
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('name', 'Your Tile Layer'))
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('description', 'Description of your tile layer'))
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('version', '1'))
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('format', 'pbf'))
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('bounds', '-180,-85.0511,180,85.0511'))
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('minzoom', '0'))
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('maxzoom', '0'))

    conn.commit()
    conn.close()


def process_geojson_to_mbtiles(geojson_file, mbtile_file, z, x, y):
    """
    Process GeoJSON file and insert corresponding tiles into MBTiles.
    """
    # Load GeoJSON data
    with open(geojson_file, 'r') as f:
        geojson_data = json.load(f)

    # Convert GeoJSON to MVT
    mvt_data = geojson_to_mvt(geojson_data, z, x, y)

    # Insert MVT data into MBTiles file
    insert_tile_to_mbtiles(mbtile_file, z, x, y, mvt_data)

    # Set metadata for the MBTiles file
    create_metadata_table(mbtile_file)


def main():
    parser = argparse.ArgumentParser(description='Convert GeoJSON to MBTiles.')
    parser.add_argument('-i', '--input', required=True, help='Input GeoJSON file')
    parser.add_argument('-o', '--output', required=True, help='Output MBTiles file')
    parser.add_argument('-z','--zoom', type=int, default=12, help='Zoom level (default: 12)')
    parser.add_argument('-x','--x', type=int, required=True, help='X tile coordinate')
    parser.add_argument('-y','--y', type=int, required=True, help='Y tile coordinate')

    args = parser.parse_args()

    # Process GeoJSON to MBTiles
    process_geojson_to_mbtiles(args.input, args.output, args.zoom, args.x, args.y)

if __name__ == '__main__':
    main()

