import os
import requests
import argparse
from tqdm import tqdm

def download_tile(z, x, y, url_template, output_folder, pbar):
    """Download a single tile and save it in a structured folder (z/x/y.pbf)."""
    tile_url = url_template.format(z=z, x=x, y=y)
    response = requests.get(tile_url)
    if response.status_code == 200:
        # Define the path structure: output_folder/z/x/y.pbf
        tile_folder = os.path.join(output_folder, str(z), str(x))
        os.makedirs(tile_folder, exist_ok=True)  # Create directories if they don't exist
        tile_file = os.path.join(tile_folder, f'{y}.pbf')  # Save file as y.pbf
        with open(tile_file, 'wb') as f:
            f.write(response.content)
    pbar.update(1)  # Update the progress bar after each download

def download_tiles(minzoom, maxzoom, url_template, output_folder):
    """Download all tiles from minzoom to maxzoom in a structured folder with a progress bar."""
    total_tiles = sum((2 ** z) ** 2 for z in range(minzoom, maxzoom + 1))
    with tqdm(total=total_tiles, desc="Downloading tiles", unit="tile") as pbar:
        for z in range(minzoom, maxzoom + 1):
            num_tiles = 2 ** z
            for x in range(num_tiles):
                for y in range(num_tiles):
                    download_tile(z, x, y, url_template, output_folder, pbar)

def main():
    parser = argparse.ArgumentParser(description='Download vector tiles from a tile server and store them in structured folders.')
    parser.add_argument('-url', type=str, required=True, help='URL template for vector tiles (e.g., https://your-vector-tile-server/{z}/{x}/{y}.pbf)')
    parser.add_argument('-minzoom', type=int, required=True, help='Minimum zoom level')
    parser.add_argument('-maxzoom', type=int, required=True, help='Maximum zoom level')
    parser.add_argument('-o', type=str, default='tiles', help='Output folder for downloaded tiles')

    args = parser.parse_args()

    download_tiles(args.minzoom, args.maxzoom, args.url, args.o)

if __name__ == '__main__':
    main()
