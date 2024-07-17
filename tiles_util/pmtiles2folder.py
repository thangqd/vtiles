import argparse
import json
import os
from pmtiles.reader import Reader, MmapSource, all_tiles

def pmtiles_to_dir(input_file, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    with open(input_file, "r+b") as f:
        source = MmapSource(f)
        reader = Reader(source)
        
        with open(os.path.join(output_folder, "metadata.json"), "w") as metadata_file:
            metadata_file.write(json.dumps(reader.metadata()))

        for zxy, tile_data in all_tiles(source):
            directory = os.path.join(output_folder, str(zxy[0]), str(zxy[1]))
            os.makedirs(directory, exist_ok=True)
            # path = os.path.join(directory, str(zxy[2]) + ".mvt")
            path = os.path.join(directory, str(zxy[2]) + ".pbf")
            with open(path, "wb") as tile_file:
                tile_file.write(tile_data)

def main():
    parser = argparse.ArgumentParser(description="Convert PMTiles to individual MVT files.")
    parser.add_argument("-i", "--input", required=True, help="Input PMTiles file path.")
    parser.add_argument("-o", "--output", required=True, help="Output directory path.")
    args = parser.parse_args()

    input_pmtiles = args.input
    output_directory = args.output

    pmtiles_to_dir(input_pmtiles, output_directory)

if __name__ == "__main__":
    main()
