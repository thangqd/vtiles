import os
import sys
import boto3
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
s3 = boto3.client('s3')

def upload_file(bucket_name, local_file_path, s3_key, content_type=None, content_encoding=None):
    try:
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        if content_encoding:
            extra_args['ContentEncoding'] = content_encoding
        s3.upload_file(local_file_path, bucket_name, s3_key, ExtraArgs=extra_args)
        return True
    except Exception as e:
        logging.error(f"Error uploading {local_file_path} to {s3_key}: {e}")
        return False

def upload_files(bucket_name, input_folder, s3_prefix='', content_type=None, content_encoding=None):
    total_files = sum(len(files) for _, _, files in os.walk(input_folder))
    num_cores = multiprocessing.cpu_count()

    with tqdm(total=total_files, desc="Uploading", unit="files ") as pbar:
        with ThreadPoolExecutor(max_workers=num_cores*2) as executor:
            futures = []
            for root, _, files in os.walk(input_folder):
                for file in files:
                    local_file_path = os.path.join(root, file)
                    s3_key = os.path.relpath(local_file_path, input_folder)
                    s3_key = os.path.join(s3_prefix, s3_key).replace('\\', '/')  # for Windows compatibility
                    future = executor.submit(upload_file, bucket_name, local_file_path, s3_key, content_type, content_encoding)
                    future.add_done_callback(lambda p: pbar.update())
                    futures.append(future)
            # Wait for all uploads to complete
            for future in futures:
                future.result()

def folder2s3(input_folder, format='', bucket_name='', s3_prefix='', aws_access_key_id=None, aws_secret_access_key=None, aws_region=None):
    session = boto3.Session(
        region_name=aws_region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    try:
        logging.info('Creating a connection to S3')
        global s3
        s3 = session.client('s3')
    except Exception as e:
        logging.error(f"Failed to create S3 client: {e}")
        return

    try:
        logging.info(f'Uploading folder {input_folder} to S3 bucket: {bucket_name}.Press Ctrl+C to cancel')
        if format == 'pbf' or format == 'mvt' :
            upload_files(bucket_name, input_folder, s3_prefix, 'application/x-protobuf', 'gzip')
        else:
            upload_files(bucket_name, input_folder, s3_prefix)
        logging.info('Uploading folder to S3 done!')
    except Exception as e:
        logging.error(f"Error uploading folder to S3: {e}")
        return

def main():
    parser = argparse.ArgumentParser(description='Upload a tiles folder to S3.')
    parser.add_argument('input', type=str, help='The tiles folder to upload.')
    parser.add_argument('-format', type=str, required=True, choices=['pbf', 'mvt', 'png', 'jpg', 'jpeg', 'webp'], help='format of the files to upload.')
    args = parser.parse_args()

    input_folder = args.input
    format = args.format

    if not os.path.exists(input_folder) or not os.path.isdir(input_folder):
        logging.error('Input folder does not exist or is invalid. Please recheck and provide a correct one.')
        exit()

    input_folder_abspath = os.path.abspath(input_folder)

    logging.info('### Input S3 parameters:')
    s3_bucket_name = input('S3 Bucket name: ')
    while not s3_bucket_name:
        logging.error('S3 Bucket name is required.')
        s3_bucket_name = input('S3 Bucket name: ')

    s3_prefix = input(f'S3 prefix (Press Enter to upload to the bucket {s3_bucket_name} root folder): ')
    if not s3_prefix:
        s3_prefix = ''

    aws_access_key_id = input('AWS Access Key ID: ')
    while not aws_access_key_id:
        aws_access_key_id = input('AWS Access Key ID is required. Please input AWS Access Key ID: ')

    aws_secret_access_key = input('AWS Secret Access Key: ')
    while not aws_secret_access_key:
        aws_secret_access_key = input('AWS Secret Access Key is required. Please input AWS Secret Access Key: ')

    aws_region = input('AWS region (Press Enter to choose default region): ')
    if not aws_region:
        aws_region = None

    folder2s3(input_folder_abspath, format, s3_bucket_name, s3_prefix, aws_access_key_id, aws_secret_access_key, aws_region)

if __name__ == "__main__":
    main()
