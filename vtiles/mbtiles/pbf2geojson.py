import requests
import json
import argparse
import sqlite3
import os
from vtiles.utils.vt2geojson.tools import vt_bytes_to_geojson, _is_url
import gzip, zlib
import logging
from re import search
from urllib.request import urlopen

def tile_data_to_geojson(tile_data, x, y, z, output):
    try:
        features = vt_bytes_to_geojson(tile_data, x,y,z)
        with open(output, 'w') as f:
            json.dump(features, f, indent=2)
        print(f"GeoJSON data has been saved to {output}")
    except Exception as e:
        print(f"Error saving pbf to geojson: {e}")


def main():
    parser = argparse.ArgumentParser(description='Convert tile data from BBF file, MBTiles file, or URL to GeoJSON.')
    parser.add_argument('-i', '--input', type=str, required=True, help='Input PBF file, MBTiles file, or URL')
    parser.add_argument('-z', type=int, help='Tile zoom level')
    parser.add_argument('-x', type=int, help='Tile column')
    parser.add_argument('-y', type=int, help='Tile row')
    # parser.add_argument("-l", "--layer", help="include only the specified layer", type=str)
    parser.add_argument('-o', '--output', type=str, required=True, help='Output GeoJSON file')
    parser.add_argument('-flipy', '--flipy', type=int, choices=[0, 1], default=0, help='TMS <--> XYZ tiling scheme (optional): 1 or 0, default is 0')

    args = parser.parse_args()    
    tile_data,z,x,y = None,None,None,None
    url_or_path = args.input
    flipy = args.flipy
    XYZ_REGEX = r"\/(\d+)\/(\d+)\/(\d+)"

    if _is_url(url_or_path):
        matches = search(XYZ_REGEX, args.input)
        if matches is None:
            raise ValueError("Unknown url, no `/z/x/y` pattern.")
        z, x, y = map(int, matches.groups()) # set z, x, y based on /z/x/y values in the URL
        r = urlopen(url_or_path)
        tile_data = r.read()
    else:
        if args.z is None or args.x is None or args.y is None:
            raise ValueError("-z, -x, -y must be specified for MBTiles or PBF file!")
        z = args.z
        x = args.x
        y = args.y        
        if url_or_path.endswith('.mbtiles'):
            try:
                conn = sqlite3.connect(url_or_path)
                cursor = conn.cursor()                   
                cursor.execute('''
                    SELECT tile_data 
                    FROM tiles 
                    WHERE zoom_level=? 
                    AND tile_column=? 
                    AND tile_row=?''',                    
                    (z, x, y))
                row = cursor.fetchone()
                conn.close()
                if row:
                    tile_data = row[0]
                else:
                    logging.error(f"Tile not found in MBTiles file at zoom_level={z}, tile_column={x}, tile_row={y}")
                    return None
            except sqlite3.Error as e:
                logging.error(f"Failed to read MBTiles file {url_or_path}: {e}")
                return None
        
        elif  url_or_path.endswith('.pbf'):
            try:
                with open(url_or_path, 'rb') as f:
                    tile_data = f.read()
            except IOError as e:
                logging.error(f"Failed to read file {url_or_path}: {e}")

    # Decompress tile_data
    if tile_data:
        try:
            if tile_data[:2] == b'\x1f\x8b':  # Check for gzip magic number
                tile_data = gzip.decompress(tile_data)
            elif tile_data[:2] == b'\x78\x9c' or tile_data[:2] == b'\x78\x01' or tile_data[:2] == b'\x78\xda':
                tile_data = zlib.decompress(tile_data) 
        except Exception as e:
            logging.error(f"Failed to decompress gzip data: {e}")
        if flipy: 
            y = (1 << z) - 1 - y          
        tile_data_to_geojson(tile_data, x,y,z,args.output)

if __name__ == '__main__':
    main()
