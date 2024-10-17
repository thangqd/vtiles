import hashlib
import logging
import os
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from urllib.parse import urlparse
import math
import boto3
import requests
import sqlite3
from vtiles.utils.mapbox_vector_tile import decode
import zlib, gzip
import vtiles.utils.mercantile as mercantile
import binascii
CHUNK_SIZE = 1024

def num2deg(xtile, ytile, zoom):
		n = 2.0 ** zoom
		lon_deg = xtile / n * 360.0 - 180.0
		lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
		lat_deg = math.degrees(lat_rad)
		return (lat_deg, lon_deg)

def flip_y(zoom, y):
  return (2**zoom-1) - y

def safe_makedir(d):
  if os.path.exists(d):
    return
  os.makedirs(d)

def set_dir(d):
  safe_makedir(d)
  os.chdir(d)

def fix_wkt(data):
    result = []
    
    for key in data:
        feature_collection = data[key]
        features = []
        
        for feature in feature_collection.get('features', []):
            geom = feature.get('geometry', {})
            geom_type = geom.get('type')
            coords = geom.get('coordinates')
            
            if geom_type is None or coords is None or (isinstance(coords, (list, dict)) and not coords):
                # Handle null or empty geometry
                wkt_geom = f'{geom_type or "GEOMETRY"} EMPTY'
                
            elif geom_type == 'Polygon':
                if not coords or not coords[0]:
                    wkt_geom = 'POLYGON EMPTY'
                else:
                    wkt_geom = 'POLYGON ((' + ', '.join([' '.join(map(str, pt)) for pt in coords[0]]) + '))'
                
            elif geom_type == 'LineString':
                if not coords:
                    wkt_geom = 'LINESTRING EMPTY'
                else:
                    wkt_geom = 'LINESTRING (' + ', '.join([' '.join(map(str, pt)) for pt in coords]) + ')'
                
            elif geom_type == 'MultiPolygon':
                if not coords:
                    wkt_geom = 'MULTIPOLYGON EMPTY'
                else:
                    polygons = []
                    for polygon in coords:
                        if not polygon:
                            polygons.append('EMPTY')
                        else:
                            polygons.append('((' + ', '.join([' '.join(map(str, pt)) for pt in polygon[0]]) + '))')
                    wkt_geom = 'MULTIPOLYGON (' + ', '.join(polygons) + ')'
                
            elif geom_type == 'MultiLineString':
                if not coords:
                    wkt_geom = 'MULTILINESTRING EMPTY'
                else:
                    lines = []
                    for line in coords:
                        if not line:
                            lines.append('EMPTY')
                        else:
                            lines.append('(' + ', '.join([' '.join(map(str, pt)) for pt in line]) + ')')
                    wkt_geom = 'MULTILINESTRING (' + ', '.join(lines) + ')'
                
            elif geom_type == 'Point':
                if not coords:
                    wkt_geom = 'POINT EMPTY'
                else:
                    wkt_geom = 'POINT (' + ' '.join(map(str, coords)) + ')'
                
            elif geom_type == 'MultiPoint':
                if not coords:
                    wkt_geom = 'MULTIPOINT EMPTY'
                else:
                    points = []
                    for point in coords:
                        points.append(' '.join(map(str, point)))
                    wkt_geom = 'MULTIPOINT (' + ', '.join(points) + ')'
                
            else:
                # Skip unsupported geometry types
                continue
            
            features.append({
                'geometry': wkt_geom,
                'properties': feature.get('properties', {})
            })
        
        result.append({
            'name': key,
            'features': features
        })
    
    return result


# Check if mbtiles is vector
def check_vector(mbtiles):   
    compression_type = None
    try:   
        conn = sqlite3.connect(mbtiles)
        cursor = conn.cursor()
        cursor.execute("SELECT tile_data FROM tiles LIMIT 1")
        tile_data = cursor.fetchone()[0]
                  
        if tile_data[:2] == b'\x1f\x8b':
            compression_type = 'GZIP'
            tile_data = gzip.decompress(tile_data)
        elif tile_data[:2] == b'\x78\x9c' or tile_data[:2] == b'\x78\x01' or tile_data[:2] == b'\x78\xda':
            compression_type = 'ZLIB'
            tile_data = zlib.decompress(tile_data)
        decode(tile_data)
        return True, compression_type
    except:
        return False, compression_type
    finally:
        cursor.close()
        conn.close()

def determine_tileformat(mbtiles):
    tile_format = ''  
    conn = sqlite3.connect(mbtiles)
    cursor = conn.cursor()    
    try:
        # Open database connection and cursor
        is_vector,_ = check_vector(mbtiles)
        if is_vector:
            tile_format = 'pbf'
        else: 
            # Get a tile's binary data from the tiles table
            cursor.execute("SELECT tile_data FROM tiles LIMIT 1;")
            tile_data = cursor.fetchone()[0]  # Access the first element of the tuple
            
            if tile_data:
                # Convert the binary data to a hex string for inspection
                hex_data = binascii.hexlify(tile_data[:12]).decode('utf-8')            
                # Check the format based on the hex data
                if hex_data.startswith('52494646') and '57454250' in hex_data:  # WebP
                    tile_format = 'webp'  # WebP format
                elif hex_data.startswith('89504e47'):
                    tile_format = 'png'  # PNG format
                elif hex_data.startswith('ffd8ff'):
                    tile_format = 'jpg'  # JPG format
                else:
                    tile_format='unknown' # Unknown format if none match
    except Exception as e:
        print (f"Error reading format from tile_data: {e}")
    
    finally:
        cursor.close()
        conn.close()

    return tile_format  # Return the determined tile_format

