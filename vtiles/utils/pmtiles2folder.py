import argparse
import json
import os
from .pmtiles.reader import Reader, MmapSource, all_tiles  
from tqdm import tqdm 

def pmtiles_to_folder(input_file, output_folder):
    """
    Convert PMTiles to a folder structure.

    Parameters:
    input_file (str): Path to the input PMTiles file.
    output_folder (str): Path to the output directory.
    """
    os.makedirs(output_folder, exist_ok=True)  # Create output folder if it doesn't exist
    with open(input_file, "r+b") as f:
        source = MmapSource(f)
        reader = Reader(source)
        
        # Write metadata to a JSON file
        with open(os.path.join(output_folder, "metadata.json"), "w") as metadata_file:
            metadata_file.write(json.dumps(reader.metadata()))

        # Get total number of tiles for progress bar
        total_tiles = len(list(all_tiles(source)))
        
        # Iterate over all tiles and write them to the output folder
        for zxy, tile_data in tqdm(all_tiles(source), total=total_tiles, desc="Processing tiles"):
            z, x, y = zxy
            directory = os.path.join(output_folder, str(z), str(x))
            os.makedirs(directory, exist_ok=True)
            path = os.path.join(directory, str(y) + ".pbf")  # Change extension as needed
            with open(path, "wb") as tile_file:
                tile_file.write(tile_data)

def main():
    """
    Main function to parse arguments and call the conversion function.
    """
    parser = argparse.ArgumentParser(description="Convert PMTiles to folder.")
    parser.add_argument("-i", "--input", required=True, help="Input PMTiles file path.")
    parser.add_argument("-o", "--output", required=True, help="Output directory path.")
    args = parser.parse_args()

    input_pmtiles = args.input
    output_directory = args.output

    pmtiles_to_folder(input_pmtiles, output_directory)

if __name__ == "__main__":
    main()
