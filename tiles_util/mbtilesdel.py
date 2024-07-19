import sqlite3
import mapbox_vector_tile
import argparse
import shutil
import gzip
import json
from tqdm import tqdm

def fix_wkt(data):
    result = []
    for key in data:
        feature_collection = data[key]
        features = []
        for feature in feature_collection['features']:
            geom_type = feature['geometry']['type']
            coords = feature['geometry']['coordinates']
            if geom_type == 'Polygon':
                wkt_geom = 'POLYGON ((' + ', '.join([' '.join(map(str, pt)) for pt in coords[0]]) + '))'
            elif geom_type == 'LineString':
                wkt_geom = 'LINESTRING (' + ', '.join([' '.join(map(str, pt)) for pt in coords]) + ')'
            elif geom_type == 'MultiPolygon':
                polygons = []
                for polygon in coords:
                    polygons.append('((' + ', '.join([' '.join(map(str, pt)) for pt in polygon[0]]) + '))')
                wkt_geom = 'MULTIPOLYGON (' + ', '.join(polygons) + ')'
            elif geom_type == 'MultiLineString':
                lines = []
                for line in coords:
                    lines.append('(' + ', '.join([' '.join(map(str, pt)) for pt in line]) + ')')
                wkt_geom = 'MULTILINESTRING (' + ', '.join(lines) + ')'
            elif geom_type == 'Point':
                wkt_geom = 'POINT (' + ' '.join(map(str, coords)) + ')'
            elif geom_type == 'MultiPoint':
                points = []
                for point in coords:
                    points.append(' '.join(map(str, point)))
                wkt_geom = 'MULTIPOINT (' + ', '.join(points) + ')'
            else:
                continue  # Skip other geometry types
            features.append({
                'geometry': wkt_geom,
                'properties': feature['properties']
            })
        result.append({
            'name': key,
            'features': features
        })
    return result

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


def delete_layers_from_mbtiles(input_path, output_path, layers_to_delete):
    # Copy the input MBTiles file to the output path
    shutil.copyfile(input_path, output_path)

    # Connect to the copied MBTiles file
    with sqlite3.connect(output_path) as conn:
        # Update metadata
        update_metadata(conn, layers_to_delete)

        cursor = conn.cursor()

        # Select all tiles
        cursor.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles")
        tiles = cursor.fetchall()

        # Create tqdm progress bar
        for tile in tqdm(tiles, desc="Processing tiles", unit="tile"):
            zoom_level, tile_column, tile_row, tile_data = tile

            # Decompress the tile data if it is compressed
            if tile_data[:2] == b'\x1f\x8b':
                tile_data = gzip.decompress(tile_data)

            # Decode the tile data
            decoded_tile = mapbox_vector_tile.decode(tile_data)
            decoded_tile = fix_wkt(decoded_tile)

            # Remove the specified layers
            decoded_tile_filtered = [item for item in decoded_tile if item["name"] not in layers_to_delete]

            if len(decoded_tile_filtered) < len(decoded_tile):
                # Encode and compress the modified tile
                try:
                    encoded_tile = mapbox_vector_tile.encode(decoded_tile_filtered)
                    encoded_tile_gzip = gzip.compress(encoded_tile)

                    # Update the tile data in the database
                    cursor.execute("""
                        UPDATE tiles
                        SET tile_data = ?
                        WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?""",
                        (encoded_tile_gzip, zoom_level, tile_column, tile_row))
                except Exception as e:
                    print(f"Error processing tile {zoom_level}/{tile_column}/{tile_row}: {e}")

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
