
import os
import sqlite3, json
import argparse
from tqdm import tqdm

######################################
def safeMakeDir(d):
  if os.path.exists(d):
    return
  os.makedirs(d)

def setDir(d):
  safeMakeDir(d)
  os.chdir(d)

######################################
def main():
  parser = argparse.ArgumentParser(description='Convert MBTiles file to folder')

  # Add your command-line arguments/options here
  parser.add_argument('-i', help='Input MBTiles file name')
  parser.add_argument('-o', help='Output folder name')

  # Parse the command-line arguments
  args = parser.parse_args()
  # if not len(sys.argv) == 3:
  #   print ('Please provide  the mbtiles input filename and output folder')
  #   exit()

  if not args.i :
    print ('Please provide the mbtiles input filename.')
    exit()
  if not os.path.exists(args.i):
    print ('MBTiles file does not exist!. Please recheck and input a correct file path.')
    exit()
  if not args.o:
    print ('Please provide the output folder name.')
    exit()

  # Process input
  # input_filename = sys.argv[1]
  input_filename = args.i
  # dirname = input_filename[0:input_filename.index('.')]
  # dirname = sys.argv[2]
  dirname = args.o

  # This will fail if there is already a directory.
  os.makedirs(dirname)

  # Database connection boilerplate
  connection = sqlite3.connect(input_filename)
  cursor = connection.cursor()

  cursor.execute("SELECT name, value FROM metadata")
  metadata_rows = cursor.fetchall()

  # Extract metadata
  metadata = {}
  for name, value in metadata_rows:
      metadata[name] = value

  # Write metadata to JSON file
  metadata_json_path = os.path.join(dirname, "metadata.json")
  with open(metadata_json_path, "w") as metadata_file:
      json.dump(metadata, metadata_file, indent=4)
  print ("Writing metadata.json done!")

  # Read format type from metadata
  cursor.execute("SELECT value FROM metadata WHERE name='format'")
  tile_format = cursor.fetchone()

  if tile_format:
      if tile_format[0] == 'png' or tile_format[0] == 'webp':
          out_format = '.png'
      elif tile_format[0] == 'jpg':
          out_format = '.jpg'
      elif tile_format[0] == 'pbf':
          out_format = '.pbf'
  else:
      out_format = ''

  cursor.execute('SELECT COUNT(*) FROM tiles')
  total_tiles = cursor.fetchone()[0]

  print ('Start converting "%s" into tiles folder "%s"' % (input_filename, dirname))

  os.chdir(dirname)
  # select all info in tiles view
  cursor.execute('SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles order by zoom_level')
  with tqdm(total=total_tiles, desc="Progress", unit="tile") as pbar:
    for row in cursor:
      setDir(str(row[0]))
      setDir(str(row[1]))
      # y = (2^row[0] - 1) - row[2]
      output_file = open(str(row[2]) + out_format, 'wb')
      # output_file = open(str(y) + out_format, 'wb')
      output_file.write(row[3])
      output_file.close()
      os.chdir('..')
      os.chdir('..')
      pbar.update(1)
  
  print ('Converting mbtiles to folder done!')
  connection.close()
  
if __name__ == "__main__":
    main()
