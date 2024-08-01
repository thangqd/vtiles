import requests
import json
import argparse
import sqlite3
import os
from tiles_util.utils.vt2geojson.tools import vt_bytes_to_geojson
import gzip
import zlib
import logging
from re import search
from urllib.request import urlopen
from tqdm import tqdm

def tile_data_to_geojson(tile_data, x, y, z):
    try:
        features = vt_bytes_to_geojson(tile_data, x, y, z)
        return features
    except Exception as e:
        logging.error(f"Error converting tile data to geojson: {e}")
        return None

def decompress_tile_data(tile_data):
    try:
        if tile_data[:2] == b'\x1f\x8b':  # Check for gzip magic number
            return gzip.decompress(tile_data)
        elif tile_data[:2] == b'\x78\x9c' or tile_data[:2] == b'\x78\x01' or tile_data[:2] == b'\x78\xda':
            return zlib.decompress(tile_data)
        return tile_data
    except Exception as e:
        logging.error(f"Failed to decompress data: {e}")
        return tile_data

def mbtiles_to_geojson(input_mbtiles, output_geojson, zoom_level,flipy):
    all_features = []
    # try:
    conn = sqlite3.connect(input_mbtiles)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT tile_column, tile_row, tile_data 
        FROM tiles 
        WHERE zoom_level=?''', (zoom_level,))
    rows = cursor.fetchall()
    conn.close()

    for x, y, tile_data in tqdm(rows, desc="Converting tiles to GeoJSON"):
        if flipy: 
            y = (1 << zoom_level) - 1 - y
        tile_data = decompress_tile_data(tile_data)
        if tile_data:
            features = tile_data_to_geojson(tile_data, x, y, zoom_level)
            print(features)
            # if features:
            #     all_features.extend(features['features'])

    # geojson_data = {
    #     "type": "FeatureCollection",
    #     "features": features
    # }
    # print(geojson_data)
    with open(output_geojson, 'w') as f:
        json.dump(features, f, indent=2)
    print(f"GeoJSON data has been saved to {output_geojson}")
    # except sqlite3.Error as e:
    #     logging.error(f"Failed to read MBTiles file {input_mbtiles}: {e}")
    # except Exception as e:
    #     logging.error(f"Failed to convert {input_mbtiles} at zoom level {zoom_level} to GeoJSON: {e}")

def main():
    parser = argparse.ArgumentParser(description='Convert Tile data from PBF file, MBTiles file, or URL to GeoJSON.')
    parser.add_argument('-i', '--input', type=str, required=True, help='Input PBF file, MBTiles file, or URL')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output GeoJSON file')
    parser.add_argument('-z', '--zoom', type=int, required=True, help='Tile zoom level')
    parser.add_argument('-flipy', '--flipy', help='Use TMS (flip y) format: 1 or 0', type=int, default=0)
    args = parser.parse_args()
    
    mbtiles_to_geojson(args.input,args.output, args.zoom, args.flipy)

if __name__ == '__main__':
    main()
