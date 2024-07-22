import json
import argparse
from mapbox_vector_tile import encode
import mercantile
import sqlite3
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Proj, transform as pyproj_transform
from shapely.wkt import loads as wkt_loads, dumps as wkt_dumps
import gzip

def create_mbtiles(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('CREATE TABLE metadata (name TEXT, value TEXT);')
    c.execute('CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB);')
    c.execute('CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row);')
    conn.commit()
    conn.close()

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
    formatted_layers = [{
        "name": "water",
        "features": [
          {
            "geometry":"POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))",
            "properties":{
              "uid":123,
              "foo":"bar",
              "cat":"flew"
            }
          }
        ]
      }]
    return formatted_layers

def reproject_geojson_to_tile_extent(geojson_data, tile_x, tile_y, zoom, tile_size=4096):
    # Get the bounds of the specified tile
    tile_bounds = mercantile.bounds(tile_x, tile_y, zoom)

    # Calculate scale factors
    minx, miny, maxx, maxy = tile_bounds
    scale_x = tile_size / (maxx - minx)
    scale_y = tile_size / (maxy - miny)

    def scale_coords(x, y, z=None):
        return (x - minx) * scale_x, (y - miny) * scale_y

    # Convert and scale features
    reprojected_features = []
    for feature in geojson_data["features"]:
        geometry = shape(feature["geometry"])
        scaled_geometry = transform(scale_coords, geometry)
        reprojected_features.append({
            "type": "Feature",
            "properties": feature["properties"],
            "geometry": mapping(scaled_geometry)
        })

    # Create the new GeoJSON structure
    reprojected_geojson = {
        "type": "FeatureCollection",
        "name": geojson_data.get("name", "reprojected_geojson"),
        "crs": geojson_data.get("crs"),
        "features": reprojected_features
    }

    return reprojected_geojson

def add_tile_to_mbtiles(db_path, z, x, y, tile_data):
    """Add a tile to the MBTiles database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?);', (z, x, y, tile_data))
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Convert GeoJSON to MBTiles.")
    parser.add_argument('-i', '--input', required=True, help="Input GeoJSON file.")
    parser.add_argument('-o', '--output', required=True, help="Output MBTiles file.")
    parser.add_argument('-z', '--zoom', type=int, default=0, help="Zoom level for the tile.")
    parser.add_argument('-x', '--x', type=int, default=0, help="Tile column.")
    parser.add_argument('-y', '--y', type=int, default=0, help="Tile row.")
    args = parser.parse_args()

    # Read the input GeoJSON file
    with open(args.input, 'r') as f:
        geojson_data = json.load(f)

    # Define tile coordinates
    z, x, y = args.zoom, args.x, args.y

    # Create MBTiles file
    create_mbtiles(args.output)
    
    geojson_reprojected = reproject_geojson_to_tile_extent(geojson_data,z, x, y)
    print (geojson_reprojected)
    geojson_reprojected_processed = geojson_to_custom_format(geojson_reprojected)
    print (geojson_reprojected_processed)
    # Add tile to MBTiles
    add_tile_to_mbtiles(args.output, z, x, y, encode(geojson_reprojected_processed))

if __name__ == "__main__":
    main()
