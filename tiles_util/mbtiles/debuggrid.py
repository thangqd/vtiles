import argparse
import os
import math
import mercantile
from tiles_util.utils.mapbox_vector_tile import encode
from shapely.geometry import box, mapping
import sqlite3
import gzip
from pyproj import Transformer
from tqdm import tqdm

# Web Mercator bounds for the entire world
WEB_MERCATOR_BOUNDS = (-20037508.342789244, -20037508.342789244, 20037508.342789244, 20037508.342789244)

# Define the Web Mercator projection (EPSG:3857)
transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)

def mercator_to_4096(x, y, bounds, zoom):
    min_x, min_y, max_x, max_y = bounds
    scale = 2 ** zoom
    x_extent = (x - min_x) / (max_x - min_x) * 4096 * scale
    y_extent = (max_y - y) / (max_y - min_y) * 4096 * scale
    return x_extent, y_extent

def bbox_to_4096(bbox, zoom):
    west, south = transformer.transform(bbox.west, bbox.south)
    east, north = transformer.transform(bbox.east, bbox.north)
    west_4096, south_4096 = mercator_to_4096(west, south, WEB_MERCATOR_BOUNDS, zoom)
    east_4096, north_4096 = mercator_to_4096(east, north, WEB_MERCATOR_BOUNDS, zoom)
    return box(0, 0, 4096, 4096)

def create_tile(z, x, y):
    bbox = mercantile.bounds(x, y, z)
    tile_geometry = bbox_to_4096(bbox, z)
    properties = {
        'z': z,
        'x': x,
        'y': y,
        'id': f'{z}_{x}_{y}',
        'name': f'{z}/{x}/{y}'
    }

    feature = {
        'geometry': mapping(tile_geometry),
        'properties': properties
    }

    tile_data = {
        'name': 'debug_grid',
        'features': [feature]
    }

    tile_data_encoded = encode(tile_data)
    tile_data_encoded_gzipped = gzip.compress(tile_data_encoded)
    return tile_data_encoded_gzipped

def create_mbtiles(tiles, output_mbtiles, max_zoom):
    if os.path.exists(output_mbtiles):
        os.remove(output_mbtiles)

    conn = sqlite3.connect(output_mbtiles)
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE metadata (name TEXT, value TEXT);''')
    cursor.execute('''CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB);''')

    cursor.execute("INSERT INTO metadata (name, value) VALUES ('name', 'Debug Grid');")
    cursor.execute("INSERT INTO metadata (name, value) VALUES ('description', 'A debug grid for XYZ tiles using tiles_util.debuggrid');")
    cursor.execute("INSERT INTO metadata (name, value) VALUES ('type', 'overlay');")
    cursor.execute("INSERT INTO metadata (name, value) VALUES ('version', '1');")
    cursor.execute("INSERT INTO metadata (name, value) VALUES ('format', 'pbf');")
    cursor.execute("INSERT INTO metadata (name, value) VALUES ('minzoom', '0');")
    cursor.execute(f"INSERT INTO metadata (name, value) VALUES ('maxzoom', '{max_zoom}');")
    cursor.execute("INSERT INTO metadata (name, value) VALUES ('bounds', '-180.000000,-85.051129,180.000000,85.051129');")

    for tile in tqdm(tiles, desc="Creating tiles"):
        z, x, y = tile.z, tile.x, tile.y
        tile_data = create_tile(z, x, y)
        tms_y = (2 ** z - 1) - y
        cursor.execute('INSERT INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?);', 
                       (z, x, tms_y, tile_data))

    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='Create a debug grid representing the XYZ vector tile scheme as an MBTiles file.')
    parser.add_argument('-o', '--output', required=True, help='Output MBTiles file')
    parser.add_argument('-z', '--zoom', type=int, required=True, help='Maximum zoom level')
    args = parser.parse_args()

    min_latitude = -85.05112878
    max_latitude = 85.05112878
    min_longitude = -180.0
    max_longitude = 180.0

    all_tiles = []

    for zoom_level in range(0, args.zoom + 1):
        tiles = list(mercantile.tiles(min_longitude, min_latitude, max_longitude, max_latitude, zoom_level))
        all_tiles.extend(tiles)

    create_mbtiles(all_tiles, args.output, args.zoom)

if __name__ == '__main__':
    main()
