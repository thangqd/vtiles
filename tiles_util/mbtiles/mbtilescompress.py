import argparse, os
import sqlite3
import gzip, zlib
import logging
import shutil
from tqdm import tqdm

def compress_tile_data(tile_data):
    try: 
        if tile_data[:2] != b'\x1f\x8b':  # check if GZIP    
            if tile_data[:2] == b'\x78\x9c' or tile_data[:2] == b'\x78\x01' or tile_data[:2] == b'\x78\xda': # Check if ZLIB
                tile_data = zlib.decompress(tile_data)           
            tile_data = gzip.compress(tile_data)
    except Exception as e:
        logging.error(f"Failed to compress tile data: {e}")
        return tile_data
    return tile_data          

def compress_mbtiles(input_mbtiles, output_mbtiles):
    
    if os.path.exists(output_mbtiles):
            os.remove(output_mbtiles)

    # Copy the original MBTiles file to the output path
    shutil.copyfile(input_mbtiles, output_mbtiles)

    # Open the copied MBTiles file
    conn = sqlite3.connect(output_mbtiles)
    cursor = conn.cursor()

    # Check if the tiles table is a view
    cursor.execute("SELECT type FROM sqlite_master WHERE name='tiles'")
    result = cursor.fetchone()

    if result and result[0] == 'view':
        # Create a new table named tiles_new
        cursor.execute("CREATE TABLE tiles_new (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB)")
        
        # Select data from the view
        cursor.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles order by zoom_level")
        tiles = cursor.fetchall()
        
        # Insert decompressed data into the new table
        for zoom_level, tile_column, tile_row, tile_data in tqdm(tiles, desc="Compressing tiles", unit="tile"):
            try:
                compressed_tile = compress_tile_data(tile_data)
                cursor.execute(
                    "INSERT INTO tiles_new (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)",
                    (zoom_level, tile_column, tile_row,compressed_tile)
                )
            except Exception as e:
                print(f"Error compressing tile {zoom_level}/{tile_column}/{tile_row}: {e}")
    
        # Drop the view and rename the new table to tiles
        cursor.execute("DROP VIEW tiles")
        cursor.execute("ALTER TABLE tiles_new RENAME TO tiles")
        cursor.execute("CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row)")
    else:
        # Decompress tile data in the existing tiles table
        cursor.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles order by zoom_level")
        tiles = cursor.fetchall()
        
        # Add tqdm progress bar
        for zoom_level, tile_column, tile_row, tile_data in tqdm(tiles, desc="Compressing tiles", unit="tile"):
            compressed_tile = compress_tile_data(tile_data)
            try:
                cursor.execute(
                    "UPDATE tiles SET tile_data = ? WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?",
                    (compressed_tile, zoom_level, tile_column, tile_row)
                )
            except Exception as e:
                print(f"Error compressing tile {zoom_level}/{tile_column}/{tile_row}: {e}")
    
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS tile_index ON tiles (zoom_level, tile_column, tile_row)")
    # Commit and close connections
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='Decompress an MBTiles file.')
    parser.add_argument('-i', '--input', required=True, help='Path to the input MBTiles file.')
    parser.add_argument('-o', '--output', required=True, help='Path to the output MBTiles file.')

    args = parser.parse_args()
    compress_mbtiles(args.input, args.output)

if __name__ == "__main__":
    main()
