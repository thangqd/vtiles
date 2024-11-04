import os
import http.server
import socketserver
import sys

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()


def inject_url_in_html(file_path, url):
    # Read original content and store it for later
    with open(file_path, 'r') as f:
        original_content = f.read()

    updated_content = original_content.replace('https://map-api-new.sovereignsolutions.net/sovereign/v20240410/vietnam/tiles.json', url)

    # Write the updated content to the file
    with open(file_path, 'w') as f:
        f.write(updated_content)

    # Return original content for restoration
    return original_content

def start_server(directory, port=8000):
    handler = CORSRequestHandler
    socketserver.TCPServer.allow_reuse_address = True

    os.chdir(directory)

    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving HTTP on port {port}")
        httpd.serve_forever()

def main():
    if len(sys.argv) < 2:
        print("Usage: tilesinspect <Tiles JSON URL>")
        sys.exit(1)

    url = sys.argv[1]
    directory = os.path.dirname(os.path.abspath(__file__))
    index_file_path = os.path.join(directory, 'index.html')

    if not os.path.exists(index_file_path):
        print(f"Error: The file '{index_file_path}' does not exist.")
        sys.exit(1)

    original_content = inject_url_in_html(index_file_path, url)
    
    try:
        start_server(directory)
    finally:
        # Restore the original content
        with open(index_file_path, 'w') as f:
            f.write(original_content)

if __name__ == "__main__":
    main()
