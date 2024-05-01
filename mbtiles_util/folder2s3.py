import os
import sqlite3
import json
import argparse
from tqdm import tqdm
import boto3

def folder2s3(input_folder, bucket_name='', s3_prefix='', region_name=None, aws_access_key_id=None, aws_secret_access_key=None):
  session = boto3.Session(
      region_name=region_name,
      aws_access_key_id=aws_access_key_id,
      aws_secret_access_key=aws_secret_access_key,
  )
  s3 = session.client('s3')
  total_files = sum(len(files) for _, _, files in os.walk(input_folder))
  with tqdm(total=total_files, desc="Uploading", unit="file") as pbar:
    for root, dirs, files in os.walk(input_folder):
      for file in files:
        local_file_path = os.path.join(root, file)
        s3_key = os.path.relpath(local_file_path, input_folder)
        s3_key = os.path.join(s3_prefix, s3_key).replace('\\', '/')  # for Windows compatibility
        s3.upload_file(local_file_path, bucket_name, s3_key)
        pbar.update(1)
  print('Uploading folder to S3 done!')

def main():
  parser = argparse.ArgumentParser(description='Upload a tiles folder to S3')
  parser.add_argument('-i', help='Input folder name', required=True)
  parser.add_argument('-b', help='S3 bucket name', required=True)
  parser.add_argument('-p', help='S3 prefix (optional)', default='')
  parser.add_argument('-r', help='AWS region (optional)', default=None)
  args = parser.parse_args()

  if not args.i:
    print('Please provide the input folder name.')
    exit()
  if not os.path.exists(args.i):
    print('Input folder does not exist!. Please recheck and input a correct one.')
    exit()
  if not args.b:
    print('Please provide the S3 bucket name.')
    exit()
  input_folder_abspath =  os.path.abspath(args.i)

  aws_access_key_id = input('Enter AWS Access Key ID: ')
  aws_secret_access_key = input('Enter AWS Secret Access Key: ')
  print (f'Uploading folder {input_folder_abspath} to S3 with bucket name: {args.b}')
  folder2s3(args.i, args.b, args.p, args.r, aws_access_key_id, aws_secret_access_key)

if __name__ == "__main__":
  main()