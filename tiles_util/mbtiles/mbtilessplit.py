import sqlite3
import shutil
import gzip, zlib
import json
import argparse
import os
from tqdm import tqdm
from tiles_util.utils.mapbox_vector_tile import encode, decode
from tiles_util.utils.geopreocessing import fix_wkt

def filter_metadata(metadata_json, layers_to_split):
    # Filter vector_layers
    vector_layers = metadata_json.get('vector_layers', [])
    filtered_layers = [layer for layer in vector_layers if layer['id'] in layers_to_split]
    
    # Update tilestats to reflect the filtered layers
    tilestats = metadata_json.get('tilestats', {})
    updated_stats = tilestats.copy()
    updated_stats['layerCount'] = len(filtered_layers)
    updated_stats['layers'] = [stat for stat in updated_stats.get('layers', []) if stat['layer'] in layers_to_split]
    
    metadata_json['vector_layers'] = filtered_layers
    metadata_json['tilestats'] = updated_stats
    
    return metadata_json

def split_mbtiles_by_layers(input_mbtiles, output_mbtiles, layers_to_split):
    if os.path.exists(output_mbtiles):
        os.remove(output_mbtiles)
    # Copy the input MBTiles file to the output path
    shutil.copyfile(input_mbtiles, output_mbtiles)
     # Check if the tiles table is a view
    with sqlite3.connect(output_mbtiles) as conn:
        cursor = conn.cursor()
            
        #     # Read and filter metadata
        cursor.execute("SELECT name, value FROM metadata WHERE name = 'json'")
        metadata = cursor.fetchone()
        
        if metadata:
            _, metadata_value = metadata
            metadata_json = json.loads(metadata_value)
            filtered_metadata = filter_metadata(metadata_json, layers_to_split)
            
            # Update metadata
            cursor.execute("DELETE FROM metadata WHERE name = 'json'")
            cursor.execute("INSERT INTO metadata (name, value) VALUES ('json', ?)", (json.dumps(filtered_metadata),))
        
        cursor.execute("SELECT type FROM sqlite_master WHERE name='tiles'")
        result = cursor.fetchone()
        if result:
            if result[0] == 'view':
                cursor.execute("DROP VIEW IF EXISTS tiles")
            else:
                cursor.execute("DROP TABLE IF EXISTS tiles")   
        
        # out_conn.commit
        # Recreate the tiles table
        cursor.execute("""
            CREATE TABLE tiles (
                zoom_level INTEGER,
                tile_column INTEGER,
                tile_row INTEGER,
                tile_data BLOB
            )
        """)
        cursor.execute("CREATE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row)")
        with sqlite3.connect(input_mbtiles) as in_conn:
            in_cursor = in_conn.cursor()
            in_cursor.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles order by zoom_level")
            tiles = in_cursor.fetchall()
            
            # Create tqdm progress bar
            for zoom_level, tile_column, tile_row, tile_data in tqdm(tiles, desc="Processing tiles", unit="tile"):       
                # Handle possible compression
                if tile_data[:2] == b'\x1f\x8b':
                    tile_data = gzip.decompress(tile_data)
                elif tile_data[:2] == b'\x78\x9c' or tile_data[:2] == b'\x78\x01' or tile_data[:2] == b'\x78\xda':
                    tile_data = zlib.decompress(tile_data)
            
                # Decode the tile data
                decoded_tile = decode(tile_data)
                decoded_tile = fix_wkt(decoded_tile)
                
                decoded_tile_filtered = [item for item in decoded_tile if item["name"] in layers_to_split]
                # print(decoded_tile_filtered)
                try:
                    encoded_tile = encode(decoded_tile_filtered)
                    encoded_tile_gzip = gzip.compress(encoded_tile)
                    cursor.execute("""
                        INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data)
                        VALUES (?, ?, ?, ?)""", (zoom_level, tile_column, tile_row, encoded_tile_gzip))
                except Exception as e:
                    print(f"Error processing tile {zoom_level}/{tile_column}/{tile_row}: {e}")
            
        conn.commit   

def main():
    parser = argparse.ArgumentParser(description="Split an MBTiles file by selected layers.")
    parser.add_argument("-i", "--input", required=True, help="Path to the input MBTiles file")
    parser.add_argument("-o", "--output", required=True, help="Path to the output MBTiles file")
    parser.add_argument("-l", "--layers", nargs='+', required=True, help="Names of the layers to keep")
    args = parser.parse_args()
    
    split_mbtiles_by_layers(args.input, args.output, args.layers)

if __name__ == "__main__":
    main()
