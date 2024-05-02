# MBTiles Utilities

## Installation: 
- Using pip install (Windows/ Linux):
    ``` bash 
    pip install mbtiles-util
    ```
- Show information of installed mbtiles-util: 
    ``` bash 
    pip show mbtiles-util
    ```
- Install the latest vertion of mbtiles-util:
    ``` bash 
    pip install mbtiles-util --upgrade
    ```
    
- Visit mbtiles-util on [PyPI](https://pypi.org/project/mbtiles-util/)

## Usage:
### mbtilesinfo:
- Display MBTiles metadata info:  
    ``` bash 
    > mbtilesinfo <file_path>
    ```
  Ex: `> mbtilesinfo tiles.mbtiles`
### mbtiles2folder: 
- Convert MBTiles file to folder:  
    ``` bash 
    > mbtiles2folder -i <file_path> -o [output_folder (optional)] -tms [TMS scheme (optional 0 or 1, default is 0)]
    ```
  Ex: `> mbtiles2folder -i tiles.mbtiles -o tiles_folder -tms 0`
    
### folder2s3: 
- Uplpad a tiles folder to Amazon S3 Bucket:  
    ``` bash 
    > folder2s3 <input_folder>   
    ```
  Ex: `> folder2s3 tiles_folder`
 
  Input S3 parameters:

  ```bash
    > S3 Bucket name: <Your S3 Bucket name (required)>
    > S3 Prefix: [Your S3 prefix (Optional. Press Enter to upload to the bucket root folder)]
    > AWS Access Key ID: <Your_Access_Key_ID (required)>
    > AWS Secret Access Key: <Your_Secrect_Access_Key (required)>
    > AWS Region: <AWS region (Optional. Press Enter to choose default region)>
  ```