import sqlite3
import mapbox_vector_tile
import argparse
import shutil
import os

def delete_layer_from_mbtiles(input_path, output_path, layer_name):
    # Copy the input MBTiles file to the output path
    shutil.copyfile(input_path, output_path)

    # Connect to the copied MBTiles file
    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()

    # Select all tiles
    cursor.execute("SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles")
    tiles = cursor.fetchall()

    for zoom_level, tile_column, tile_row, tile_data in tiles:
        try:
            # Decode the tile
            decoded_tile = mapbox_vector_tile.decode(tile_data)

            # Remove the specified layer if it exists
            if layer_name in decoded_tile['layers']:
                del decoded_tile['layers'][layer_name]

                # Encode the modified tile
                encoded_tile = mapbox_vector_tile.encode(decoded_tile)

                # Update the tile in the database
                cursor.execute("""
                    UPDATE tiles
                    SET tile_data = ?
                    WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?
                """, (encoded_tile, zoom_level, tile_column, tile_row))
        except Exception as e:
            print(f"Error processing tile at zoom {zoom_level}, column {tile_column}, row {tile_row}: {e}")

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
    print(f"Layer '{args.layer}' has been deleted from {args.output}")

if __name__ == "__main__":
    main()
