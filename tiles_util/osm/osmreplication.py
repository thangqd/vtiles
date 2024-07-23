import osmium as o
import sys
import datetime as dt
import osmium.replication.server as rserv
import argparse

class Stats(object):

    def __init__(self):
        self.added = 0
        self.modified = 0
        self.deleted = 0

    def add(self, o):
        if o.deleted:
            self.deleted += 1
        elif o.version == 1:
            self.added += 1
        else:
            self.modified += 1

    def outstats(self, prefix):
        print("%s added: %d" % (prefix, self.added))
        print("%s modified: %d" % (prefix, self.modified))
        print("%s deleted: %d" % (prefix, self.deleted))

class FileStatsHandler(o.SimpleHandler):
    def __init__(self):
        super(FileStatsHandler, self).__init__()
        self.nodes = Stats()
        self.ways = Stats()
        self.rels = Stats()

    def node(self, n):
        self.nodes.add(n)

    def way(self, w):
        self.ways.add(w)

    def relation(self, r):
        self.rels.add(r)

def main():
    parser = argparse.ArgumentParser(description="Compute stats from OSM replication server.")
    parser.add_argument('-url', required=True, help='Replication server URL')
    parser.add_argument('-starttime', required=True, help='Start time in the format YYYY-MM-DDTHH:MM:SSZ')
    parser.add_argument('-maxkB', type=int, required=True, help='Maximum kB to download')

    args = parser.parse_args()

    start = dt.datetime.strptime(args.starttime, "%Y-%m-%dT%H:%M:%SZ")
    if sys.version_info >= (3, 0):
        start = start.replace(tzinfo=dt.timezone.utc)
    maxkb = min(args.maxkB, 10 * 1024)

    repserv = rserv.ReplicationServer(args.url)

    seqid = repserv.timestamp_to_sequence(start)
    print("Initial sequence id:", seqid)

    h = FileStatsHandler()
    seqid = repserv.apply_diffs(h, seqid, maxkb)
    print("Final sequence id:", seqid)

    h.nodes.outstats("Nodes")
    h.ways.outstats("Ways")
    h.rels.outstats("Relations")

if __name__ == '__main__':
    main()
