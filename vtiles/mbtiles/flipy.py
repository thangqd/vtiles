#!/usr/bin/env python
import os
import shutil
import sys
import argparse
from tqdm import tqdm

def convert_tms_to_xyz(inDIR, copyDIR):
    # Check if output directory exists, exit if it does
    if os.path.exists(copyDIR):
        sys.exit("ERROR: The output directory already exists!")

    # Create the root of the output directory if it does not exist
    if not os.path.exists(copyDIR):
        os.makedirs(copyDIR)

    # Copy all files from the root of inDIR to the root of copyDIR, including metadata.json
    root_files = [f for f in os.listdir(inDIR) if os.path.isfile(os.path.join(inDIR, f))]
    for root_file in tqdm(root_files, desc="Copying metadata (if existed)", unit=' ', ncols=80, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{percentage:.0f}%]'):
        shutil.copy(os.path.join(inDIR, root_file), os.path.join(copyDIR, root_file))

    # Count the total number of files to process
    total_files = sum([len(files) for rVal, dName, files in os.walk(inDIR) if rVal != inDIR])

    # Initialize the progress bar for nested files
    with tqdm(total=total_files, desc="Processing files", unit=' ', ncols=80, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{percentage:.0f}%]') as pbar:
        for rVal, dName, fList in os.walk(inDIR):
            # Skip the root directory as it has already been handled
            if rVal == inDIR:
                continue

            # Calculate the relative path for the new directory structure
            relPath = os.path.relpath(rVal, inDIR)
            newpath = os.path.join(copyDIR, relPath)
            if not os.path.exists(newpath):
                os.makedirs(newpath)

            for fileName in fList:
                zxParts = os.path.normpath(relPath).split(os.sep)
                if len(zxParts) < 2:
                    print(f"Skipping file due to insufficient path depth: {fileName}")
                    continue

                z = int(zxParts[0])
                y = int(fileName.split(".")[0])
                fileExtension = fileName.split(".")[1]
                newY = str((2**z - 1) - y) + "." + fileExtension
                shutil.copyfile(os.path.join(rVal, fileName), os.path.join(newpath, newY))
                pbar.update(1)

def main():
    # Get the command line arguments and set up some variables
    parser = argparse.ArgumentParser(description='Convert TMS <--> XYZ tiling scheme for a tiles folder')
    parser.add_argument('-i', type=str, help='input directorty')
    parser.add_argument('-o', type=str, help='output directory')
    args = parser.parse_args()
    
    convert_tms_to_xyz(args.i, args.o)

if __name__ == "__main__":
    main()
