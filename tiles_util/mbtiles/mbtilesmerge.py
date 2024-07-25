import sqlite3
import os
import shutil
from tiles_util.utils.mapbox_vector_tile import encode, decode
import argparse
import gzip, zlib
import json
import logging
from tqdm import tqdm
from tiles_util.utils.geopreocessing import fix_wkt

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


def merge_tiles(tile1, tile2):
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
                return tile1
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


def get_zoom_levels_from_tiles(mbtiles_path):
    conn = sqlite3.connect(mbtiles_path)
    cursor = conn.cursor()
    cursor.execute("SELECT MIN(zoom_level), MAX(zoom_level) FROM tiles;")
    min_zoom, max_zoom = cursor.fetchone()
    conn.close()
    return min_zoom, max_zoom

def get_combined_zoom_levels(mbtiles_files):
    combined_min_zoom = None
    combined_max_zoom = None
    
    for mbtiles_file in mbtiles_files:
        min_zoom, max_zoom = get_zoom_levels_from_tiles(mbtiles_file)
        
        if combined_min_zoom is None or min_zoom < combined_min_zoom:
            combined_min_zoom = min_zoom
        
        if combined_max_zoom is None or max_zoom > combined_max_zoom:
            combined_max_zoom = max_zoom
    
    return combined_min_zoom, combined_max_zoom

def merge_mbtiles(mbtiles_1,mbtiles_2,output_mbtiles):   
    if os.path.exists(output_mbtiles):
        os.remove(output_mbtiles)
    minzoom, maxzoom = get_combined_zoom_levels([mbtiles_1,mbtiles_2])
    with sqlite3.connect(output_mbtiles) as conn:
        cursor = conn.cursor()
        cursor.executescript("""
        CREATE TABLE metadata (name TEXT, value TEXT);
        CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB);
        CREATE UNIQUE INDEX name ON metadata (name);
        CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row);
        """)
        metadata = [
        ("name", "merged MBTiles"),
        ("type", "overlay"),
        ("version", "1.0"),
        ("description", "Merged MBTiles by tiles_util.mbtilesmerge"),
        ("format", "pbf"),
        ("minzoom", str(minzoom)),
        ("maxzoom", str(maxzoom))
        ]
        cursor.executemany("INSERT INTO metadata (name, value) VALUES (?, ?)", metadata)
        conn.commit


def main():
    parser = argparse.ArgumentParser(description="Merge multiple MBTiles files into a single MBTiles file.")
    parser.add_argument('-i1', '--input1', required=True, help='First Input MBTiles to merge.')
    parser.add_argument('-i2', '--input2', required=True, help='Second Input MBTiles to merge.')
    parser.add_argument('-o', '--output', required=True, help='Output merged MBTiles file.')

    args = parser.parse_args()

    merge_mbtiles(args.input1, args.input2, args.output)

if __name__ == '__main__':
    main()
