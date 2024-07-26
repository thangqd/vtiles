import sqlite3
import os
import shutil
from tiles_util.utils.mapbox_vector_tile import encode, decode
from tiles_util.utils.geopreocessing import fix_wkt
import argparse
import gzip, zlib
import json
import logging
from tqdm import tqdm

#### may got error when running not starting by a polygon layers
# mbtilesmerge -o ./data/_lalala.mbtiles -i ./data/polyline.mbtiles ./data/point.mbtiles ./data/polygon.mbtiles

logging.basicConfig(level=logging.INFO)

def merge_json_data(data1, data2):
    # Create a dictionary to combine features by layer name
    combined_data = {}
    
    # Add features from the first JSON data
    for layer in data1:
        name = layer['name']
        if name not in combined_data:
            combined_data[name] = layer
        else:
            combined_data[name]['features'].extend(layer['features'])

    # Add features from the second JSON data
    for layer in data2:
        name = layer['name']
        if name not in combined_data:
            combined_data[name] = layer
        else:
            combined_data[name]['features'].extend(layer['features'])

    # Convert combined data to a list
    merged_data = list(combined_data.values())
    
    return merged_data

def merge_tiles(tile1, tile2,z=None, x=None, y=None):
    try:        
        if tile1 and tile2:
            if tile1[:2] == b'\x1f\x8b':
                tile1 = gzip.decompress(tile1)
            elif tile1[:2] == b'\x78\x9c' or tile1[:2] == b'\x78\x01' or tile1[:2] == b'\x78\xda':
                tile1 = zlib.decompress(tile1)
            decoded_tile1 = decode(tile1)
            decoded_tile1_fixed = fix_wkt(decoded_tile1)

            if tile2[:2] == b'\x1f\x8b':
                tile2 = gzip.decompress(tile2)
            elif tile2[:2] == b'\x78\x9c' or tile2[:2] == b'\x78\x01' or tile2[:2] == b'\x78\xda':
                tile2 = zlib.decompress(tile2)
            decoded_tile2 = decode(tile2)
            decoded_tile2_fixed = fix_wkt(decoded_tile2)

            merged_tiles = merge_json_data (decoded_tile1_fixed,decoded_tile2_fixed)
            # print (merged_tiles)
            merged_tiles_encoded = encode(merged_tiles)
            encoded_tile_encoded_gzip = gzip.compress(merged_tiles_encoded)   
            return encoded_tile_encoded_gzip
                
        elif tile1:
            if tile1[:2] == b'\x1f\x8b':
                return tile1
            elif tile1[:2] == b'\x78\x9c' or tile1[:2] == b'\x78\x01' or tile1[:2] != b'\x78\xda':
                tile1_decompressed_zlib = zlib.decompress(tile1)
                return gzip.compress(tile1_decompressed_zlib)
                
        elif tile2:
            if tile2[:2] == b'\x1f\x8b':
                return tile2
            elif tile2[:2] == b'\x78\x9c' or tile2[:2] == b'\x78\x01' or tile2[:2] != b'\x78\xda':
                tile2_decompressed_zlib = zlib.decompress(tile2)
                return gzip.compress(tile2_decompressed_zlib)     
        
    except Exception as e:
        return None

def merge_vector_layers(layer1, layer2):
    layer1_ids = {layer['id'] for layer in layer1}
    merged_layers = layer1[:]

    for layer in layer2:
        if layer['id'] in layer1_ids:
            continue  # Skip duplicate layers by 'id'
        merged_layers.append(layer)
    
    return merged_layers

def merge_tilestats(stats1, stats2):
    stats1_layers = {layer['layer']: layer for layer in stats1['layers']}
    merged_layers = stats1['layers'][:]

    for layer in stats2['layers']:
        if layer['layer'] in stats1_layers:
            stats1_layer = stats1_layers[layer['layer']]
            stats1_layer['count'] += layer['count']
            stats1_layer['attributeCount'] += layer['attributeCount']
            stats1_layer['attributes'].extend(layer['attributes'])
        else:
            merged_layers.append(layer)
    
    return {
        "layerCount": len(merged_layers),
        "layers": merged_layers
    }

