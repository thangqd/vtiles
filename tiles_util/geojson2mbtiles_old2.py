import json
import mercantile
import sqlite3
import gzip
from tqdm import tqdm
from shapely.geometry import shape
from shapely.wkt import dumps
from pyproj import Transformer
from mapbox_vector_tile import encode

# Initialize transformer for WGS84 to Web Mercator
transformer = Transformer.from_crs("epsg:4326", "epsg:3857")

def latlon_to_web_mercator(lon, lat):
    return transformer.transform(lon, lat)

def coords_to_tile_coords(lon, lat, zoom):
    x, y = mercantile.xy(*mercantile.lng_lat(lon, lat), zoom)
    return x, y

def tile_to_pixel_coords(x, y, zoom, tile_size=4096):
    scale = tile_size / 256
    pixel_x = x * tile_size
    pixel_y = y * tile_size
    return pixel_x, pixel_y

def bounds_to_pixel_coords(bounds, zoom, tile_size=4096):
    min_lon, min_lat = bounds[0], bounds[1]
    max_lon, max_lat = bounds[2], bounds[3]
    
    min_x, min_y = coords_to_tile_coords(min_lon, min_lat, zoom)
    max_x, max_y = coords_to_tile_coords(max_lon, max_lat, zoom)
    
    min_pixel_x, min_pixel_y = tile_to_pixel_coords(min_x, min_y, zoom, tile_size)
    max_pixel_x, max_pixel_y = tile_to_pixel_coords(max_x, max_y, zoom, tile_size)
    
    return (min_pixel_x, min_pixel_y, max_pixel_x, max_pixel_y)

# Create an MBTiles database
def create_mbtiles(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('CREATE TABLE metadata (name TEXT, value TEXT);')
    c.execute('CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB);')
    c.execute('CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row);')
    conn.commit()
    conn.close()

# Add tile to MBTiles
def add_tile_to_mbtiles(db_path, z, x, y, tile_data):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?);', (z, x, y, tile_data))
    conn.commit()
    conn.close()

# Get the bounding box of a feature
def get_feature_bounds(feature):
    geom = shape(feature['geometry'])
    return geom.bounds

def geojson_to_custom_format(geojson):
    layers = {}

    # Process each feature
    for feature in geojson['features']:
        layer_name = 'my_layer'  # Customize layer name if needed
        if layer_name not in layers:
            layers[layer_name] = []

        # Convert GeoJSON feature geometry to WKT format
        geom = shape(feature['geometry'])  # Convert GeoJSON to Shapely geometry
        geom_wkt = dumps(geom)  # Convert Shapely geometry to WKT

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

# Main function
def main():
    import argparse
    import logging

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Convert GeoJSON to MBTiles")
    parser.add_argument("-i", "--input", required=True, help="Path to the input GeoJSON file")
    parser.add_argument("-o", "--output", required=True, help="Path to the output MBTiles file")
    parser.add_argument("-z", "--zoom", type=int, default=14, help="Zoom level for the tiles (default: 14)")

    args = parser.parse_args()

    try:
        # Read GeoJSON file
        with open(args.input) as f:
            geojson_data = json.load(f)
    except Exception as e:
        logging.error(f"Error reading GeoJSON file: {e}")
        return

    # Create MBTiles file
    try:
        create_mbtiles(args.output)
    except Exception as e:
        logging.error(f"Error creating MBTiles file: {e}")
        return

    # Process each feature
    for feature in tqdm(geojson_data['features'], desc="Processing features"):
        try:
            # Get the bounds of the feature
            bounds = get_feature_bounds(feature)

            # Generate tiles that cover the feature
            tiles = list(mercantile.tiles(bounds[0], bounds[1], bounds[2], bounds[3], args.zoom))

            # for tile in tiles:
            #     x, y, z = tile.x, tile.y, tile.z
            #     tile_features = {
            #         "type": "FeatureCollection",
            #         "features": [feature]
            #     }
            #     tile_data = geojson_to_custom_format(tile_features)
                
            #     tile_data_encoded = encode(tile_data)
            #     tile_data_encoded_zipped = gzip.compress(tile_data_encoded)

            #     # Add the tile to the MBTiles database
            #     # add_tile_to_mbtiles(args.output, z, x, y, tile_data_encoded_zipped)
            #     add_tile_to_mbtiles(args.output, 0,0,0, tile_data_encoded_zipped)

            tile_features = {
                    "type": "FeatureCollection",
                    "features": [feature]
                }
            tile_data = geojson_to_custom_format(tile_features)
            
            tile_data_encoded = encode(tile_data)
            tile_data_encoded_zipped = gzip.compress(tile_data_encoded)

            add_tile_to_mbtiles(args.output, 0,0,0, tile_data_encoded)

        except Exception as e:
            logging.error(f"Error processing feature {feature}: {e}")

if __name__ == "__main__":
    main()
