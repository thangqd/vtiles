import sqlite3
import mapbox_vector_tile
import argparse
import gzip

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

def delete_layer_from_mbtiles(input_mbtiles, output_mbtiles, layer_to_delete):
    # Connect to the MBTiles database
    conn = sqlite3.connect(input_mbtiles)
    cursor = conn.cursor()

    # Create a new MBTiles database
    conn_out = sqlite3.connect(output_mbtiles)
    cursor_out = conn_out.cursor()
    cursor_out.execute('''
        CREATE TABLE metadata (
            name TEXT,
            value TEXT
        )
    ''')
    cursor_out.execute('''
        CREATE TABLE tiles (
            zoom_level INTEGER,
            tile_column INTEGER,
            tile_row INTEGER,
            tile_data BLOB
        )
    ''')

    # Copy metadata
    cursor.execute('SELECT name, value FROM metadata')
    for row in cursor.fetchall():
        cursor_out.execute('INSERT INTO metadata (name, value) VALUES (?, ?)', row)

    # Copy and modify tiles
    cursor.execute('SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles order by zoom_level')
    for zoom, col, row, tile_data in cursor.fetchall():
        tile_data_decompressed = gzip.decompress(tile_data)
        tile_data_decompressed_decoded = mapbox_vector_tile.decode(tile_data_decompressed)
        tile_data_decompressed_decoded_fixed = fix_wkt(tile_data_decompressed_decoded)
        print (tile_data_decompressed_decoded_fixed)
        # modified_tile = {}
        # for layer_name, layer_data in tile.items():
        #     if layer_name != layer_to_delete:
        #         modified_tile[layer_name] = layer_data
        encoded_tile = mapbox_vector_tile.encode(tile_data_decompressed_decoded_fixed)
        print(encoded_tile)
        encoded_tile_gzib= gzip.compress(encoded_tile)
        print(encoded_tile_gzib)
        cursor_out.execute('INSERT INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)', (zoom, col, row, sqlite3.Binary(encoded_tile)))
        break        

    # Commit and close the connections
    conn_out.commit()
    conn.close()
    conn_out.close()

def main():
    parser = argparse.ArgumentParser(description='Delete a layer from an MBTiles file.')
    parser.add_argument('-i', '--input', required=True, help='Path to the input MBTiles file.')
    parser.add_argument('-o', '--output', required=True, help='Path to the output MBTiles file.')
    parser.add_argument('-l', '--layer', required=True, help='Name of the layer to delete.')
    
    args = parser.parse_args()
    
    delete_layer_from_mbtiles(args.input, args.output, args.layer)

if __name__ == '__main__':
    main()
