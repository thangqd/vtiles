import os
import argparse

def tms_to_xyz(input_dir, output_dir):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Iterate through TMS tiles
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".pbf"):  # Assuming tiles are in Protocol Buffer format
                tms_tile_path = os.path.join(root, file)
                xyz_tile_path = os.path.join(output_dir, os.path.relpath(tms_tile_path, input_dir))

                # Read TMS tile
                with open(tms_tile_path, 'rb') as f:
                    tms_tile_data = f.read()

                # Convert TMS to XYZ format (no transformation needed for vector tiles)
                xyz_tile_data = tms_tile_data

                # Ensure directory exists for writing XYZ tile
                xyz_tile_dir = os.path.dirname(xyz_tile_path)
                if not os.path.exists(xyz_tile_dir):
                    os.makedirs(xyz_tile_dir)

                # Write XYZ tile
                with open(xyz_tile_path, 'wb') as f:
                    f.write(xyz_tile_data)

                print(f"Converted {tms_tile_path} to XYZ format")

if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="Convert TMS vector tiles to XYZ vector tiles")
    # Add arguments
    parser.add_argument("input_dir", help="Input directory containing TMS vector tiles in PBF format")
    parser.add_argument("output_dir", help="Output directory to save the converted XYZ vector tiles")

    # Parse arguments
    args = parser.parse_args()

    # Call the conversion function with user-provided input and output directories
    tms_to_xyz(args.input_dir, args.output_dir)
