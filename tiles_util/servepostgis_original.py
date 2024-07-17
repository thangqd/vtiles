import http.server
import socketserver
import re
import psycopg2
import yaml
import argparse

# Argument parser for command-line arguments
parser = argparse.ArgumentParser(description='Serve MVT tiles from a PostgreSQL/PostGIS database.')
parser.add_argument('config_file', help='Path to the YAML configuration file')
args = parser.parse_args()

# Load configuration from a YAML file
with open(args.config_file, 'r') as file:
    config = yaml.safe_load(file)

# Extract database and HTTP server configuration
DATABASE = config['database']
HTTP_SERVER = config['http_server']

########################################################################

class TileRequestHandler(http.server.BaseHTTPRequestHandler):

    DATABASE_CONNECTION = None

    def pathToTile(self, path):
        m = re.search(r'^\/(\d+)\/(\d+)\/(\d+)\.(\w+)', path)
        if m:
            return {'zoom': int(m.group(1)),
                    'x': int(m.group(2)),
                    'y': int(m.group(3)),
                    'format': m.group(4)}
        else:
            return None

    def tileIsValid(self, tile):
        if not ('x' in tile and 'y' in tile and 'zoom' in tile):
            return False
        if 'format' not in tile or tile['format'] not in ['pbf', 'mvt']:
            return False
        size = 2 ** tile['zoom']
        if tile['x'] >= size or tile['y'] >= size:
            return False
        if tile['x'] < 0 or tile['y'] < 0:
            return False
        return True

    def envelopeToBoundsSQL(self, tile):
        return f'ST_TileEnvelope({tile["zoom"]}, {tile["x"]}, {tile["y"]})'

    def envelopeToSQL(self, tile):
        sql_queries = []
        for table_name, table_config in config['tables'].items():
            if 'min_zoom' in table_config and tile['zoom'] < table_config['min_zoom']:
                continue
            if 'max_zoom' in table_config and tile['zoom'] > table_config['max_zoom']:
                continue
            
            tbl = table_config.copy()
            tbl['env'] = self.envelopeToBoundsSQL(tile)
            sql_tmpl = """
                WITH 
                bounds AS (
                    SELECT {env} AS geom, 
                        {env}::box2d AS b2d
                ),
                mvtgeom AS (
                    SELECT ST_AsMVTGeom(ST_Transform(t.{geomColumn}, 3857), bounds.b2d) AS geom, 
                        {attrColumns}
                    FROM {table} t, bounds
                    WHERE ST_Intersects(t.{geomColumn}, ST_Transform(bounds.geom, {srid}))
                ) 
                SELECT '{table_name}' AS layer, ST_AsMVT(mvtgeom.*, '{table_name}') FROM mvtgeom
            """
            sql_queries.append(sql_tmpl.format(table_name=table_name, **tbl))
        
        return sql_queries


    def sqlToPbf(self, sql_queries):
        if not self.DATABASE_CONNECTION:
            try:
                self.DATABASE_CONNECTION = psycopg2.connect(**DATABASE)
            except (Exception, psycopg2.Error) as error:
                self.send_error(500, f"Cannot connect to database: {str(error)}")
                return None

        responses = []
        with self.DATABASE_CONNECTION.cursor() as cur:
            for sql in sql_queries:
                cur.execute(sql)
                if not cur:
                    self.send_error(404, f"SQL query failed: {sql}")
                    return None
                responses.append(cur.fetchone())

        return responses

    def do_GET(self):
        tile = self.pathToTile(self.path)
        if not (tile and self.tileIsValid(tile)):
            self.send_error(400, f"Invalid tile path: {self.path}")
            return

        sql_queries = self.envelopeToSQL(tile)
        pbf_responses = self.sqlToPbf(sql_queries)

        self.log_message("path: %s\ntile: %s" % (self.path, tile))
        self.log_message("sql_queries: %s" % (sql_queries))

        if pbf_responses is None or len(pbf_responses) == 0:
            self.send_error(500, "Failed to generate tile data")
            return
        
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-type", "application/x-protobuf")
        self.end_headers()
        
        # Concatenate all MVT responses into a single protobuf response
        for response in pbf_responses:
            self.wfile.write(response[1])  # Assuming the MVT data is in the second column

########################################################################

def main():
    try:
        with http.server.HTTPServer((HTTP_SERVER['host'], HTTP_SERVER['port']), TileRequestHandler) as server:
            print(f"Serving at port {HTTP_SERVER['port']}")
            server.serve_forever()
    except KeyboardInterrupt:
        if TileRequestHandler.DATABASE_CONNECTION:
            TileRequestHandler.DATABASE_CONNECTION.close()
        print('^C received, shutting down server')
        server.socket.close()

if __name__ == "__main__":
    main()
