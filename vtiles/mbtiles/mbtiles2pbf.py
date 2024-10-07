#!/usr/bin/env python
import os,sys, logging
import sqlite3
import argparse
from vtiles.utils.geopreocessing import check_vector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_tile_to_pbf(mbtiles_file, z, x, y, output_pbf):
    try:
        # Connect to the MBTiles database
        conn = sqlite3.connect(mbtiles_file)
        cursor = conn.cursor()        
       
        # Query the tile data
        cursor.execute('SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?', (z, x, y))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            tile_data = row[0] 
            # Write the decompressed tile data to the output PBF file
            with open(output_pbf, 'wb') as f:
                f.write(tile_data)
            print(f"Tile {z}/{x}/{y} successfully extracted to {output_pbf}")
        else:
            print("Tile not found in MBTiles file")
    except sqlite3.Error as e:
        print(f"Failed to read MBTiles file: {e}")

def main():
    parser = argparse.ArgumentParser(description='Extract a tile from MBTiles to PBF.')
    parser.add_argument('input', help='Input MBTiles file')
    parser.add_argument('-z', '--zoom', type=int, required=True, help='Zoom level')
    parser.add_argument('-x', '--x', type=int, required=True, help='tile column')
    parser.add_argument('-y', '--y', type=int, required=True, help='tile row')
    parser.add_argument('-o', '--output', help='Output PBF file')
    
    args = parser.parse_args()
    if not os.path.exists(args.input):
        logging.error('MBTiles file does not exist! Please recheck and input a correct file path.')
        sys.exit(1)
    input_file_abspath = os.path.abspath(args.input)
   
    if args.output:
      output_file_abspath = os.path.abspath(args.output)
      if os.path.exists(output_file_abspath):
        logger.error(f'Output pbf file {output_file_abspath} already exists!. Please recheck and input a correct one. Ex: -o tiles.pbf')
        sys.exit(1)
      elif not output_file_abspath.endswith('mbtiles'):
        logger.error(f'Output pbf file {output_file_abspath} must end with .mbtiles. Please recheck and input a correct one. Ex: -o tiles.pbf')
        sys.exit(1)

    else:
        output_file_name = os.path.basename(input_file_abspath).replace('.mbtiles', str(args.zoom) + str(args.x) + str(args.y)+ '.pbf')

        output_file_abspath = os.path.join(os.path.dirname(args.input), output_file_name)    
        if os.path.exists(output_file_abspath): 
            logger.error(f'Output pbf file {output_file_abspath} already exists! Please recheck and input a correct one. Ex: -o tiles.pbf')
            sys.exit(1)      
    
    is_vector, _ = check_vector(args.input)
    if is_vector:
        logging.info(f'Converting {input_file_abspath} to {output_file_abspath}') 
        extract_tile_to_pbf(input_file_abspath, args.zoom, args.x, args.y, output_file_abspath)
    else:
        logging.warning(f'mbtiles2pbf only supports vector MBTiles. {input_file_abspath} is not a vector MBTiles.')
        sys.exit(1)
   
if __name__ == '__main__':
    main()
