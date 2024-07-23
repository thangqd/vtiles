import sqlite3
import shutil
import gzip
import json
import argparse
import os
from tqdm import tqdm
from tiles_util.utils.mapbox_vector_tile import encode, decode


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

def filter_metadata(metadata_json, layers_to_keep):
    # Filter vector_layers
    vector_layers = metadata_json.get('vector_layers', [])
    filtered_layers = [layer for layer in vector_layers if layer['id'] in layers_to_keep]
    
    # Update tilestats to reflect the filtered layers
    tilestats = metadata_json.get('tilestats', {})
    updated_stats = tilestats.copy()
    updated_stats['layerCount'] = len(filtered_layers)
    updated_stats['layers'] = [stat for stat in updated_stats.get('layers', []) if stat['layer'] in layers_to_keep]
    
    metadata_json['vector_layers'] = filtered_layers
    metadata_json['tilestats'] = updated_stats
    
    return metadata_json

def split_mbtiles_by_layers(input_path, output_path, layers_to_keep):
    # Copy the input MBTiles file to the output path
    shutil.copyfile(input_path, output_path)
    
    with sqlite3.connect(output_path) as conn:
        cursor = conn.cursor()
        
        # Read and filter metadata
        cursor.execute("SELECT name, value FROM metadata WHERE name = 'json'")
        metadata = cursor.fetchone()
        
        if metadata:
            _, metadata_value = metadata
            metadata_json = json.loads(metadata_value)
            filtered_metadata = filter_metadata(metadata_json, layers_to_keep)
            
            # Update metadata
            cursor.execute("DELETE FROM metadata WHERE name = 'json'")
            cursor.execute("INSERT INTO metadata (name, value) VALUES ('json', ?)", (json.dumps(filtered_metadata),))
        
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
        # also create index 
        # Copy tiles from input to output
        with sqlite3.connect(input_path) as in_conn:
            in_cursor = in_conn.cursor()
            in_cursor.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles")
            tiles = in_cursor.fetchall()
            
            # Create tqdm progress bar
            for tile in tqdm(tiles, desc="Processing tiles", unit="tile"):
                zoom_level, tile_column, tile_row, tile_data = tile
                
                # Handle possible compression
                # if tile_data[:2] == b'\x1f\x8b':
                #     tile_data = gzip.decompress(tile_data)
                # else:
                #     tile_data = gzip.compress(tile_data)

                if tile_data[:2] == b'\x1f\x8b':
                    tile_data = gzip.decompress(tile_data)

                # Decode the tile data
                decoded_tile = decode(tile_data)
                decoded_tile = fix_wkt(decoded_tile)
                
                decoded_tile_filtered = [item for item in decoded_tile if item["name"] in layers_to_keep]

                if len(decoded_tile_filtered) < len(decoded_tile):
                # Encode and compress the modified tile
                    try:
                        encoded_tile = encode(decoded_tile_filtered)
                        encoded_tile_gzip = gzip.compress(encoded_tile)
                        cursor.execute("""
                            INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data)
                            VALUES (?, ?, ?, ?)
                        """, (zoom_level, tile_column, tile_row, encoded_tile_gzip))
                    except Exception as e:
                        print(f"Error processing tile {zoom_level}/{tile_column}/{tile_row}: {e}")
        conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Split an MBTiles file by selected layers.")
    parser.add_argument("-i", "--input", required=True, help="Path to the input MBTiles file")
    parser.add_argument("-o", "--output", required=True, help="Path to the output MBTiles file")
    parser.add_argument("-l", "--layers", nargs='+', required=True, help="Names of the layers to keep")
    args = parser.parse_args()
    
    split_mbtiles_by_layers(args.input, args.output, args.layers)

if __name__ == "__main__":
    main()
