import zipfile
import os
import argparse
from tqdm import tqdm

def extract_vtpk(vtpk_path, output_dir):
    # Check if the output directory exists, if not, create it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Open the VTPK file
    with zipfile.ZipFile(vtpk_path, 'r') as zip_ref:
        # Get the list of files in the archive
        file_list = zip_ref.namelist()
        
        # Use tqdm to display a progress bar while extracting files
        for file in tqdm(file_list, desc="Extracting VTPK", unit="file"):
            zip_ref.extract(file, output_dir)

    print(f'Extracted VTPK to {output_dir}')

def main():
    # Initialize the argument parser
    parser = argparse.ArgumentParser(description="Extract VTPK (Vector Tile Package) to a specified folder.")
    
    # Define input and output arguments
    parser.add_argument('-i', '--input', required=True, help="Path to the input VTPK file")
    parser.add_argument('-o', '--output', required=True, help="Path to the output directory")
    
    # Parse the command-line arguments
    args = parser.parse_args()

    # Extract the VTPK
    extract_vtpk(args.input, args.output)

if __name__ == '__main__':
    main()
