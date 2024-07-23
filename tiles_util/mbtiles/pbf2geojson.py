import requests
import json
import argparse
import sqlite3
import os
from tiles_util.utils.vt2geojson.tools import vt_bytes_to_geojson
import gzip, zlib
import logging

def fetch_vector_tile(url_or_path, x, y, z):
    """
    Fetch a vector tile from a URL, MBTiles file, or local file path.

    Parameters:
    url_or_path (str): The URL, path to an MBTiles file, or local file path.
    x (int): The X coordinate of the tile.
    y (int): The Y coordinate of the tile.
    z (int): The zoom level of the tile.

    Returns:
    bytes: The raw (or decompressed) tile data if successful, otherwise None.
    """
    tile_data = None
    
    if url_or_path.startswith('http'):
        try:
            r = requests.get(url_or_path)
            r.raise_for_status()  # Will raise an HTTPError for bad responses
            tile_data = r.content
        except requests.exceptions.RequestException as e:
            logging.error(f"Request to {url_or_path} failed: {e}")
            return None
    elif url_or_path.endswith('.mbtiles'):
        try:
            conn = sqlite3.connect(url_or_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT tile_data 
                FROM tiles 
                WHERE zoom_level=? 
                AND tile_column=? 
                AND tile_row=?''', 
                (z, x, (1 << z) - 1 - y))
            row = cursor.fetchone()
            conn.close()
            if row:
                tile_data = row[0]
            else:
                logging.error(f"Tile not found in MBTiles file at zoom_level={z}, tile_column={x}, tile_row={(1 << z) - 1 - y}")
                return None
        except sqlite3.Error as e:
            logging.error(f"Failed to read MBTiles file {url_or_path}: {e}")
            return None
    else:
        try:
            with open(url_or_path, 'rb') as f:
                tile_data = f.read()
        except IOError as e:
            logging.error(f"Failed to read file {url_or_path}: {e}")
            return None
    
    # Decompress tile_data
    if tile_data:
        try:
            if tile_data[:2] == b'\x1f\x8b':  # Check for gzip magic number
                tile_data = gzip.decompress(tile_data)
            elif tile_data[:2] == b'\x78\x9c' or tile_data[:2] == b'\x78\x01' or tile_data[:2] == b'\x78\xda':
                tile_data = zlib.decompress(tile_data) 
        except Exception as e:
            logging.error(f"Failed to decompress gzip data: {e}")
            return None
    
    return tile_data


def convert_pbf_to_geojson(vt_content, x, y, z, output_file):
    try:
        features = vt_bytes_to_geojson(vt_content, x, y, z)
        with open(output_file, 'w') as f:
            json.dump(features, f, indent=2)
        print(f"GeoJSON data has been saved to {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    parser = argparse.ArgumentParser(description='Convert PBF file or URL to GeoJSON.')
    parser.add_argument('-i', '--input', type=str, help='Input PBF file, MBTiles file, or URL')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output GeoJSON file')
    parser.add_argument('-z', type=int, required=True, help='Tile zoom level')
    parser.add_argument('-x', type=int, required=True, help='Tile x coordinate')
    parser.add_argument('-y', type=int, required=True, help='Tile y coordinate')
    
    args = parser.parse_args()
    
    vt_content = fetch_vector_tile(args.input, args.x, args.y, args.z)
    if vt_content:
        convert_pbf_to_geojson(vt_content, args.x, args.y, args.z, args.output)

if __name__ == '__main__':
    main()
