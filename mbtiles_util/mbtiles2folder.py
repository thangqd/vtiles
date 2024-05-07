import os, math
import sqlite3
import json
import argparse
from tqdm import tqdm

def flip_y(zoom, y):
  return (2**zoom-1) - y

def safe_makedir(d):
  if os.path.exists(d):
    return
  os.makedirs(d)

def set_dir(d):
  safe_makedir(d)
  os.chdir(d)

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
  tile_format = cursor.fetchone()
  if tile_format:
      if tile_format[0] == 'png' or tile_format[0] == 'webp':
          return 'png'
      elif tile_format[0] == 'jpg':
          return 'jpg'
      elif tile_format[0] == 'pbf':
          return 'pbf'
  return ''

def count_total_tiles(cursor):
  """Count total number of tiles."""
  cursor.execute('SELECT COUNT(*) FROM tiles')
  return cursor.fetchone()[0]

def convert_mbtiles_to_folder(input_filename, output_folder, tms=0):
  """Convert MBTiles file to folder."""
  connection = sqlite3.connect(input_filename)
  cursor = connection.cursor()  
  os.mkdir("%s" % output_folder)

  tile_format = determine_tile_format(cursor)
  total_tiles = count_total_tiles(cursor)
  base_path = output_folder
  
  if not os.path.isdir(base_path):
    os.makedirs(base_path)

  metadata = extract_metadata(cursor)
  write_metadata_to_json(metadata, output_folder)
 
  # os.chdir(output_folder)
  cursor.execute('SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles order by zoom_level')
  t = cursor.fetchone()
  with tqdm(total=total_tiles, desc="Converting mbtiles to folder", unit="tile") as pbar:  
    while t:
      z = t[0]
      x = t[1]
      y = t[2]
      if tms == 1:
        y = flip_y(z,y)
        tile_dir = os.path.join(base_path, str(z), str(x))
      else:
        tile_dir = os.path.join(base_path, str(z), str(x))
      if not os.path.isdir(tile_dir):
        os.makedirs(tile_dir)
      tile = os.path.join(tile_dir,'%s.%s' % (y, tile_format))

      f = open(tile, 'wb')
      f.write(t[3])
      f.close()
      t = cursor.fetchone()
      pbar.update(1)

    # for row in cursor:
    #   z = row[0]
    #   x = row[1]
    #   tile_data = row[3]
    #   set_dir(str(z))
    #   set_dir(str(x))
    #   y = row[2]
    #   if tms == 1:
    #     y = flip_y(z, y)
    #   output_file = open(str(y) + tile_format, 'wb')
    #   output_file.write(tile_data)
    #   output_file.close()
    #   os.chdir('..')
    #   os.chdir('..')
    # pbar.update(1)

  print('Converting mbtiles to folder done!')
  connection.close()

def main():
  parser = argparse.ArgumentParser(description='Convert MBTiles file to folder')
  parser.add_argument('-i', help='Input MBTiles file name')
  parser.add_argument('-o', help='Output folder name (optional)', default=None)
  parser.add_argument('-tms', help='Use TMS (flip y) format: 1 or 0', type=int, default=0)

  args = parser.parse_args()

  if not args.i:
    print('Please provide the mbtiles input filename.')
    exit()
  
  if not os.path.exists(args.i):
    print('MBTiles file does not exist!. Please recheck and input a correct file path.')
    exit()
  
  input_filename_abspath =  os.path.abspath(args.i)
  if not args.o:
    if args.i:
      output_folder_name = os.path.splitext(os.path.basename(args.i))[0]  # Get file name without extension
      output_folder_path = os.path.join(os.path.dirname(args.i), output_folder_name)
      args.o = output_folder_path
      output_folder_abspath  = os.path.abspath(output_folder_path)      
      print(f'Output folder not provided. Converting {input_filename_abspath} to {output_folder_abspath} folder.')
  else:     
     output_folder_abspath = os.path.abspath(args.o)
     print(f'Converting {input_filename_abspath} to {output_folder_abspath} folder')
  
  convert_mbtiles_to_folder(args.i, args.o, args.tms)

if __name__ == "__main__":
    main()
