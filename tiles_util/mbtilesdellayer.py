import sqlite3
import mapbox_vector_tile
import argparse
import shutil
import gzip,zlib
import geojson, json
from collections import defaultdict
from io import BytesIO
import csv


def repair_wkt(data):
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



def delete_layer_from_mbtiles(input_path, output_path, layer_name):
    # Copy the input MBTiles file to the output path
    shutil.copyfile(input_path, output_path)

    # Connect to the copied MBTiles file
    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()

    # Select all tiles
    # cursor.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles where zoom_level=0 and tile_column=0 and tile_row=0  ")
    cursor.execute("SELECT tile_data FROM tiles where zoom_level=0 and tile_column=0 and tile_row=0")
    tiles = cursor.fetchone()
    tile_data = tiles[0]
    print('origin:' ,tile_data)
    print('#######################')
    # for zoom_level, tile_column, tile_row, tile_data in tiles:
    # try:
    #     decompressed_data = gzip.decompress(tile_data)
    #     print('gzib')
    # except (OSError, EOFError):        
    #     decompressed_data = tile_data  # Assume data is not compressed
    #     print('no gzib')
    # print('original: ', tile_data)
    with BytesIO(tile_data) as byte_stream:
        decompressed_data = gzip.decompress(byte_stream.getvalue())
    # decompressed_data = gzip.decompress(tile_data)
    print('decompressed:' ,decompressed_data)
    print('#######################')

    decoded_tile = None
    # decompressed_data = repair_wkt(decompressed_data)

    # # Decode the tile data
    decoded_tile = mapbox_vector_tile.decode(decompressed_data)
    # print('decoded:', decoded_tile)
    decoded_tile = repair_wkt(decoded_tile)
    # print('repaired:', decoded_tile)


    # print('decoded',mapbox_vector_tile.decode(encoded) )
    # # Remove the specified layer if it exists
    # # try:
    print('decoded: ', decoded_tile)
    print('#################')
    decoded_tile_deleted = [item for item in decoded_tile if item["name"] != layer_name]
    # print ('decoded_tile_deleted: ', decoded_tile_deleted)
    # for layername, layerdata in decoded_tile:
    #     if (layer_name == layername):
    #         print(f"Layer: {layername}")
    #     del decoded_tile[0]
    #     break

    # # print (decoded_tile)  
    encoded_tile = mapbox_vector_tile.encode(decoded_tile_deleted)
    with BytesIO(encoded_tile) as byte_stream:
        encoded_tile_gzib = gzip.compress(byte_stream.getvalue())
    # encoded_tile_gzib = gzip.compress(encoded_tile)
    print('encoded: ', encoded_tile)
    print('#################')


    # decoded_again = mapbox_vector_tile.decode(encoded_tile)
    # print('decoded_again: ', decoded_again)
    # print('#################')
    # # # Serialize and encode the dictionary to JSON bytes
    # json_data = json.dumps(decoded_tile)
    # byte_data = json_data.encode('utf-8')

    # # Compress the byte data
    # buffer = BytesIO()
    # with gzip.GzipFile(fileobj=buffer, mode='wb') as gz_file:
    #     gz_file.write(byte_data)
    # compressed_data = buffer.getvalue()
    
    # # Decompress the compressed data
    # buffer = BytesIO(compressed_data)
    # with gzip.GzipFile(fileobj=buffer, mode='rb') as gz_file:
    #     decompressed_data = gz_file.read()

    # # Deserialize the decompressed bytes back to a dictionary
    # decoded_tile_reloaded = json.loads(decompressed_data.decode('utf-8'))

    # # Output for verification
    # print(decoded_tile)


    # encoded_tile = mapbox_vector_tile.encode(decoded_tile)

    # print(encoded_tile)
     # Update the tile in the database
    # with BytesIO(encoded_tile) as byte_stream:
    #     encoded_tile_compressed = gzip.compress(byte_stream.getvalue())

    # print('encoded_tile_compressed:', encoded_tile_compressed)
    # print('#################')

    # with BytesIO(encoded_tile_compressed) as byte_stream:
    #     encoded_tile_decompressed = gzip.decompress(byte_stream.getvalue())

    # print('decompressed again:', encoded_tile_decompressed)
    # print('#################')

    # cursor.execute("""
    #     UPDATE tiles
    #     SET tile_data = ?
    #     WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?""", (encoded_tile, 0, 0, 0))
    
    cursor.execute("""
        UPDATE tiles
        SET tile_data = ?
        WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?""", (encoded_tile_gzib, 0, 0, 0))
        # WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?""", (encoded_tile, 0, 0, 0))

    # # Decompress the compressed data
    # buffer = BytesIO(compressed_data)
    # with gzip.GzipFile(fileobj=buffer, mode='rb') as gz_file:
    #     decompressed_data = gz_file.read()

    # # Deserialize the decompressed bytes back to a dictionary
    # decoded_tile_reloaded = json.loads(decompressed_data.decode('utf-8'))

    # Output for verification
    # print(decoded_tile_reloaded)

    # for layer_name, layer_data in decoded_tile_reloaded.items():
    #     print(f"Layer Name: {layer_name}")
        
    # encoded_tile = mapbox_vector_tile.encode(decoded_tile_reloaded)
    # print(encoded_tile)
        # # Update the tile in the database
        # cursor.execute("""
        #     UPDATE tiles
        #     SET tile_data = ?
        #     WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?
        # """, (encoded_tile, 0, 0, 0))

        
            # for feature in layer_data['features']:
            #     print(f"Feature Type: {feature['type']}")
            #     print(f"Feature Geometry: {feature['geometry']}")
            #     print(f"Feature Properties: {feature['properties']}")
        # for layername, layerdata in decoded_tile.items():
        #     print(f"Layer: {layername}")

        # if layer_name in decoded_tile:
        #     print (decoded_tile[layer_name])
            # del decoded_tile['layers'][layer_name]

            # # Encode the modified tile
            # encoded_tile = mapbox_vector_tile.encode(decoded_tile)

            # # Update the tile in the database
            # cursor.execute("""
            #     UPDATE tiles
            #     SET tile_data = ?
            #     WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?
            # """, (encoded_tile, zoom_level, tile_column, tile_row))
    # except Exception as e:
    #     # print(f"Error processing tile at zoom {zoom_level}, column {tile_column}, row {tile_row}: {e}")
    #     print('lalala')
    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Delete a layer from an MBTiles file.")
    parser.add_argument("-i", "--input", required=True, help="Path to the input MBTiles file")
    parser.add_argument("-o", "--output", required=True, help="Path to the output MBTiles file")
    parser.add_argument("-l", "--layer", required=True, help="Name of the layer to delete")

    args = parser.parse_args()
    delete_layer_from_mbtiles(args.input, args.output, args.layer)
   
if __name__ == "__main__":
    main()
