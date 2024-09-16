from http.server import SimpleHTTPRequestHandler, HTTPServer
import os

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):

    def check_compressed(self, pbf_file):
        try:
            with open(pbf_file, 'rb') as f:
                tile_data = f.read(2)  # Read only the first two bytes
            # Check for GZIP compression
            if tile_data[:2] == b'\x1f\x8b':
                return 'GZIP'
            # Check for ZLIB compression
            elif tile_data[:2] == b'\x78\x9c' or tile_data[:2] == b'\x78\x01' or tile_data[:2] == b'\x78\xda':
                return 'ZLIB'
            else:
                return None
        except Exception as e:
            print(f"Error reading PBF file: {e}")
            return None

    def end_headers(self):
        # If the requested file is a .pbf file
        if self.path.endswith('.pbf'):
            file_path = self.translate_path(self.path)  # Get the full file path
            compression_type = self.check_compressed(file_path)  # Check the compression type

            if compression_type == 'GZIP':
                self.send_header('Content-Encoding', 'gzip')
            elif compression_type == 'ZLIB':
                self.send_header('Content-Encoding', 'deflate')  # ZLIB uses 'deflate' as encoding

        SimpleHTTPRequestHandler.end_headers(self)

    def guess_type(self, path):
        base, ext = os.path.splitext(path)
        if ext.lower() == '.pbf':
            return 'application/x-protobuf'
        else:
            return SimpleHTTPRequestHandler.guess_type(self, path)

def main():
    port = 8000  # Set the port
    server_address = ('', port)  # Set the server address
    handler_class = CustomHTTPRequestHandler  # Specify the custom request handler
    httpd = HTTPServer(server_address, handler_class)  # Create the HTTP server
    print(f"Simple Vector Tile Server for tiles cache folder running on port {port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Keyboard interrupt received, stopping server...")
        httpd.server_close()

if __name__ == "__main__":
    main()
