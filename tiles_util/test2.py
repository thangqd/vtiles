import json
import sqlite3
import os
import argparse
import mercantile
from shapely.geometry import shape, box
from shapely.geometry.geo import mapping
from mapbox_vector_tile import encode
from shapely.wkt import loads as wkt_loads, dumps as wkt_dumps
import gzip

def clip_geojson(geojson_data, bbox):
    clipped_features = []
    bbox_shape = box(*bbox)
    
    for feature in geojson_data['features']:
        geom = shape(feature['geometry'])
        if geom.intersects(bbox_shape):
            clipped_geom = geom.intersection(bbox_shape)
            if not clipped_geom.is_empty:
                feature['geometry'] = mapping(clipped_geom)
                clipped_features.append(feature)
    
    return {
        'type': 'FeatureCollection',
        'features': clipped_features
    }

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
    # # formatted_layers = [{'name': 'my_layer', 'features': [{'geometry': 'POLYGON ((11834838.0505347177386284 1211292.9252088242210448, 11833637.9057463649660349 1212264.4709898722358048, 11835889.6059683244675398 1212893.1182599624153227, 11837546.9487712886184454 1210584.2682861764915287, 11835192.3789960406720638 1210641.4180380033794791, 11835192.3789960406720638 1210641.4180380033794791, 11834838.0505347177386284 1211292.9252088242210448))', 'properties': {'name': '1'}}, {'geometry': 'POLYGON ((11837455.5091683678328991 1209909.9012146256864071, 11838267.0356443021446466 1211327.2150599195156246, 11839615.7697874046862125 1211167.1957548058126122, 11839832.9388443436473608 1210172.7900730269029737, 11838369.9051975868642330 1209452.7032000147737563, 11837455.5091683678328991 1209909.9012146256864071))', 'properties': {'name': '1'}}, {'geometry': 'POLYGON ((11834864.5771230701357126 1209201.3277407283894718, 11836524.3525836132466793 1209498.7441527340561152, 11836015.8664598632603884 1208616.0889945253729820, 11836015.8664598632603884 1208616.0889945253729820, 11834864.5771230701357126 1209201.3277407283894718))', 'properties': {'name': '2'}}]}]
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
    return formatted_layers

def geojson_to_tiles(geojson_file, mbtiles_file, zoom_levels=[0,1]):
    # Create MBTiles database
    if os.path.exists(mbtiles_file):
        os.remove(mbtiles_file)
    conn = sqlite3.connect(mbtiles_file)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE tiles (
                 zoom_level INTEGER,
                 tile_column INTEGER,
                 tile_row INTEGER,
                 tile_data BLOB,
                 PRIMARY KEY (zoom_level, tile_column, tile_row))''')
    c.execute('''CREATE TABLE metadata (
                 name TEXT,
                 value TEXT)''')
    metadata = {
        'name': 'GeoJSON to MBTiles',
        'type': 'baselayer',
        'version': '1.0',
        'description': 'Tiles created from GeoJSON'
    }
    for name, value in metadata.items():
        c.execute('INSERT INTO metadata (name, value) VALUES (?, ?)', (name, value))

    # Load GeoJSON
    with open(geojson_file, 'r') as f:
        geojson_data = json.load(f)

    def add_tile(z, x, y, data):
        c.execute("""insert into tiles (zoom_level,
                  tile_column, tile_row, tile_data) values
                  (?, ?, ?, ?);""",
                  # (z, x, y, file_content))
                  (z, x, y, sqlite3.Binary(data)))

    # Iterate over zoom levels and tiles
    for z in zoom_levels:
        for x in range(2**z):
            for y in range(2**z):
                bbox = mercantile.xy_bounds(x, y, z)
                clipped_geojson = clip_geojson(geojson_data, bbox)
                clipped_wkt = geojson_to_custom_format(clipped_geojson)
                # tile_date = {'layer_name': clipped_geojson}
                print(x, y, z, clipped_wkt)
                # Encode vector tile
                tile_data_encoded = encode(clipped_wkt)
                tile_data_encoded_gzipped = gzip.compress(tile_data_encoded)

                add_tile(z, x, y, tile_data_encoded_gzipped)

    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='Convert GeoJSON to MBTiles.')
    parser.add_argument('-i', '--input', required=True, help='Input GeoJSON file')
    parser.add_argument('-o', '--output', required=True, help='Output MBTiles file')
    args = parser.parse_args()

    geojson_to_tiles(args.input, args.output)

if __name__ == '__main__':
    main()
