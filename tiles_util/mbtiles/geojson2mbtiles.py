import json, math, os
import argparse
from tiles_util.utils.mapbox_vector_tile import encode, decode
import tiles_util.utils.mercantile as mercantile
from tiles_util.utils.geojson2vt.geojson2vt import geojson2vt
import sqlite3
from shapely.geometry import shape, mapping
from shapely.ops import transform
from shapely.wkt import dumps as wkt_dumps
import gzip
from tiles_util.mbtiles import mbtilesfixmeta
import pyproj
import logging
from tiles_util.utils.geopreocessing import fix_wkt
from shapely.geometry import shape, GeometryCollection

logging.basicConfig(level=logging.INFO)

from shapely.geometry import shape
from shapely.wkt import dumps as wkt_dumps

def create_mbtiles(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE metadata (name TEXT, value TEXT);')
    cursor.execute('CREATE UNIQUE INDEX name on metadata (name);')
    cursor.execute('CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB);')
    cursor.execute('CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row);')
    conn.commit()
    conn.close()

def add_tile_to_mbtiles(db_path, z, x, y, tile_data):
    """Add a tile to the MBTiles database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?);', (z, x, y, tile_data))
    conn.commit()
    conn.close()

def transform_to_layer(data, layer_name):
    """
    Transforms the input dictionary into a list format with a specified layer name.

    Args:
        data (dict): The input dictionary containing features and metadata.
        layer_name (str): The name to be assigned to the layer.

    Returns:
        list: A list containing the transformed dictionary with the specified layer name.
    """
    transformed_data = [{
        "name": layer_name,
        "features": data.get('features', [])
        # 'numPoints': data.get('numPoints'),
        # 'numSimplified': data.get('numSimplified'),
        # 'numFeatures': data.get('numFeatures'),
        # 'source': data.get('source', []),
        # 'x': data.get('x'),
        # 'y': data.get('y'),
        # 'z': data.get('z'),
        # 'transformed': data.get('transformed'),
        # 'minX': data.get('minX'),
        # 'minY': data.get('minY'),
        # 'maxX': data.get('maxX'),
        # 'maxY': data.get('maxY')
    }]
    
    for feature_collection in transformed_data:
        for feature in feature_collection['features']:
            # Convert 'geometry' based on type
            if feature['type'] == 1:  # Point
                coords = feature['geometry']
                coords[1] = 4096 - coords[1]  # Apply y-axis inversion
                feature['geometry'] = f"POINT({coords[0]} {coords[1]})"
            elif feature['type'] == 2:  # LineString
                coords = feature['geometry']
                coords = [(x, 4096 - y) for x, y in coords]  # Apply y-axis inversion to each coordinate
                coords_str = ', '.join([f"{x} {y}" for x, y in coords])
                feature['geometry'] = f"LINESTRING({coords_str})"
            elif feature['type'] == 3:  # Polygon
                coords = feature['geometry'][0]
                coords = [(x, 4096 - y) for x, y in coords]  # Apply y-axis inversion to each coordinate
                coords_str = ', '.join([f"{x} {y}" for x, y in coords])
                feature['geometry'] = f"POLYGON(({coords_str}))"
            
            # Rename 'tags' to 'properties'
            feature['properties'] = feature.pop('tags')

            # Remove 'type' as it's no longer needed
            del feature['type']


    return transformed_data


def main():
    parser = argparse.ArgumentParser(description="Convert GeoJSON to MBTiles.")
    parser.add_argument('-i', '--input', required=True, help="Input GeoJSON file.")
    parser.add_argument('-o', '--output', required=True, help="Output MBTiles file.")
    parser.add_argument('-z', '--zoom', type=int, default=0, help="Zoom level for the tile.")
    parser.add_argument('-x', '--x', type=int, default=0, help="Tile column.")
    parser.add_argument('-y', '--y', type=int, default=0, help="Tile row.")
    args = parser.parse_args()

    # Read the input GeoJSON file
    with open(args.input, 'r',encoding='utf-8') as f:
        geojson_data = json.load(f)

    layer_name = os.path.basename(args.input)
    # Define tile coordinates
    z, x, y = args.zoom, args.x, args.y

    # Create MBTiles file
    create_mbtiles(args.output)
    tile_index = geojson2vt(geojson_data, {
	'maxZoom': 5,  # max zoom to preserve detail on; can't be higher than 24
	'tolerance': 3, # simplification tolerance (higher means simpler)
	'extent': 4096, # tile extent (both width and height)
	'buffer': 64,   # tile buffer on each side
	'lineMetrics': False, # whether to enable line metrics tracking for LineString/MultiLineString features
	'promoteId': None,    # name of a feature property to promote to feature.id. Cannot be used with `generateId`
	'generateId': False,  # whether to generate feature ids. Cannot be used with `promoteId`
	'indexMaxZoom': 5,       # max zoom in the initial tile index
	'indexMaxPoints': 100000 # max number of points per tile in the index
    }, logging.INFO)
    tile_data = tile_index.get_tile(0,0,0)
    print(tile_data)
    tile_data_fixed = transform_to_layer(tile_data,layer_name)
    print(tile_data_fixed)
    # tile_data_fixed = fix_wkt(tile_data_fixed)    
    tile_data_fixed_encoded = encode(tile_data_fixed)
    # # tile_data_fixed = fix_wkt(tile_data_fixed)
    # print(tile_data_fixed_encoded)
    # # geojson = vt2geojson(tile_data)

    # # tile_data_fixed = geojson_to_custom_format(tile_data)
    # # print(tile_data_fixed)
    # # tile_data_fixed_encoded = encode(tile_data)
    tile_data_fixed_encoded_compressed = gzip.compress(tile_data_fixed_encoded)

    # # # geojson_reprojected_processed_encoded = encode(tile_index)
    # # # geojson_reprojected_processed_encoded_compressed = gzip.compress(geojson_reprojected_processed_encoded)

    # # # # Add tile to MBTiles
    add_tile_to_mbtiles(args.output, z, x, y, tile_data_fixed_encoded_compressed)
    mbtilesfixmeta.fix_metadata(args.output, 'GZIP') 

if __name__ == "__main__":
    main()
