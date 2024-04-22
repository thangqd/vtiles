import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

class TileServer(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        if directory is None:
            directory = os.getcwd()  # Default to current working directory
        super().__init__(*args, directory=directory, **kwargs)

def serve_vector_tiles(directory, port=8000):
    os.chdir(directory)
    server_address = ('', port)
    httpd = HTTPServer(server_address, TileServer)
    print(f"Server running at http://localhost:{port}/")
    httpd.serve_forever()

if __name__ == "__main__":
    serve_vector_tiles("nepal", port=8080)
