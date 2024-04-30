import os
import sqlite3
import json
import argparse
from tqdm import tqdm
import boto3

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
          return '.png'
      elif tile_format[0] == 'jpg':
          return '.jpg'
      elif tile_format[0] == 'pbf':
          return '.pbf'
  return ''

def count_total_tiles(cursor):
  """Count total number of tiles."""
  cursor.execute('SELECT COUNT(*) FROM tiles')
  return cursor.fetchone()[0]

def mbtiles2folder(input_filename, output_folder):
  """Convert MBTiles file to folder."""
  os.makedirs(output_folder)
  connection = sqlite3.connect(input_filename)
  cursor = connection.cursor()  
  tile_format = determine_tile_format(cursor)
  total_tiles = count_total_tiles(cursor)
  metadata = extract_metadata(cursor)
  write_metadata_to_json(metadata, output_folder)
 
  os.chdir(output_folder)
  cursor.execute('SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles order by zoom_level')
  with tqdm(total=total_tiles, desc="Progress", unit="tile") as pbar:      
    for row in cursor:
      set_dir(str(row[0]))
      set_dir(str(row[1]))
      output_file = open(str(row[2]) + tile_format, 'wb')
      output_file.write(row[3])
      output_file.close()
      os.chdir('..')
      os.chdir('..')
      pbar.update(1)
  print('Converting mbtiles to folder done!')
  connection.close()

def folder_to_s3(input_filename, output_folder, bucket_name, s3_prefix='', region=None, aws_access_key_id=None, aws_secret_access_key=None):
  mbtiles2folder(input_filename, output_folder);
  session = boto3.Session(
      region_name=region,
      aws_access_key_id=aws_access_key_id,
      aws_secret_access_key=aws_secret_access_key,
  )
  s3 = session.client('s3')
  total_files = sum(len(files) for _, _, files in os.walk(output_folder))
  with tqdm(total=total_files, desc="Uploading", unit="file") as pbar:
    for root, dirs, files in os.walk(output_folder):
      for file in files:
          local_file_path = os.path.join(root, file)
          s3_key = os.path.relpath(local_file_path, output_folder)
          s3_key = os.path.join(s3_prefix, s3_key).replace('\\', '/')  # for Windows compatibility
          s3.upload_file(local_file_path, bucket_name, s3_key)
          pbar.update(1)
  print('Uploading folder to S3 done!')

def main():
  parser = argparse.ArgumentParser(description='Upload a folder to S3')
  parser.add_argument('-i', help='Input folder name', required=True)
  parser.add_argument('-b', help='S3 bucket name', required=True)
  parser.add_argument('-p', help='S3 prefix (optional)', default='')
  parser.add_argument('-r', help='AWS region (optional)', default='us-east-1')
  args = parser.parse_args()

  args = parser.parse_args()

  if not args.i:
      print('Please provide the input folder name.')
      exit()
  if not os.path.exists(args.i):
      print('Input folder does not exist!. Please recheck and input a correct folder path.')
      exit()
  if not args.b:
      print('Please provide the S3 bucket name.')
      exit()

  aws_access_key_id = input('Enter AWS Access Key ID: ')
  aws_secret_access_key = input('Enter AWS Secret Access Key: ')
  folder_to_s3(args.i, args.b, args.p, aws_access_key_id, aws_secret_access_key)

if __name__ == "__main__":
  main()

