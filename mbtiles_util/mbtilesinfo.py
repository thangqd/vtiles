import sqlite3, json
import argparse, os, sys

# Check if mbtiles is vector or raster
def check_vector(input_filename):    
    connection = sqlite3.connect(input_filename)
    cursor = connection.cursor()
    cursor.execute("SELECT value FROM metadata WHERE name='format'")
    format_info = cursor.fetchone()

    # Close the database connection
    connection.close()

    # Check if format_info is not None
    if format_info:
        format_value = format_info[0].lower()
        if 'pbf' in format_value or 'vector' in format_value:
            return 1
        elif 'png' in format_value or 'jpg' in format_value or 'webp' in format_value or 'raster' in format_value:
            return 0
    else:
        return -1

# Read vector metadata
def read_vector_metadata(input_filename):
    """Read metadata from vector MBTiles file."""
    connection = sqlite3.connect(input_filename)
    cursor = connection.cursor()
    
    # Extract metadata
    # cursor.execute("SELECT name, value FROM metadata where name <>'json'")
    cursor.execute("SELECT name, value FROM metadata where name <> 'json'")
    metadata = dict(cursor.fetchall())
    
    cursor.close()
    connection.close()
    
    return metadata

# Read raster metadata
def read_raster_metadata(input_filename):
    """Read metadata from raster MBTiles file."""
    connection = sqlite3.connect(input_filename)
    cursor = connection.cursor()
    
    # Extract metadata
    cursor.execute("SELECT name, value FROM metadata")
    metadata = dict(cursor.fetchall())
    
    cursor.close()
    connection.close()
    
    return metadata

def count_tiles(input_filename):
    """Count the number of tiles in the MBTiles file."""
    connection = sqlite3.connect(input_filename)
    cursor = connection.cursor()
    
    # Count the number of tiles
    cursor.execute("SELECT COUNT(*) FROM tiles")
    num_tiles = cursor.fetchone()[0]
    
    cursor.close()
    connection.close()
    
    return num_tiles

# list all vector layers
def read_vector_layers(input_filename):    
    connection = sqlite3.connect(input_filename)
    cursor = connection.cursor()
    cursor.execute("SELECT name, value FROM metadata where name = 'json'")
    json_content = cursor.fetchone()[1]
    layers_json = json.loads(json_content)
    # print (layers_json)
    if "vector_layers" in layers_json:
      vector_layers = layers_json["vector_layers"]
      print("Vector layers:")
      for index, layer in enumerate(vector_layers):
          row_index = index + 1
          layer_id  = layer["id"]
          print(f"{row_index}: {layer_id}")
          # print("  Description:", layer.get("description", "N/A"))
          # print("  Min zoom:", layer.get("minzoom", "N/A"))
          # print("  Max zoom:", layer.get("maxzoom", "N/A"))
          # print("  Fields:", layer.get("fields", "N/A"))
    else:
      print("No 'vector_layers' found in metadata.")
    # Write metadata to JSON content
    # metadata_json_path = os.path.join(os.path.dirname(input_filename), "tiles.json")
    # with open(metadata_json_path, "w") as metadata_file:
    #     json.dump(layers_json, metadata_file, indent=4)
    # print ("Writing tiles.json done!")

def main():
    if len(sys.argv) != 2:
      print("Please provide the mbtiles input filename.")
      return

    input_filename = sys.argv[1]
    if (os.path.exists(input_filename)):
        if check_vector(input_filename) == 1: # vector
            metadata = read_vector_metadata(input_filename)
            num_tiles = count_tiles(input_filename)
            print("Metadata:")
            for key, value in metadata.items():
                print(f"{key}: {value}")

            print(f"Total number of tiles: {num_tiles}")
            read_vector_layers(input_filename)
        elif check_vector(input_filename) == 0: # raster
            metadata = read_raster_metadata(input_filename)
            num_tiles = count_tiles(input_filename)
            print("Metadata:")
            for key, value in metadata.items():
                print(f"{key}: {value}")

            print(f"Total number of tiles: {num_tiles}")
    else: 
        print ('MBTiles file does not exist!. Please recheck and input a correct file path.')
        return

if __name__ == "__main__":
    main()
