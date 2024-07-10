import osmium as o
import sys, os, datetime

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


def main(osmfile):
    h = FileStatsHandler()

    h.apply_file(osmfile)

    print("Nodes: %d" % h.nodes)
    print("Ways: %d" % h.ways)
    print("Relations: %d" % h.rels)

    return 0

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path_to_osm_file.osm.pbf>")
        sys.exit(1)
    osmfile = sys.argv[1]    
    file_stat = os.stat(osmfile)
    file_size_mb = round(file_stat.st_size / (1024 * 1024),2)
    # file_created = datetime.datetime.fromtimestamp(file_stat.st_ctime).strftime("%Y-%m-%d %I:%M:%S %p")
    file_last_modified = datetime.datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %I:%M:%S %p")
    print('######')
    print("File size: ", file_size_mb, 'MB')
    # print("Date created: ", file_created)
    print("Last modified: ", file_last_modified)
    print('######')
    h = FileStatsHandler()
    h.apply_file(osmfile)
    print("Nodes: %d" % h.nodes)
    print("Ways: %d" % h.ways)
    print("Relations: %d" % h.rels)
    os._exit(0)

if __name__ == "__main__":
    main()