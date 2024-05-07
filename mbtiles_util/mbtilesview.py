import argparse
import leafmap.foliumap as leafmap

def main(mbtiles_file):
    # Create a map object
    m = leafmap.Map()

    # Add the .mbtiles file as a TileLayer
    m.add_tile_layer(mbtiles_file, name="My MBTiles Layer", attribution ="Leafmap")

    # Display the map
    m
    m.save('mbview.html')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Display an MBTiles file on a map.")
    parser.add_argument("mbtiles_file", type=str, help="Path to the .mbtiles file")
    args = parser.parse_args()
    main(args.mbtiles_file)
