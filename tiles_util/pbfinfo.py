import mapbox_vector_tile
import sys

def read_pbf_tile(pbf_file):
    # Read the .pbf file
    with open(pbf_file, 'rb') as f:
        tile_data = f.read()

    # Parse the .pbf tile data
    tile = mapbox_vector_tile.decode(tile_data)

    # Now 'tile' contains the parsed data from the .pbf file
    # You can access features, geometries, and properties as needed
    return tile

def main():
    # Check if the path to the .pbf file is provided
    if len(sys.argv) < 2:
        print("Please provide the path to the .pbf file as an argument.")
        return

    pbf_file = sys.argv[1]

    # Call the function to read and parse the .pbf tile
    tile_data = read_pbf_tile(pbf_file)

    # Example: Print the layers and their feature count
    for layer_name, layer_data in tile_data.items():
        num_features = len(layer_data['features'])
        print(f"Layer '{layer_name}' has {num_features} features.")

if __name__ == "__main__":
    main()
