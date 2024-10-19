import os
import http.server
import socketserver
import sys

def inject_url_in_html(file_path, url):
    """
    Injects the provided URL into the `index.html` file.
    """
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace the placeholder in the HTML file with the provided URL
    updated_content = content.replace(
        'https://raw.githubusercontent.com/thangqd/vstyles/main/vstyles/topography/vietnam.json',
        url
    )

    with open(file_path, 'w') as f:
        f.write(updated_content)

def start_server(directory, port=8000):
    """
    Starts an HTTP server in the specified directory.
    """
    handler = http.server.SimpleHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True

    # Change working directory to the folder where assets are stored
    os.chdir(directory)

    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving HTTP on port {port}")
        httpd.serve_forever()

def main():
    if len(sys.argv) < 2:
        print("Usage: tilesinspect <URL>")
        sys.exit(1)

    # Get the URL from the command line argument
    url = sys.argv[1]

    # Set the path to the directory where the `index.html` and other assets are located
    directory = os.path.dirname(os.path.abspath(__file__))

    # Path to `index.html`
    index_file_path = os.path.join(directory, 'index.html')

    # Check if index.html exists
    if not os.path.exists(index_file_path):
        print(f"Error: The file '{index_file_path}' does not exist.")
        sys.exit(1)

    # Inject the provided URL into the `index.html`
    inject_url_in_html(index_file_path, url)

    # Start the server on the specified folder and serve files
    start_server(directory)

if __name__ == "__main__":
    main()
