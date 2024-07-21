import sqlite3
import os
import shutil
from .mapbox_vector_tile import encode, decode
import argparse
import gzip
import json
import logging
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)

def fix_wkt(data):
    result = []
    
    for key in data:
        feature_collection = data[key]
        features = []
        
        for feature in feature_collection.get('features', []):
            geom = feature.get('geometry', {})
            geom_type = geom.get('type')
            coords = geom.get('coordinates')
            
            if geom_type is None or coords is None or (isinstance(coords, (list, dict)) and not coords):
                # Handle null or empty geometry
                wkt_geom = f'{geom_type or "GEOMETRY"} EMPTY'
                
            elif geom_type == 'Polygon':
                if not coords or not coords[0]:
                    wkt_geom = 'POLYGON EMPTY'
                else:
                    wkt_geom = 'POLYGON ((' + ', '.join([' '.join(map(str, pt)) for pt in coords[0]]) + '))'
                
            elif geom_type == 'LineString':
                if not coords:
                    wkt_geom = 'LINESTRING EMPTY'
                else:
                    wkt_geom = 'LINESTRING (' + ', '.join([' '.join(map(str, pt)) for pt in coords]) + ')'
                
            elif geom_type == 'MultiPolygon':
                if not coords:
                    wkt_geom = 'MULTIPOLYGON EMPTY'
                else:
                    polygons = []
                    for polygon in coords:
                        if not polygon:
                            polygons.append('EMPTY')
                        else:
                            polygons.append('((' + ', '.join([' '.join(map(str, pt)) for pt in polygon[0]]) + '))')
                    wkt_geom = 'MULTIPOLYGON (' + ', '.join(polygons) + ')'
                
            elif geom_type == 'MultiLineString':
                if not coords:
                    wkt_geom = 'MULTILINESTRING EMPTY'
                else:
                    lines = []
                    for line in coords:
                        if not line:
                            lines.append('EMPTY')
                        else:
                            lines.append('(' + ', '.join([' '.join(map(str, pt)) for pt in line]) + ')')
                    wkt_geom = 'MULTILINESTRING (' + ', '.join(lines) + ')'
                
            elif geom_type == 'Point':
                if not coords:
                    wkt_geom = 'POINT EMPTY'
                else:
                    wkt_geom = 'POINT (' + ' '.join(map(str, coords)) + ')'
                
            elif geom_type == 'MultiPoint':
                if not coords:
                    wkt_geom = 'MULTIPOINT EMPTY'
                else:
                    points = []
                    for point in coords:
                        points.append(' '.join(map(str, point)))
                    wkt_geom = 'MULTIPOINT (' + ', '.join(points) + ')'
                
            else:
                # Skip unsupported geometry types
                continue
            
            features.append({
                'geometry': wkt_geom,
                'properties': feature.get('properties', {})
            })
        
        result.append({
            'name': key,
            'features': features
        })
    
    return result

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


def merge_tiles(tile1, tile2, z=None, x=None, y=None):
    try:        
        if tile1 and tile2:
            if tile1[:2] == b'\x1f\x8b':
                tile1 = gzip.decompress(tile1)
            decoded_tile1 = decode(tile1)
            decoded_tile1_fixed = fix_wkt(decoded_tile1)

            if tile2[:2] == b'\x1f\x8b':
                tile2 = gzip.decompress(tile2)
            decoded_tile2 = decode(tile2)
            decoded_tile2_fixed = fix_wkt(decoded_tile2)

            merged_tiles = merge_json_data (decoded_tile1_fixed,decoded_tile2_fixed)
            merged_tiles_encoded = encode(merged_tiles)
            encoded_tile_encoded_gzip = gzip.compress(merged_tiles_encoded)
            
            return encoded_tile_encoded_gzip
        elif tile1:
            return gzip.compress(tile1) if tile1[:2] != b'\x1f\x8b' else tile1
        elif tile2:
            return gzip.compress(tile2) if tile2[:2] != b'\x1f\x8b' else tile2
        return None
        
    except Exception as e:
        logging.error(f"Error merging tiles at (z={z}, x={x}, y={y}): {e}")
        file_name = f"{z}_{x}_{y}.json"
        # Save merged_tiles content to the file
        with open(file_name, 'w') as f:
            # Serialize merged_tiles to JSON
            json.dump(merged_tiles, f, indent=2)
        logging.info(f"Saved merged tiles data to {file_name}")
        if tile1:
            return gzip.compress(tile1) if tile1[:2] != b'\x1f\x8b' else tile1


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

        connections = [sqlite3.connect(mbtiles) for mbtiles in mbtiles_files]
        conn_out = sqlite3.connect(output_mbtiles)
        cursors = [conn.cursor() for conn in connections]
        cur_out = conn_out.cursor()

        cur_out.execute('CREATE TABLE IF NOT EXISTS tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB)')
        cur_out.execute('CREATE TABLE IF NOT EXISTS metadata (name TEXT, value TEXT)')
        cur_out.execute('CREATE UNIQUE INDEX IF NOT EXISTS tile_index ON tiles (zoom_level, tile_column, tile_row)')

        # Merging tiles
        tiles = {}
        for i, cursor in enumerate(cursors):
            mbtiles_name = os.path.basename(mbtiles_files[i])
            cursor.execute('SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles')
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
        for i, cursor in enumerate(cursors):
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
        logging.error(f"Error merging MBTiles: {e}")

def main():
    parser = argparse.ArgumentParser(description="Merge multiple MBTiles files into a single MBTiles file.")
    parser.add_argument('-i', '--input', nargs='+', required=True, help='Input MBTiles files to merge.')
    parser.add_argument('-o', '--output', required=True, help='Output merged MBTiles file.')

    args = parser.parse_args()

    merge_mbtiles(args.input, args.output)

if __name__ == '__main__':
    main()
