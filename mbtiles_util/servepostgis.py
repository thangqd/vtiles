#!/usr/bin/env python
"""
This is a simple vector tile server that returns a PBF tile for  /tiles/{z}/{x}/{y}.pbf  requests

Usage:
  postserve <tileset> [--serve=<url>] [--port=<port>] [--key] [--gzip [<gzlevel>]]
                      [--no-feature-ids] [--file=<sql-file>]
                      [--layer=<layer>]... [--exclude-layers]
                      [--pghost=<host>] [--pgport=<port>] [--dbname=<db>]
                      [--user=<user>] [--password=<password>]
                      [--test-geometry] [--verbose]
  postserve --help
  postserve --version

  <tileset>             Tileset definition yaml file

Options:
  -l --layer=<layer>    If set, limit tile generation to just this layer (could be multiple)
  -x --exclude-layers   If set, uses all layers except the ones listed with -l (-l is required)
  -s --serve=<url>      Return this URL as tileserver URL in metadata  [default: http://localhost:<port>]
  -p --port=<port>      Serve on this port  [default: 8090]
  --key                 If set, print md5 of the data to console (generated by Postgres)
  --gzip                If set, compress MVT with gzip, with optional level=0..9.
  --no-feature-ids      Disable feature ID generation, e.g. from osm_id.
                        Feature IDS are automatically disabled with PostGIS before v3
  -g --test-geometry    Validate all geometries produced by ST_AsMvtGeom(), and warn.
  -v --verbose          Print additional debugging information
  --help                Show this screen.
  --version             Show version.

PostgreSQL Options:
  -h --pghost=<host>    Postgres hostname. By default uses PGHOST env or "localhost" if not set.
  -P --pgport=<port>    Postgres port. By default uses PGPORT env or "5432" if not set.
  -d --dbname=<db>      Postgres db name. By default uses PGDATABASE env or "openmaptiles" if not set.
  -U --user=<user>      Postgres user. By default uses PGUSER env or "openmaptiles" if not set.
  --password=<password> Postgres password. By default uses PGPASSWORD env or "openmaptiles" if not set.
  --file=<sql-file>     Override SQL file generated by generate-sqltomvt script with the --query flag

These legacy environment variables should not be used, but they are still supported:
  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
"""

from docopt import docopt

import openmaptiles
from openmaptiles.pgutils import parse_pg_args
from openmaptiles.postserve import Postserve


# def main(args):
#     pghost, pgport, dbname, user, password = parse_pg_args(args)
#     Postserve(
#         url=args['--serve'].replace('<port>', args['--port']),
#         port=int(args['--port']),
#         pghost=pghost,
#         pgport=pgport,
#         dbname=dbname,
#         user=user,
#         password=password,
#         layers=args['--layer'],
#         exclude_layers=args['--exclude-layers'],
#         tileset_path=args['<tileset>'],
#         sql_file=args.get('--file'),
#         key_column=args['--key'],
#         gzip=args['--gzip'] and (args['<gzlevel>'] or True),
#         disable_feature_ids=args['--no-feature-ids'],
#         test_geometry=args['--test-geometry'],
#         verbose=args.get('--verbose'),
#     ).serve()


if __name__ == '__main__':
  # main(docopt(__doc__, version=openmaptiles.__version__))
  url = "localhost"  # URL where the server will be hosted
  port = 8080  # Port number to listen on
  pghost = "10.222.6.8"  # PostgreSQL host
  pgport = 5434  # PostgreSQL port
  dbname = "openmaptiles"  # PostgreSQL database name
  user = "openmaptiles"  # PostgreSQL username
  password = "openmaptiles"  # PostgreSQL password
  layers = []  # List of layers to include
  tileset_path = "./openmaptiles/openmaptiles.yaml"  # Path to tileset JSON file
  sql_file = None  # Optional SQL file containing custom queries
  key_column = ""  # Optional key column for tiles
  disable_feature_ids = False  # Disable feature IDs
  gzip = False  # Enable gzip compression
  verbose = True  # Enable verbose logging
  exclude_layers = []  # List of layers to exclude
  test_geometry = False  # Test geometry validity

  # Instantiate Postserve object
  postserve = Postserve(url, port, pghost, pgport, dbname, user, password,
                        layers, tileset_path, sql_file, key_column,
                        disable_feature_ids, gzip, verbose, exclude_layers,
                        test_geometry)

  # Start the server
  postserve.serve()

