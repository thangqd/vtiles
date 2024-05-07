from http.server import SimpleHTTPRequestHandler, HTTPServer
import os
import gzip

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        if self.path.endswith('.pbf'):
            self.send_header('Content-Encoding', 'gzip')
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
    # httpd.serve_forever()  # Start serving forever
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Keyboard interrupt received, stopping server...")
        httpd.server_close()

if __name__ == "__main__":
    main()