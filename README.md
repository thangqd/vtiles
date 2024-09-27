# VTiles - Vector Tiles Utilities

## Installation: 
- Using pip install (Windows/ Linux):
  ``` bash 
  pip install vtiles
  ```
- Show information of installed vtiles: 
  ``` bash 
  pip show vtiles
  ```
- Install the latest vertion of vtiles:
  ``` bash 
  pip install vtiles --upgrade
  ```
    
- Visit vtiles on [PyPI](https://pypi.org/project/vtiles/)

## Usage:
### MBTILES Utilities:
#### mbtilesinfo
- Show MBTiles metadata info, support raster MBTiles and vector MBTiles
- **mbtilesinfo** can show information from metadata table, total number of tiles, and vector_layers list for vector mbtiles 
  ``` bash 
  > mbtilesinfo <file_path>
  ```

#### mbtilesinspect
- Inspect MBTiles in actual tiles data instead of reading from metadata: 
- **mbtilesinspect** can show minzoom, maxzoom, total number of tiles, tile compression type, number of tiles comparing to standard tiles number at each zoom level, and it can show the duplicated rows in terms of zoom_level, tile_column, and tile_row
  ``` bash 
  > mbtilesinspect <file_path>
  ```
Ex: `> mbtilesinspect tiles.mbtiles`

#### mbtilesdelduplicate
- Inspect MBTiles in actual tiles data instead of reading from metadata: 
- **mbtilesinspect** can show minzoom, maxzoom, total number of tiles, tile compression type, number of tiles comparing to standard tiles number at each zoom level, and it can show the duplicated rows in terms of zoom_level, tile_column, and tile_row
  ``` bash 
  > mbtilesinspect <file_path>
  ```
Ex: `> mbtilesinspect tiles.mbtiles`


#### mbtiles2folder
- Convert MBTiles file to folder: (support raster MBTiles (.png, .jpg, .webp) and vector MBTiles (.pbf)) 
  ``` bash 
  > mbtiles2folder -i <file_name.mbtiles> -o [output_folder (optional, current dir if not specified)] -flipy [TMS <--> XYZ tiling scheme (optional): 1 or 0, default is 0] -minzoom [optional, default is 0] -maxzoom [Maximum zoom level to export (optional, default is maxzoom from input MBTiles]
  ```
  Ex: `> mbtiles2folder -i tiles.mbtiles -o tiles_folder -flipy 0 -minzoom 0 -maxzoom 6`

#### url2folder
- Download tiles from a tile server to tiles folders: 
  ``` bash 
  > url2folder -url <URL> -o <output_folder> -minzoom <min zoom> -maxzoom <max zoom>
  ```
  Ex: `> url2folder -url -o tiles.mbtiles -minzoom 0 -maxzoom 1 `

#### folder2mbtiles
- Convert a tiles folder to MBTiles file: (support raster tile (.png, .jpg, .webp) and vector tile (.pbf))
  ``` bash 
  > folder2mbtiles -i <input_folder> -o [file_name.mbtiles (optional)] -flipy [TMS <--> XYZ tiling scheme (optional): 1 or 0, default is 0]
  ```
  Ex: `> folder2mbtiles -i tiles_folder -o tiles.mbtiles -flipy 0`
  
  Without -o parameter: file_name.mbtiles has the same name with <input_folder> name at the current directory 

#### mbtiles2geojson
- Convert MBTiles to GeoJSON.
  ``` bash 
  > mbtiles2geojson -i <input file> -o <Output GeoJSON> -minzoom <minzoom> -maxzoom <maxzoom> -flipy [TMS <--> XYZ tiling scheme (optional): 1 or 0, default is 0] -l [List of layer names to convert, all layers if not specified]
  ```
  Ex: `> mbtiles2geojson -i tiles.mbtils -o geojson.geojson -minzoom 0 - maxzoom 1 -flipy 0 -l water building`

#### geoson2mbtiles
- Convert geojson file to mbtiles (need tippecanoe to be installed)
  ``` bash 
  > geojson2mbtiles -i <input files> -z <maxzoom> -o <output> -t <tippecanoe path> --extra-args <drop-densest-as-needed or coalesce-densest-as-needed or extend-zooms-if-still-dropping>
  ```
  Ex: `> geojson2mbtiles -i state.geojson district.geojson -z9 -o state_district.mbtiles -t /usr/local/bin/ --extra-args coalesce-densest-as-needed` (on Linux)

#### folder2s3
- Uplpad a vector/ raster tiles folder to Amazon S3 Bucket:  
  ``` bash 
  > folder2s3 -i <input_folder> -format <'pbf', 'png', 'jpg', 'jpeg', 'webp', 'pbf', 'mvt'>
  ```
  Ex: `> folder2s3 -i vectortiles_folder -format pbf`
 
  Input S3 parameters:

  ```bash
  > S3 Bucket name: <Your S3 Bucket name (required)>
  > S3 Prefix: [Your S3 prefix (Optional. Press Enter to upload to the bucket root folder)]
  > AWS Access Key ID: <Your_Access_Key_ID (required)>
  > AWS Secret Access Key: <Your_Secrect_Access_Key (required)>
  > AWS Region: <AWS region (Optional. Press Enter to choose default region)>
  ```

#### mbtiles2s3
- Uplpad a MBTiles file to Amazon S3 Bucket: Need to install aws cli and run aws configure to input credentials first
  ``` bash 
  > mbtiles2s3 <input file> <s3 bucket> -p (to see the uploading progress)
  ```
  Ex: `> mbtiles2s3 tiles.mbtiles s3://mybucket -p`
- Install aws cli on Ubuntu:
  ``` bash 
  sudo apt update
  sudo apt install curl unzip -y
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  unzip awscliv2.zip
  sudo ./aws/install
  ```
  Verify aws cli installation:
  ``` bash 
  aws --version
  ```
- Configure aws cli:
  ``` bash 
  aws configure
  ```
  Input AWS Access Key ID and AWS Secret Access Key
  ``` bash 
  AWS Access Key ID [None]: AKIAxxxxxxxxxxxxxxxx
  AWS Secret Access Key [None]: wJalrxxxxxxxxxxxxxxxxxxxxxxxxxx
  Default region name [None]:
  Default output format [None]:
  ```
  Check aws configuration by listing your S3 buckets:
  ``` bash 
  aws s3 ls
  ```

#### mbtiles2pbf
- Extract a tile from MBTiles to PBF 
  ``` bash 
    > mbtiles2pbf -i <input file> -z <zoom level> -x <tile column> -y <tile row> -o <output file>
  ```
  Ex: `> mbtiles2pbf -i tiles.mbtils -z 2 -x 1 -y 2 -o pbf_212.pbf`

#### pbfinfo
- Show pbf metadata info
  ``` bash 
    > pbfinfo <input file>
  ```
  Ex: `> pbfinfo pbf_file.pbf`

#### pbf2geojson
- Convert tile data from a BBF file, MBTiles file, or URL to GeoJSON 
  ``` bash 
    > pbf2geojson -i <input pbf, MBTiles or URL> -o <output file> -z <tile zoom level> - x <tile column> -y <tile row>  -flipy [TMS <--> XYZ tiling scheme (optional): 1 or 0, default is 0] 
  ```
  Ex: `> pbf2geojson -i pbf_file.pbf -o geojson_file.geojson -z 2 -x 1 -y 2`

#### flipy
- Convert TMS <--> XYZ tiling scheme for a tiles folder
  ``` bash 
    > flipy -i <input folder> -o <output folder>
  ```
  Ex: `> flipy -i input_folder -o output_folder`

#### mbtiles2pmtiles
- Convert Convert MBTiles to PMTiles
  ``` bash 
    > flipy -i <input MBTiles> -o <output PMTiles> -z <max zoom level>
  ```
  Ex: `> mbtiles2pmtiles -i mbtiles_file.mbtiles -o pmtiles_file.pmtiles -z 6`

#### mbtilessplit
- Split an MBTiles file by selected layers
  ``` bash 
    > mbtilessplit -i <input file> -o <output file> -l <list of layer names to be splitted>
  ```
  Ex: `> mbtilessplit -i input_file.mbtiles -o splitted_file.mbtiles -l water`
      (mbtilessplit also save remaining mbtiles layers to {input file}_remained.mbtiles)

#### mbtilesmerge
- Merge multiple MBTiles files into a single MBTiles file
  ``` bash 
    > mbtilesmerge -i <input file list> -o <output file> -l <list of layer names to be splitted>
  ```
  Ex: `> mbtilesmerge -i file_1.mbtiles file_2.mbtiles -o merged.mbtiles`

#### mbtilescompress
- Compress MBTiles file with GZIP
  ``` bash 
    > mbtilescompress -i <input file> -o <output file>
  ```
  Ex: `> mbtilescompress -i mbtiles_file.mbtiles -o compressed.mbtiles`

#### mbtilesdecompress
- Decompress MBTiles file (either being compressed with GZIP or ZLIB)
  ``` bash 
    > mbtilesdecompress -i <input file> -o <output file>
  ```
  Ex: `> mbtilesdecompress -i mbtiles_file.mbtiles -o decompressed.mbtiles`

#### mbtilesfixmeta
- Create or update metadata for an existing MBTiles file.
  ``` bash 
    > mbtilesfixmeta <input file>
  ```
  Ex: `> mbtilesfixmeta mbtiles_file.mbtiles`

### MBTILES Server Utilities:
#### servefolder
- Serve a raster tiles or vector tiles for the current folder, so clients can access to the tiles server via, for ex. htttp://localhost/8000/tiles/{z}/{x}/{y}.pbf.
  ``` bash 
    > servefolder
  ```

#### servembtiles
- Serve raster tiles for the input MBTiles file, so clients can access to the tiles server via, for ex. htttp://localhost/8000/rastertiles/z/x/y.png.
  ``` bash 
    > servembtiles --serve -p <port> -f <input file>
  ```
#### servevectormbtiles
- Serve vector tiles for the input MBTiles file, so clients can access to the tiles server via, for ex. htttp://localhost/8000/vectortiles/z/x/y.pbf.
  ``` bash 
    > servevectormbtiles --serve -p <port> -f <input file>
  ```
#### servepostgis
- Serve MVT tiles from a PostgreSQL/PostGIS database, so clients can access to the tiles server via, for ex. htttp://localhost/8000/mvt/z/x/y.pbf.
  ``` bash 
    > servepostgis -config <YAML configuration file> 
  ```
#### servepmtiles
- Serve MVT tiles from a PostgreSQL/PostGIS database, so clients can access to the tiles server via, for ex. htttp://localhost/8000/pmtiles/z/x/y.pbf.
  ``` bash 
    > servepostgis -i <PMTiles file> -port <port number> -host <host IP, default is localhost>
  ```
### Other Utilities:
#### pmtilesinfo
- Show PMTiles metadata.
  ``` bash 
    > pmtilesinfo <mbtiles file> Z [zoom level] X [tile column] Y [tile row]
  ```
#### pmtiles2folder
- Convert PMTiles file to folder
    ``` bash 
    > pmtiles2folder -i <input file> -o <output_folder>
    ```
#### pmtiles2mbtiles
- Convert PMTiles file to MBTiles file
    ``` bash 
    > pmtiles2mbtiles -i <input PMTiles> -o <output MBTiles>
    ```