def merge_json_metadata(json1, json2):
    if not json1:
        return json2
    if not json2:
        return json1

    dict1 = json.loads(json1)
    dict2 = json.loads(json2)

    merged_dict = {**dict1}

    if "vector_layers" in dict1 and "vector_layers" in dict2:
        merged_dict["vector_layers"] = merge_vector_layers(dict1["vector_layers"], dict2["vector_layers"])

    if "tilestats" in dict1 and "tilestats" in dict2:
        merged_dict["tilestats"] = merge_tilestats(dict1["tilestats"], dict2["tilestats"])

    return json.dumps(merged_dict)

def merge_metadata(metadata_dicts):
    merged_metadata = {}
    for metadata in metadata_dicts:
        for name, value in metadata.items():
            if name in merged_metadata:
                if name.endswith('json'):  # Check if the metadata name suggests JSON content
                    merged_metadata[name] = merge_json_metadata(merged_metadata[name], value)
                else:
                    if merged_metadata[name] != value:
                        merged_metadata[name] += '; ' + value
            else:
                merged_metadata[name] = value
    return merged_metadata

def merge_mbtiles(mbtiles_files, output_mbtiles):
    try:
        if os.path.exists(output_mbtiles):
            os.remove(output_mbtiles)
        shutil.copyfile(mbtiles_files[0], output_mbtiles)

        conn_out = sqlite3.connect(output_mbtiles)       
        cur_out = conn_out.cursor()

        cur_out.execute('CREATE TABLE IF NOT EXISTS metadata (name TEXT, value TEXT)')
        cur_out.execute('DROP TABLE IF EXISTS tiles_new;')
        cur_out.execute('CREATE TABLE tiles_new (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB, PRIMARY KEY (zoom_level, tile_column, tile_row))')
        cur_out.execute('''
            INSERT INTO tiles_new (zoom_level, tile_column, tile_row, tile_data)
            SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles;
            ''')
        
        cur_out.execute("SELECT type FROM sqlite_master WHERE name='tiles'")  
        result = cur_out.fetchone()
        if result:
            if result[0] == 'view':
                cur_out.execute('DROP VIEW tiles')
            elif result[0] == 'table':
                cur_out.execute('DROP TABLE tiles')
        cur_out.execute('ALTER TABLE tiles_new RENAME TO tiles')
        cur_out.execute('CREATE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row)')
    
        # Merging tiles   
        cur_out.execute('SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles ORDER BY zoom_level')          
        output_rows = cur_out.fetchall()
        tiles = {}

        for (z, x, y, tile) in output_rows:
            key = (z, x, y)
            tiles[key] = tile
        
        connections = [sqlite3.connect(mbtiles) for mbtiles in mbtiles_files]
        cursors_in = [conn.cursor() for conn in connections]
        for i, cursor in enumerate(cursors_in):
            if i == 0:
                continue  # Skip the cursor for the first MBTiles file     
            mbtiles_name = os.path.basename(mbtiles_files[i])
            cursor.execute('SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles ORDER BY zoom_level')
            rows = cursor.fetchall()
            for (z, x, y, tile) in tqdm(rows, desc=f"Merging tiles from {mbtiles_name}"):
                key = (z, x, y)
                if key in tiles:
                    tiles[key] = merge_tiles(tiles[key], tile, z, x, y)
                else:
                    tiles[key] = tile

        for key, tile in tqdm(tiles.items(), desc="Inserting merged tiles"):
            cur_out.execute('INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)', (key[0], key[1], key[2], tile))

        # Merging metadata
        metadata_dicts = []
        for i, cursor in enumerate(cursors_in):
            if i == 0:
                continue  # Skip the cursor for the first MBTiles file     
            mbtiles_name = os.path.basename(mbtiles_files[i])
            cursor.execute('SELECT name, value FROM metadata')
            metadata_dicts.append({name: value for name, value in cursor.fetchall()})

        merged_metadata = merge_metadata(metadata_dicts)

        for name, value in tqdm(merged_metadata.items(), desc="Inserting merged metadata"):
            cur_out.execute('INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)', (name, value))

        for conn in connections:
            conn.close()
        
        conn_out.commit()
        conn_out.close()
    except Exception as e:
            logging.error(f"Error Merging MBTiles: {e}")

def main():
    parser = argparse.ArgumentParser(description="Merge multiple MBTiles files into a single MBTiles file.")
    parser.add_argument('-i', '--input', nargs='+', required=True, help='Input MBTiles files to merge.')
    parser.add_argument('-o', '--output', required=True, help='Output merged MBTiles file.')

    args = parser.parse_args()

    merge_mbtiles(args.input, args.output)

if __name__ == '__main__':
    main()