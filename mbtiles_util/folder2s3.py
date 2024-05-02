import os, sys
from tqdm import tqdm
import boto3

def folder2s3(input_folder, bucket_name='', s3_prefix='', aws_access_key_id=None, aws_secret_access_key=None,aws_region=None):
  session = boto3.Session(
      region_name=aws_region,
      aws_access_key_id=aws_access_key_id,
      aws_secret_access_key=aws_secret_access_key,
  )
  try:
    # Attempt to create an S3 client
    print (f'Create a connection to S3')
    s3 = session.client('s3')
  except Exception as e:
    print("Failed to create S3 client:", e)
    return  # Exit function if S3 client creation fails
      
  try:
    print (f'Uploading folder {input_folder} to S3 bucket: {bucket_name}. Press Crtl+C to cancel')
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
  except Exception as e:
    print("Error uploading folder to S3:", e)
    return
              
def main():
  if len(sys.argv) != 2:
    print("Please provide the input folder name.")
    return
 
  input_folder= sys.argv[1]
  if not input_folder:
    print('Please provide the input folder name.')
    exit()
  if not os.path.exists(input_folder) or not os.path.isdir(input_folder):
    print('Input folder does not exist or invalid!. Please recheck and input a correct one.')
    exit()

  input_folder_abspath =  os.path.abspath(input_folder)

  print('### Input S3 parmeters:')
  s3_bucket_name = input('S3 Bucket name: ')
  while not s3_bucket_name:  # Keep prompting until the user provides a non-empty value
    print('S3 Bucket name is required.')
    s3_bucket_name = input('S3 Bucket name: ')
  
  s3_prefix = input(f'S3 prefix (Press Enter to upload to the bucket {s3_bucket_name} root folder): ')
  if not s3_prefix:  # If the user presses Enter without typing anything
    s3_prefix = ''  # Assign a default value, e.g., None
  
  aws_access_key_id = input('AWS Access Key ID: ')
  while not aws_access_key_id:  # Keep prompting until the user provides a non-empty value
    aws_access_key_id = input('AWS Access Key ID is required. Please input AWS Access Key ID: ')

  aws_secret_access_key = input('AWS Secret Access Key: ')
  while not aws_secret_access_key:  # Keep prompting until the user provides a non-empty value
    aws_secret_access_key = input('AWS Secret Access Key is required. Please input AWS Secret Access Key: ')

  aws_region = input(f'AWS region (Press Enter to choose default region): ')
  if not aws_region:  # If the user presses Enter without typing anything
    aws_region =None  # Assign a default value, e.g., None

  folder2s3(input_folder_abspath, s3_bucket_name, s3_prefix, aws_access_key_id, aws_secret_access_key,aws_region)

if __name__ == "__main__":
  main()