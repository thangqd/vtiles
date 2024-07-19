import sqlite3
import shutil
import json
import argparse
import os
from tqdm import tqdm
import mapbox_vector_tile
import gzip

def merge_metadata(metadata_list):
    merged_metadata = {}
    
    for metadata in metadata_list:
        if metadata:
            metadata_json = json.loads(metadata)
            
            # Merge vector_layers
            vector_layers = metadata_json.get('vector_layers', [])
            if 'vector_layers' not in merged_metadata:
                merged_metadata['vector_layers'] = vector_layers
            else:
                existing_layers = {layer['id'] for layer in merged_metadata['vector_layers']}
                for layer in vector_layers:
                    if layer['id'] not in existing_layers:
                        merged_metadata['vector_layers'].append(layer)

            # Merge tilestats
            tilestats = metadata_json.get('tilestats', {})
            if 'tilestats' not in merged_metadata:
                merged_metadata['tilestats'] = tilestats
            else:
                existing_stats = merged_metadata['tilestats']
                existing_stats['layerCount'] += tilestats.get('layerCount', 0)
                existing_stats['layers'] += tilestats.get('layers', [])

    return merged_metadata

def merge_mbtiles(input_paths, output_path):
    # Copy the first MBTiles file to the output path
    shutil.copyfile(input_paths[0], output_path)
    
    with sqlite3.connect(output_path) as conn:
        cursor = conn.cursor()
        
        # Read and merge metadata from all input files
        metadata_list = []
        for input_path in input_paths:
            with sqlite3.connect(input_path) as in_conn:
                in_cursor = in_conn.cursor()
                in_cursor.execute("SELECT value FROM metadata WHERE name = 'json'")
                metadata = in_cursor.fetchone()
                if metadata:
                    metadata_list.append(metadata[0])
        
        merged_metadata = merge_metadata(metadata_list)
        
        # Update metadata
        cursor.execute("DELETE FROM metadata WHERE name = 'json'")
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('json', ?)", (json.dumps(merged_metadata),))
        
        # Drop the existing tiles table if it exists
        cursor.execute("DROP TABLE IF EXISTS tiles")
        
        # Recreate the tiles table
        cursor.execute("""
            CREATE TABLE tiles (
                zoom_level INTEGER,
                tile_column INTEGER,
                tile_row INTEGER,
                tile_data BLOB,
                PRIMARY KEY (zoom_level, tile_column, tile_row)
            )
        """)
        
        # Merge tiles from all input files
        for input_path in input_paths:
            with sqlite3.connect(input_path) as in_conn:
                in_cursor = in_conn.cursor()
                in_cursor.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles")
                tiles = in_cursor.fetchall()
                
                for tile in tqdm(tiles, desc=f"Merging tiles from {input_path}", unit="tile"):
                    zoom_level, tile_column, tile_row, tile_data = tile

                    # Handle possible compression
                    if tile_data[:2] == b'\x1f\x8b':
                        tile_data = gzip.decompress(tile_data)
                    
                    # Decode and re-encode the tile data
                    try:
                        decoded_tile = mapbox_vector_tile.decode(tile_data)
                        encoded_tile = mapbox_vector_tile.encode(decoded_tile)
                        encoded_tile_gzip = gzip.compress(encoded_tile)
                        
                        # Insert or replace tile data in the output file
                        cursor.execute("""
                            INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data)
                            VALUES (?, ?, ?, ?)
                        """, (zoom_level, tile_column, tile_row, encoded_tile_gzip))
                    except Exception as e:
                        print(f"Error processing tile {zoom_level}/{tile_column}/{tile_row}: {e}")
        
        conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Merge multiple MBTiles files into one.")
    parser.add_argument("-i", "--inputs", nargs='+', required=True, help="Paths to the input MBTiles files")
    parser.add_argument("-o", "--output", required=True, help="Path to the output MBTiles file")
    args = parser.parse_args()
    
    merge_mbtiles(args.inputs, args.output)

if __name__ == "__main__":
    main()
