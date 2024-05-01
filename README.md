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
    
### folder2S3: 
- Uplpad folder to Amazon S3 Bucket:  
    ``` bash 
    > folder2s3 -i <input_folder> -b <bucket_name> -p [s3_prefix (optional)]  -r [region_name (optional)]    
    ```
  Ex: `> folder2s3 -i tiles_folder -b bucket_name`
 
  And then:

  ```> Enter AWS Access Key ID: Your_Access_Key_ID```

  ```> Enter AWS Secret Access Key: Your_Secrect_Access_Key```