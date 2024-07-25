import hashlib
import logging
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from contextlib import closing
from urllib.parse import urlparse

import boto3
import click
import requests
import ujson

CHUNK_SIZE = 1024


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


def read_json(path):
    """Returns JSON dict from file.

    :param path: string
    :returns: dict
    """
    with open(path, "r") as jsonfile:
        return ujson.loads(jsonfile.read())


def write_json(path, data):
    with open(path, "w") as jsonfile:
        jsonfile.write(
            ujson.dumps(data, escape_forward_slashes=False, double_precision=5)
        )


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
