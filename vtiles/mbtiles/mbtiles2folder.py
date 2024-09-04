import os, math
import sqlite3
import json
import argparse
from tqdm import tqdm
from vtiles.utils.geopreocessing import flip_y, safe_makedir

def extract_metadata(cursor):
  """Extract metadata from MBTiles file."""
  cursor.execute("SELECT name, value FROM metadata")
  metadata_rows = cursor.fetchall()
  metadata = {}
  for name, value in metadata_rows:
    metadata[name] = value
  return metadata

def write_metadata_to_json(metadata, dirname):
  """Write metadata to JSON file."""
  metadata_json_path = os.path.join(dirname, "metadata.json")
  with open(metadata_json_path, "w") as metadata_file:
      json.dump(metadata, metadata_file, indent=4)
  print("Writing metadata.json done!")

def determine_tile_format(cursor):
  """Determine tile format based on metadata."""
  cursor.execute("SELECT value FROM metadata WHERE name='format'")
  tile_format = cursor.fetchone()[0]
  if tile_format:
      if tile_format== 'png' or tile_format == 'webp':
          return 'png'
      elif tile_format == 'jpg':
          return 'jpg'
      elif tile_format == 'pbf':
          return 'pbf'
  return ''

def get_max_zoom(cursor):
    cursor.execute('SELECT MAX(zoom_level) FROM tiles')
    max_zoom = cursor.fetchone()[0]
    return max_zoom

def convert_mbtiles_to_folder(input_mbtiles, output_folder, flipy=0, min_zoom=0, max_zoom=None):
    connection = sqlite3.connect(input_mbtiles)
    cursor = connection.cursor()
    
    safe_makedir(output_folder)
    tile_format = determine_tile_format(cursor)
    
    mbtiles_max_zoom = get_max_zoom(cursor)
    if max_zoom is None or max_zoom > mbtiles_max_zoom:
        max_zoom = mbtiles_max_zoom

   
    metadata = extract_metadata(cursor)
    write_metadata_to_json(metadata, output_folder)
    
    cursor.execute('SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles WHERE zoom_level BETWEEN ? AND ? ORDER BY zoom_level', (min_zoom, max_zoom))
    tiles = cursor.fetchall()

    for zoom, col, row, tile_data in tqdm(tiles, unit = ' tiles ', desc='Processing tiles'):
        # Flip the Y coordinate if flipy is True
        y = flip_y(zoom, row) if flipy else row

        # Construct the directory path
        tile_dir = os.path.join(output_folder, str(zoom), str(col))

        # Ensure the directory exists
        safe_makedir(tile_dir)

        # Construct the file path
        tile_path = os.path.join(tile_dir, f'{y}.{tile_format}')

        # Write the tile data to the file
        with open(tile_path, 'wb') as tile_file:
            tile_file.write(tile_data)

    print('Converting mbtiles to folder done!')
    connection.close()

def main():
    parser = argparse.ArgumentParser(description='Convert MBTiles file to folder')
    parser.add_argument('-i', required=True, help='Input MBTiles file name')
    parser.add_argument('-o', help='Output folder name (optional)')
    parser.add_argument('-flipy', help='Use TMS (flip y) format: 1 or 0', type=int, default=0)
    parser.add_argument('-minzoom', help='Minimum zoom level to export', type=int, default=0)
    parser.add_argument('-maxzoom', help='Maximum zoom level to export', type=int, default=None)

    args = parser.parse_args()

    if not os.path.exists(args.i):
        print('MBTiles file does not exist! Please recheck and input a correct file path.')
        exit()
    
    input_filename_abspath = os.path.abspath(args.i)
    output_folder_abspath = os.path.abspath(args.o) if args.o else os.path.join(os.path.dirname(args.i), os.path.splitext(os.path.basename(args.i))[0])
    
    print(f'Converting {input_filename_abspath} to {output_folder_abspath} folder.')
    convert_mbtiles_to_folder(args.i, output_folder_abspath, args.flipy, args.minzoom, args.maxzoom)

if __name__ == "__main__":
    main()