def decode_tile_data(tile_data):   
    try:
        if tile_data[:2] == b'\x1f\x8b':  # GZip compressed
            tile_data = gzip.decompress(tile_data)
        elif tile_data[:2] in (b'\x78\x9c', b'\x78\x01', b'\x78\xda'):  # Zlib compressed
            tile_data = zlib.decompress(tile_data)
        decoded_tile = decode(tile_data)    
    except Exception as e:
        print(f"Error decoding tile data: {e}")
        return None  # Handle failure gracefully
    return decoded_tile


def count_tiles(mbtiles):
    """Count the number of tiles in the MBTiles file."""
    num_tiles = None
    connection = sqlite3.connect(mbtiles)
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM tiles")
    num_tiles = cursor.fetchone()[0]   
    
    cursor.close()
    connection.close()    
    
    return num_tiles

def count_tiles_for_each_zoom(mbtiles):
    """Count the number of tiles for each zoom level in the tiles table."""
    conn = sqlite3.connect(mbtiles)
    cursor = conn.cursor()

    query = """
    SELECT zoom_level, COUNT(*) AS tile_count
    FROM tiles
    GROUP BY zoom_level
    ORDER BY zoom_level;
    """
    
    cursor.execute(query)
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results

def find_duplicates(mbtiles):
    """Find duplicate rows in the tiles table and calculate the total number of duplicates."""
    conn = sqlite3.connect(mbtiles)
    cursor = conn.cursor()

    query = """
    SELECT zoom_level, tile_column, tile_row, COUNT(*) AS count
    FROM tiles
    GROUP BY zoom_level, tile_column, tile_row
    HAVING COUNT(*) > 1
    ORDER BY count DESC
    """
    
    cursor.execute(query)
    duplicates = cursor.fetchall()

    # Calculate the total number of duplicate rows
    total_duplicates = sum(count - 1 for _, _, _, count in duplicates)

    conn.close()
    
    return duplicates, total_duplicates

def get_zoom_levels(mbtiles):
    conn = sqlite3.connect(mbtiles)
    cursor = conn.cursor()
    
    # Query to get min and max zoom levels
    cursor.execute('''
        SELECT MIN(zoom_level) AS min_zoom, MAX(zoom_level) AS max_zoom
        FROM tiles
    ''')
    
    result = cursor.fetchone()    

    cursor.close()
    conn.close()    
    min_zoom = result[0] if result else None
    max_zoom = result[1] if result else None  

    return min_zoom, max_zoom

def get_bounds_at_zoom(mbtiles, zoom_level):
    # Connect to the MBTiles SQLite database
    conn = sqlite3.connect(mbtiles)
    cursor = conn.cursor()

    # Query tiles at the specified zoom level
    cursor.execute("SELECT tile_column, tile_row FROM tiles WHERE zoom_level = ?", (zoom_level,))
    tiles = cursor.fetchall()

    # Calculate bounding boxes for each tile
    bounds = []
    for tile in tiles:
        x, y = tile
        flip_y = (1 << zoom_level) - 1 - y # TMS scheme
        # Calculate bounds for the given tile coordinates
        tile_bounds = mercantile.bounds(x,flip_y, zoom_level)
        bounds.append(tile_bounds)

    cursor.close()
    conn.close()
    return bounds

def compute_max_bound(bounds):
    # Initialize min and max coordinates with extreme values
    min_lat = min_lon = float('inf')
    max_lat = max_lon = float('-inf')

    for bound in bounds:
        # Unpack bounding box coordinates (west, south, east, north)
        west, south, east, north = bound

        # Update min and max values
        min_lon = min(min_lon, west)
        max_lon = max(max_lon, east)    
        min_lat = min(min_lat, south)
        max_lat = max(max_lat, north)
            
    center_lon = (min_lon + max_lon) / 2
    center_lat = (min_lat + max_lat) / 2

    # Return the overall bounding box
    return min_lon, min_lat, max_lon, max_lat,center_lon,center_lat

def get_bounds_center(mbtiles):   
    boundsString, centerString = None, None
    try:    
        _,max_zoom = get_zoom_levels(mbtiles)
        bounds_at_max_zoom = get_bounds_at_zoom(mbtiles, max_zoom)
        bounds = compute_max_bound(bounds_at_max_zoom)
        boundsString = ','.join(map(str, bounds[:4]))
        centerString = ','.join(map(str, bounds[4:]))+ f',{max_zoom}'     
        return boundsString, centerString
    except Exception as e:
        logging.error(f"Get bounds and center erros: {e}")        
        boundsString = '-180.000000,-85.051129,180.000000,85.051129'
        centerString = '0,0,0'
        return boundsString, centerString

