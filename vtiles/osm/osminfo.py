import osmium as o
import sys
import os
import datetime

class FileStatsHandler(o.SimpleHandler):
    def __init__(self):
        super(FileStatsHandler, self).__init__()
        self.nodes = 0
        self.ways = 0
        self.rels = 0

    def node(self, n):
        self.nodes += 1

    def way(self, w):
        self.ways += 1

    def relation(self, r):
        self.rels += 1

class CountHandler(o.SimpleHandler):
    def __init__(self):
        super(CountHandler, self).__init__()
        self.nodes = 0
        self.ways = 0
        self.rels = 0

    def node(self, n):
        self.nodes += 1

    def way(self, w):
        self.ways += 1

    def relation(self, r):
        self.rels += 1

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path_to_osm_file.osm.pbf>")
        sys.exit(1)

    osmfile = sys.argv[1]

    if not os.path.exists(osmfile):
        print(f"File not found: {osmfile}")
        sys.exit(1)

    file_stat = os.stat(osmfile)
    file_size_mb = round(file_stat.st_size / (1024 * 1024), 2)
    file_last_modified = datetime.datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %I:%M:%S %p")

    print('######')
    print(f"File size: {file_size_mb} MB")
    print(f"Last modified: {file_last_modified}")
    print('######')

    count_handler = CountHandler()
    try:
        # First pass to count total nodes, ways, and relations
        count_handler.apply_file(osmfile)

        # Initialize the FileStatsHandler without progress bars
        handler = FileStatsHandler()
        handler.apply_file(osmfile)

    except Exception as e:
        print(f"Error while processing the file: {e}")
        sys.exit(1)
    
    finally:
        sys.stdout.flush()  # Explicitly flush stdout again
        sys.exit(0)

if __name__ == "__main__":
    main()
