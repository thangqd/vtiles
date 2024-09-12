#!/usr/bin/env python3

import argparse
import http.server
import json
import re
from socketserver import ThreadingMixIn
from vtiles.utils.pmtiles.reader import Reader, MmapSource
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

class ThreadingSimpleServer(ThreadingMixIn, http.server.HTTPServer):
    pass

def main():
    parser = argparse.ArgumentParser(description="HTTP server for PMTiles archives.")
    parser.add_argument("-i", help="PMTiles archive to serve")
    parser.add_argument("-port", help="Port to bind to")
    parser.add_argument("-host", help="Address to bind server to: default localhost")
    parser.add_argument(
        "--cors-allow-all",
        help="Return Access-Control-Allow-Origin:* header",
        action="store_true",
    )
    args = parser.parse_args()

    with open(args.i, "r+b") as f:
        source = MmapSource(f)
        reader = Reader(source)

        # Accessing format information from reader.header() dictionary
        header = reader.header()
        fmt = header["tile_type"]
        fmt = 'pbf'

        class Handler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/metadata":
                    self.send_response(200)
                    if args.cors_allow_all:
                        self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(header).encode("utf-8"))
                    return
                match = re.match("/(\d+)/(\d+)/(\d+)." + fmt, self.path)
                if not match:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write("bad request".encode("utf-8"))
                    return
                z = int(match.group(1))
                x = int(match.group(2))
                y = int(match.group(3))
                data = reader.get(z, x, y)
                if not data:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write("tile not found".encode("utf-8"))
                    return
                self.send_response(200)
                if args.cors_allow_all:
                    self.send_header("Access-Control-Allow-Origin", "*")
                if fmt == "pbf":
                    self.send_header("Content-Type", "application/x-protobuf")
                    self.send_header("Content-Encoding", "gzip")
                else:
                    self.send_header("Content-Type", "image/" + fmt)
                self.end_headers()
                self.wfile.write(data)

        host = args.host or "localhost"
        print(f"serving {host}:{args.port}/{{z}}/{{x}}/{{y}}.{fmt}, for development only")
        httpd = ThreadingSimpleServer((args.host or "", int(args.port)), Handler)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Keyboard interrupt received, stopping server...")
            httpd.server_close()
        
if __name__ == "__main__":
    main()

