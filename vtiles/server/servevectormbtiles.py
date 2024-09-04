import os
import json
import sqlite3
import zlib  # For gzip compression
import logging
from wsgiref.util import shift_path_info

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Default settings or import from settings.py
try:
    from settings import MBTILES_ABSPATH, MBTILES_TILE_EXT, MBTILES_ZOOM_OFFSET, MBTILES_HOST, MBTILES_PORT, MBTILES_SERVE, USE_OSGEO_TMS_TILE_ADDRESSING
except ImportError:
    logger.warning("settings.py not set, may not be able to run via a web server (apache, nginx, etc)!")
    MBTILES_ABSPATH = None
    MBTILES_TILE_EXT = '.pbf'
    MBTILES_ZOOM_OFFSET = 0
    MBTILES_HOST = '0.0.0.0'
    MBTILES_PORT = 8005
    MBTILES_SERVE = True
    USE_OSGEO_TMS_TILE_ADDRESSING = True

# Supported image extensions for vector tiles
SUPPORTED_IMAGE_EXTENSIONS = ('.pbf',)

class MBTilesFileNotFound(Exception):
    pass

class InvalidImageExtension(Exception):
    pass

class MBTilesApplication:
    """
    Serves vector tiles within the given .mbtiles (sqlite3) file defined in settings.MBTILES_ABSPATH
    """
    def __init__(self, mbtiles_filepath, tile_image_ext='.pbf', zoom_offset=0):
        if mbtiles_filepath is None or not os.path.exists(mbtiles_filepath):
            raise MBTilesFileNotFound(mbtiles_filepath)

        if tile_image_ext not in SUPPORTED_IMAGE_EXTENSIONS:
            raise InvalidImageExtension(f"{tile_image_ext} not in {SUPPORTED_IMAGE_EXTENSIONS}!")

        self.mbtiles_db = sqlite3.connect(
            f"file:{mbtiles_filepath}?mode=ro",
            check_same_thread=False, uri=True)
        self.tile_image_ext = tile_image_ext
        self.tile_content_type = 'application/x-protobuf'
        self.tile_content_encoding = 'gzip'
        self.zoom_offset = zoom_offset
        self.maxzoom = None
        self.minzoom = None

        self._populate_supported_zoom_levels()

    def _populate_supported_zoom_levels(self):
        """
        Query the metadata table and obtain max/min zoom levels,
        setting to self.minzoom, self.maxzoom as integers
        """
        query = 'SELECT name, value FROM metadata WHERE name="minzoom" OR name="maxzoom";'
        for name, value in self.mbtiles_db.execute(query):
            setattr(self, name.lower(), max(int(value) - self.zoom_offset, 0))

    def __call__(self, environ, start_response):
        if environ['REQUEST_METHOD'] == 'GET':
            uri_field_count = len(environ['PATH_INFO'].split('/'))
            base_uri = shift_path_info(environ)

            if base_uri == 'metadata':
                query = 'SELECT * FROM metadata;'
                try:
                    metadata_results = self.mbtiles_db.execute(query).fetchall()
                    status = '200 OK'
                    response_headers = [('Content-type', 'application/json')]
                    start_response(status, response_headers)
                    json_result = json.dumps(metadata_results, ensure_ascii=False)
                    return [json_result.encode("utf8"), ]
                except sqlite3.Error as e:
                    logger.error(f"Database error: {e}")
                    status = '500 Internal Server Error'
                    response_headers = [('Content-type', 'text/plain; charset=utf-8')]
                    start_response(status, response_headers)
                    return [b'Internal Server Error'].encode('utf8')

            elif uri_field_count >= 3:  # Expect: zoom, x & y
                try:
                    zoom = int(base_uri)
                    if None not in (self.minzoom, self.maxzoom) and not (self.minzoom <= zoom <= self.maxzoom):
                        status = "404 Not Found"
                        response_headers = [('Content-type', 'text/plain; charset=utf-8')]
                        start_response(status, response_headers)
                        return [f'Requested zoomlevel({zoom}) Not Available! Valid range minzoom({self.minzoom}) maxzoom({self.maxzoom}) PATH_INFO: {environ["PATH_INFO"]}'.encode('utf8')]

                    zoom += self.zoom_offset
                    x = int(shift_path_info(environ))
                    y, ext = shift_path_info(environ).split('.')
                    y = int(y)
                except ValueError as e:
                    status = "400 Bad Request"
                    response_headers = [('Content-type', 'text/plain; charset=utf-8')]
                    start_response(status, response_headers)
                    return [f'Unable to parse PATH_INFO({environ["PATH_INFO"]}), expecting "z/x/y.pbf"'.encode('utf8'), ' '.join(i for i in e.args).encode('utf8')]

                query = 'SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?;'
                ymax = 1 << zoom
                y = ymax - y - 1
                values = (zoom, x, y)
                try:
                    tile_results = self.mbtiles_db.execute(query, values).fetchone()
                    if tile_results:
                        tile_data = tile_results[0]
                        status = '200 OK'
                        response_headers = [('Content-type', self.tile_content_type),
                                             ('Content-Encoding', self.tile_content_encoding)]
                        start_response(status, response_headers)
                        return [tile_data]
                    else:
                        status = '404 NOT FOUND'
                        response_headers = [('Content-type', 'text/plain; charset=utf-8')]
                        start_response(status, response_headers)
                        return [f'No data found for request location: {environ["PATH_INFO"]}'.encode('utf8')]
                except sqlite3.Error as e:
                    logger.error(f"Database error: {e}")
                    status = '500 Internal Server Error'
                    response_headers = [('Content-type', 'text/plain; charset=utf-8')]
                    start_response(status, response_headers)
                    return [b'Internal Server Error'].encode('utf8')

        status = "400 Bad Request"
        response_headers = [('Content-type', 'text/plain; charset=utf-8')]
        start_response(status, response_headers)
        return [b'request URI not in expected: ("metadata", "/z/x/y.pbf")']

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve",
                        default=MBTILES_SERVE,
                        action='store_true',
                        help="Start test server [DEFAULT={}]\n(Defaults to environment variable, 'MBTILES_SERVE')".format(MBTILES_SERVE))
    parser.add_argument('-p', '--port',
                        default=MBTILES_PORT,
                        type=int,
                        help="Test server port [DEFAULT={}]\n(Defaults to environment variable, 'MBTILES_PORT')".format(MBTILES_PORT))
    parser.add_argument('-a', '--address',
                        default=MBTILES_HOST,
                        help="Test address to serve on [DEFAULT=\"{}\"]\n(Defaults to environment variable, 'MBTILES_HOST')".format(MBTILES_HOST))
    parser.add_argument('-f', '--filepath',
                        default=MBTILES_ABSPATH,
                        help="mbtiles filepath [DEFAULT={}]\n(Defaults to environment variable, 'MBTILES_ABSPATH')".format(MBTILES_ABSPATH))
    parser.add_argument('-e', '--ext',
                        default=MBTILES_TILE_EXT,
                        help="mbtiles image file extension [DEFAULT={}]\n(Defaults to environment variable, 'MBTILES_TILE_EXT')".format(MBTILES_TILE_EXT))
    parser.add_argument('-z', '--zoom-offset',
                        default=MBTILES_ZOOM_OFFSET,
                        type=int,
                        help="mbtiles zoom offset [DEFAULT={}]\n(Defaults to environment variable, 'MBTILES_ZOOM_OFFSET')".format(MBTILES_ZOOM_OFFSET))
    args = parser.parse_args()
    args.filepath = os.path.abspath(args.filepath)

    if args.serve:
        # Configure logging
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        logger.addHandler(console)
        logger.setLevel(logging.DEBUG)

        logger.info("FILEPATH: {}".format(args.filepath))
        logger.info("TILE EXT: {}".format(args.ext))
        logger.info("ADDRESS : {}".format(args.address))
        logger.info("PORT    : {}".format(args.port))

        # Start WSGI server
        from wsgiref.simple_server import make_server, WSGIServer
        from socketserver import ThreadingMixIn

        class ThreadingWSGIServer(ThreadingMixIn, WSGIServer):
            pass

        httpd = make_server(args.address, args.port, MBTilesApplication(args.filepath, args.ext, args.zoom_offset), ThreadingWSGIServer)
        logger.info("Serving on {}:{}".format(args.address, args.port))
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Stopping server...")
            httpd.server_close()
    else:
        logger.info("Webserver NOT started.")

if __name__ == '__main__':
    main()
