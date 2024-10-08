import json
import argparse
import sqlite3
import os, sys
from vtiles.utils.vt2geojson.tools import vt_bytes_to_geojson, _is_url
import gzip, zlib
import logging
from re import search
from urllib.request import urlopen

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def tile_data_to_geojson(tile_data, x, y, z, output):
    try:
        features = vt_bytes_to_geojson(tile_data, x, y, z)
        with open(output, 'w') as f:
            json.dump(features, f, indent=2)
        logger.info(f"GeoJSON data has been saved to {output}")
    except Exception as e:
        logger.error(f"Error saving pbf to geojson: {e}")


def process_tile_data(input_path, z, x, y, output, flipy):
    """Handles the main tile data processing logic."""
    tile_data = None    
    if input_path.endswith('.mbtiles'):
        tile_data = read_from_mbtiles(input_path, z, x, y)
    elif input_path.endswith('.pbf'):
        tile_data = read_from_pbf(input_path)
    else:
        logger.error(f"Unsupported file type: {input_path}")
        return

    # Decompress tile data if needed
    if tile_data:
        try:
            if tile_data[:2] == b'\x1f\x8b':  # Check for gzip magic number
                tile_data = gzip.decompress(tile_data)
            elif tile_data[:2] in [b'\x78\x9c', b'\x78\x01', b'\x78\xda']:  # zlib headers
                tile_data = zlib.decompress(tile_data)
        except Exception as e:
            logger.error(f"Failed to decompress tile data: {e}")
            return
    
        # Flip Y-axis if needed (TMS/XYZ tiling scheme)
        if flipy:
            y = (1 << z) - 1 - y
        
        # Convert tile data to GeoJSON and save it
        tile_data_to_geojson(tile_data, x, y, z, output)


def read_from_mbtiles(mbtiles_path, z, x, y):
    """Read tile data from an MBTiles file."""
    try:
        conn = sqlite3.connect(mbtiles_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT tile_data 
            FROM tiles 
            WHERE zoom_level=? 
            AND tile_column=? 
            AND tile_row=?''', (z, x, y))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
        else:
            logger.error(f"Tile not found in MBTiles file at zoom_level={z}, tile_column={x}, tile_row={y}")
            return None
    except sqlite3.Error as e:
        logger.error(f"Failed to read MBTiles file {mbtiles_path}: {e}")
        return None


def read_from_pbf(pbf_path):
    """Read raw PBF tile data."""
    try:
        with open(pbf_path, 'rb') as f:
            return f.read()
    except IOError as e:
        logger.error(f"Failed to read file {pbf_path}: {e}")
        return None


def main():
    """Main function that parses command-line arguments."""
    parser = argparse.ArgumentParser(description='Convert tile data from PBF file, MBTiles file, or URL to GeoJSON.')
    parser.add_argument('input', help='Input PBF file, MBTiles file, or URL')
    parser.add_argument('-z', type=int, default=0, help='Tile zoom level')
    parser.add_argument('-x', type=int, default=0, help='Tile column')
    parser.add_argument('-y', type=int, default=0, help='Tile row')
    parser.add_argument('-o', '--output', type=str, help='Output GeoJSON file')
    parser.add_argument('-flipy', '--flipy', type=int, choices=[0, 1], default=0, help='TMS <--> XYZ tiling scheme (optional): 1 or 0, default is 0')
    
    args = parser.parse_args()
    if not os.path.exists(args.input):
        logging.error('Input file does not exist! Please recheck and input a correct file path.')
        sys.exit(1)
        
    input_file_abspath = os.path.abspath(args.input)
    # Determine the output filename
    if args.output:
        output_file_abspath = os.path.abspath(args.output)
        if os.path.exists(output_file_abspath):
            logger.error(f'Output GeoJSON file {output_file_abspath} already exists!. Please recheck and input a correct one. Ex: -o pbf2.geojson')
            sys.exit(1)
        elif not output_file_abspath.endswith('geojson'):
            logger.error(f'Output GeoJSON file {output_file_abspath} must end with .geojson. Please recheck and input a correct one. Ex: -o pbf2.geojson')
            sys.exit(1)
    else:
        if input_file_abspath.endswith('mbtiles'): 
            output_file_name = os.path.basename(input_file_abspath).replace('.mbtiles', f'{args.z}{args.x}{args.y}.geojson')
        elif input_file_abspath.endswith('pbf'): 
            output_file_name = os.path.basename(input_file_abspath).replace('pbf', 'geojson')
        
        output_file_abspath = os.path.join(os.path.dirname(input_file_abspath), output_file_name)
        
        if os.path.exists(output_file_abspath): 
            logger.error(f'Output GeoJSON file {output_file_abspath} already exists! Please recheck and input a correct one. Ex: -o pbf2.geojson')
            sys.exit(1)
# Call the processing function
    process_tile_data(input_file_abspath, args.z, args.x, args.y, output_file_abspath, args.flipy)


if __name__ == '__main__':
    main()