def get_standard_tile_count(zoom_level):
    """Calculate the standard number of tiles for a given zoom level."""
    num_tiles_per_side = 2 ** zoom_level
    return num_tiles_per_side * num_tiles_per_side

def get_files(path):
    """Returns an iterable containing the full path of all files in the
    specified path.

    :param path: string
    :yields: string
    """
    if os.path.isdir(path):
        for (dirpath, dirnames, filenames) in os.walk(path):
            for filename in filenames:
                if not filename[0] == ".":
                    yield os.path.join(dirpath, filename)
    else:
        yield path


def make_sure_path_exists(path):
    """Make directories in path if they do not exist.

    Modified from http://stackoverflow.com/a/5032238/1377021

    :param path: string
    """
    try:
        os.makedirs(path)
    except:
        pass


def get_path_parts(path):
    """Splits a path into parent directories and file.

    :param path: string
    """
    return path.split(os.sep)


def download(url):
    """Downloads a file and returns a file pointer to a temporary file.

    :param url: string
    """
    parsed_url = urlparse(url)

    urlfile = parsed_url.path.split("/")[-1]
    _, extension = os.path.split(urlfile)

    fp = tempfile.NamedTemporaryFile("wb", suffix=extension, delete=False)

    download_cache = os.getenv("DOWNLOAD_CACHE")
    cache_path = None
    if download_cache is not None:
        cache_path = os.path.join(
            download_cache, hashlib.sha224(url.encode()).hexdigest()
        )
        if os.path.exists(cache_path):
            logging.info("Returning %s from local cache at %s" % (url, cache_path))
            fp.close()
            shutil.copy(cache_path, fp.name)
            return fp

    s3_cache_bucket = os.getenv("S3_CACHE_BUCKET")
    s3_cache_key = None
    if s3_cache_bucket is not None and s3_cache_bucket not in url:
        s3_cache_key = (
            os.getenv("S3_CACHE_PREFIX", "") + hashlib.sha224(url.encode()).hexdigest()
        )
        s3 = boto3.client("s3")
        try:
            s3.download_fileobj(s3_cache_bucket, s3_cache_key, fp)
            logging.info(
                "Found %s in s3 cache at s3://%s/%s"
                % (url, s3_cache_bucket, s3_cache_key)
            )
            fp.close()
            return fp
        except:
            pass

    if parsed_url.scheme == "http" or parsed_url.scheme == "https":
        res = requests.get(url, stream=True, verify=False)

        if not res.ok:
            raise IOError

        for chunk in res.iter_content(CHUNK_SIZE):
            fp.write(chunk)
    elif parsed_url.scheme == "ftp":
        download = urllib.request.urlopen(url)

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = download.read(block_sz)
            if not buffer:
                break

            file_size_dl += len(buffer)
            fp.write(buffer)

    fp.close()

    if cache_path:
        if not os.path.exists(download_cache):
            os.makedirs(download_cache)
        shutil.copy(fp.name, cache_path)

    if s3_cache_key:
        logging.info(
            "Putting %s to s3 cache at s3://%s/%s"
            % (url, s3_cache_bucket, s3_cache_key)
        )
        s3.upload_file(fp.name, Bucket=s3_cache_bucket, Key=s3_cache_key)

    return fp


class ZipCompatibleTarFile(tarfile.TarFile):
    """Wrapper around TarFile to make it more compatible with ZipFile"""

    def infolist(self):
        members = self.getmembers()
        for m in members:
            m.filename = m.name
        return members

    def namelist(self):
        return self.getnames()


ARCHIVE_FORMAT_ZIP = "zip"
ARCHIVE_FORMAT_TAR_GZ = "tar.gz"
ARCHIVE_FORMAT_TAR_BZ2 = "tar.bz2"


def get_compressed_file_wrapper(path):
    archive_format = None

    if path.endswith(".zip"):
        archive_format = ARCHIVE_FORMAT_ZIP
    elif path.endswith(".tar.gz") or path.endswith(".tgz"):
        archive_format = ARCHIVE_FORMAT_TAR_GZ
    elif path.endswith(".tar.bz2"):
        archive_format = ARCHIVE_FORMAT_TAR_BZ2
    else:
        try:
            with zipfile.ZipFile(path, "r") as f:
                archive_format = ARCHIVE_FORMAT_ZIP
        except:
            try:
                f = tarfile.TarFile.open(path, "r")
                f.close()
                archive_format = ARCHIVE_FORMAT_ZIP
            except:
                pass

    if archive_format is None:
        raise Exception("Unable to determine archive format")

    if archive_format == ARCHIVE_FORMAT_ZIP:
        return zipfile.ZipFile(path, "r")
    elif archive_format == ARCHIVE_FORMAT_TAR_GZ:
        return ZipCompatibleTarFile.open(path, "r:gz")
    elif archive_format == ARCHIVE_FORMAT_TAR_BZ2:
        return ZipCompatibleTarFile.open(path, "r:bz2")
