import sqlite3
import shutil
import gzip, zlib
import json
import argparse
import os
from tqdm import tqdm
from vtiles.utils.mapbox_vector_tile import encode, decode
from vtiles.utils.geopreocessing import fix_wkt
import logging
from vtiles.mbtiles import mbtilesfixmeta

logging.basicConfig(level=logging.INFO)

def process_metadata(metadata_json, layers_to_keep, exclude=False):
    vector_layers = metadata_json.get('vector_layers', [])
    if exclude:
        processed_layers = [layer for layer in vector_layers if layer['id'] not in layers_to_keep]
    else:
        processed_layers = [layer for layer in vector_layers if layer['id'] in layers_to_keep]
    
    tilestats = metadata_json.get('tilestats', {})
    updated_stats = tilestats.copy()
    updated_stats['layerCount'] = len(processed_layers)
    updated_stats['layers'] = [
                            stat for stat in updated_stats.get('layers', [])
                            if (exclude and stat['layer'] not in layers_to_keep) or (not exclude and stat['layer'] in layers_to_keep)
                            ]

    metadata_json['vector_layers'] = processed_layers
    metadata_json['tilestats'] = updated_stats
    
    return metadata_json


def process_mbtiles(input_mbtiles, output_mbtiles, layers_to_keep, keep_layers=True):
    if os.path.exists(output_mbtiles):
        os.remove(output_mbtiles)
    is_vector, compression_type = mbtilesfixmeta.check_vector(input_mbtiles) 
    if is_vector:
        mbtilesfixmeta.fix_metadata(input_mbtiles, compression_type)    
        shutil.copyfile(input_mbtiles, output_mbtiles)    
        with sqlite3.connect(output_mbtiles) as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT name, value FROM metadata WHERE name = 'json'")
            metadata = cursor.fetchone()
            
            if metadata:
                _, metadata_value = metadata
                metadata_json = json.loads(metadata_value)
                processed_metadata = process_metadata(metadata_json, layers_to_keep, exclude=not keep_layers)
                cursor.execute("DELETE FROM metadata WHERE name = 'json'")
                cursor.execute("INSERT INTO metadata (name, value) VALUES ('json', ?)", (json.dumps(processed_metadata),))
            
            cursor.execute("SELECT type FROM sqlite_master WHERE name='tiles'")
            result = cursor.fetchone()
            if result:
                if result[0] == 'view':
                    cursor.execute("DROP VIEW IF EXISTS tiles")
                else:
                    cursor.execute("DROP TABLE IF EXISTS tiles")
            
            cursor.execute("""
                CREATE TABLE tiles (
                    zoom_level INTEGER,
                    tile_column INTEGER,
                    tile_row INTEGER,
                    tile_data BLOB
                )
            """)
            cursor.execute("CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row)")
            
            try:
                with sqlite3.connect(input_mbtiles) as in_conn:
                    in_cursor = in_conn.cursor()
                    in_cursor.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles ORDER BY zoom_level")
                    tiles = in_cursor.fetchall()
                    
                    for zoom_level, tile_column, tile_row, tile_data in tqdm(tiles, desc="Processing tiles", unit=" tiles"):
                        if tile_data[:2] == b'\x1f\x8b':
                            tile_data = gzip.decompress(tile_data)
                        elif tile_data[:2] in [b'\x78\x9c', b'\x78\x01', b'\x78\xda']:
                            tile_data = zlib.decompress(tile_data)
                        
                        decoded_tile = decode(tile_data)
                        decoded_tile = fix_wkt(decoded_tile)
                        
                        if keep_layers:
                            filtered_tile = [item for item in decoded_tile if item["name"] in layers_to_keep]
                        else:
                            filtered_tile = [item for item in decoded_tile if item["name"] not in layers_to_keep]
                        
                        if filtered_tile:
                            try:
                                encoded_tile = encode(filtered_tile)
                                encoded_tile_gzip = gzip.compress(encoded_tile)
                                cursor.execute("""
                                    INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data)
                                    VALUES (?, ?, ?, ?)""", (zoom_level, tile_column, tile_row, encoded_tile_gzip))
                            except Exception as e:
                                logging.error(f"Error encoding tile {zoom_level}/{tile_column}/{tile_row}: {e}")
                
                description = 'Splitting MBTiles file by selected layers using mbtilessplit from vtiles'
                cursor.execute('''
                    INSERT OR REPLACE INTO metadata (name, value)
                    VALUES ('description', ?)
                ''', (description,))
                
                conn.commit()
                if keep_layers:
                    logging.info(f'Successfully saved split MBTiles into {output_mbtiles}')
                else:
                    logging.info(f'Successfully saved remaining MBTiles into {output_mbtiles}')
            
            except sqlite3.Error as e:
                logging.error(f"Database error: {e}")
            except Exception as e:
                logging.error(f"Unexpected error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Split an MBTiles file by selected layers.")
    parser.add_argument("-i", "--input", required=True, help="Path to the input MBTiles file")
    parser.add_argument("-o", "--output", required=True, help="Path to the output MBTiles file")
    parser.add_argument("-l", "--layers", nargs='+', required=True, help="List of layer names to be splitted")
    args = parser.parse_args()
    
    process_mbtiles(args.input, args.output, args.layers, keep_layers=True)
    remaining_output = f"{os.path.splitext(args.input)[0]}_remained.mbtiles"
    process_mbtiles(args.input, remaining_output, args.layers, keep_layers=False)

if __name__ == "__main__":
    main()
