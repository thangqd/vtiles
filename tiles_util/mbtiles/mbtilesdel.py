import sqlite3
from tiles_util.utils.mapbox_vector_tile import encode, decode
from tiles_util.utils.geopreocessing import fix_wkt
import argparse, os
import shutil
import gzip, zlib
import json
from tqdm import tqdm

def update_metadata(conn, layers_to_delete):
    cursor = conn.cursor()
    
    # Read metadata
    cursor.execute("SELECT name, value FROM metadata WHERE name = 'json'")
    metadata = cursor.fetchone()
    
    if metadata:
        metadata_name, metadata_value = metadata
        metadata_json = json.loads(metadata_value)
        
        # Update vector_layers
        vector_layers = metadata_json.get('vector_layers', [])
        updated_layers = [layer for layer in vector_layers if layer['id'] not in layers_to_delete]
        
        # Update tilestats
        tilestats = metadata_json.get('tilestats', {})
        updated_stats = tilestats.copy()
        updated_stats['layerCount'] = len(updated_layers)
        updated_stats['layers'] = [stat for stat in updated_stats.get('layers', []) if stat['layer'] not in layers_to_delete]
        
        metadata_json['vector_layers'] = updated_layers
        metadata_json['tilestats'] = updated_stats
        
        # Update metadata table
        cursor.execute("DELETE FROM metadata WHERE name = 'json'")
        cursor.execute("INSERT INTO metadata (name, value) VALUES ('json', ?)", (json.dumps(metadata_json),))
    else:
        print("No json metadata found to update.")


def delete_layers_from_mbtiles(input_mbtiles, output_mbtiles, layers_to_delete):
    if os.path.exists(output_mbtiles):
        os.remove(output_mbtiles)
    # Copy the input MBTiles file to the output path
    shutil.copyfile(input_mbtiles, output_mbtiles)

    # Connect to the copied MBTiles file
    conn = sqlite3.connect(output_mbtiles)
    cursor = conn.cursor()        
    update_metadata(conn, layers_to_delete)

    # Check if the tiles table is a view
    cursor.execute("SELECT type FROM sqlite_master WHERE name='tiles'")
    result = cursor.fetchone()

    if result and result[0] == 'view':
        # Create a new table named tiles_new
        cursor.execute("CREATE TABLE tiles_new AS SELECT * FROM tiles")

        # Select data from the tiles view
        cursor.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles order by zoom_level")
        tiles = cursor.fetchall()
        
        # Insert decompressed data into the new table
        for zoom_level, tile_column, tile_row, tile_data in tqdm(tiles, desc="Processing tiles", unit="tile"):
             # Decompress the tile data if it is compressed with GZIP or ZLIP
            if tile_data[:2] == b'\x1f\x8b':
                tile_data = gzip.decompress(tile_data)
            elif tile_data[:2] == b'\x78\x9c' or tile_data[:2] == b'\x78\x01' or tile_data[:2] == b'\x78\xda':
                tile_data = zlib.decompress(tile_data)

            decoded_tile = decode(tile_data)
            decoded_tile = fix_wkt(decoded_tile)          
            # Remove the specified layers
            decoded_tile_filtered = [item for item in decoded_tile if item["name"] not in layers_to_delete]

            # Encode and compress the modified tile
            try:
                encoded_tile = encode(decoded_tile_filtered)
                encoded_tile_gzipped = gzip.compress(encoded_tile)
                # Update the tile data in the database
                cursor.execute("""
                    UPDATE tiles_new
                    SET tile_data = ?
                    WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?""",
                    (encoded_tile_gzipped, zoom_level, tile_column, tile_row))
            except Exception as e:
                print(f"Error processing tile {zoom_level}/{tile_column}/{tile_row}: {e}")
        # Drop the view and rename the new table to tiles
        cursor.execute("DROP VIEW tiles")
        cursor.execute("ALTER TABLE tiles_new RENAME TO tiles")
        cursor.execute("CREATE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row)")
    else:
        # Select all from tiles table
        cursor.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles order by zoom_level")
        tiles = cursor.fetchall()            
        # Add tqdm progress bar
        for zoom_level, tile_column, tile_row, tile_data in tqdm(tiles, desc="Processing tiles", unit="tile"):
            # Decompress the tile data if it is compressed with GZIP or ZLIP
            if tile_data[:2] == b'\x1f\x8b':
                tile_data = gzip.decompress(tile_data)
            elif tile_data[:2] == b'\x78\x9c' or tile_data[:2] == b'\x78\x01' or tile_data[:2] == b'\x78\xda':
                tile_data = zlib.decompress(tile_data)

            decoded_tile = decode(tile_data)
            decoded_tile = fix_wkt(decoded_tile)          
            # Remove the specified layers
            decoded_tile_filtered = [item for item in decoded_tile if item["name"] not in layers_to_delete]

            # Encode and compress the modified tile
            try:
                encoded_tile = encode(decoded_tile_filtered)
                encoded_tile_gzipped = gzip.compress(encoded_tile)
                # Update the tile data in the database
                cursor.execute("""
                    UPDATE tiles
                    SET tile_data = ?
                    WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?""",
                    (encoded_tile_gzipped, zoom_level, tile_column, tile_row))
            except Exception as e:
                print(f"Error processing tile {zoom_level}/{tile_column}/{tile_row}: {e}")
        cursor.execute("CREATE INDEX IF NOT EXISTS tile_index ON tiles (zoom_level, tile_column, tile_row)")

    conn.commit()
    conn.close()
    
def main():
    parser = argparse.ArgumentParser(description="Delete layers from an MBTiles file.")
    parser.add_argument("-i", "--input", required=True, help="Path to the input MBTiles file")
    parser.add_argument("-o", "--output", required=True, help="Path to the output MBTiles file")
    parser.add_argument("-l", "--layers", nargs='+', required=True, help="Names of the layers to delete")
    args = parser.parse_args()
    delete_layers_from_mbtiles(args.input, args.output, args.layers)

if __name__ == "__main__":
    main()
