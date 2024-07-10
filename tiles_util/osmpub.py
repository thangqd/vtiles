import osmium as o
import argparse

class PubHandler(o.SimpleHandler):
    def __init__(self):
        super(PubHandler, self).__init__()
        self.pubs = []

    def node(self, n):
        if 'amenity' in n.tags and n.tags['amenity'] == 'pub' and 'name' in n.tags:
            self.pubs.append(n.tags['name'])

    def way(self, w):
        if 'amenity' in w.tags and w.tags['amenity'] == 'pub' and 'name' in w.tags:
            self.pubs.append(w.tags['name'])

    def relation(self, r):
        if 'amenity' in r.tags and r.tags['amenity'] == 'pub' and 'name' in r.tags:
            self.pubs.append(r.tags['name'])

def main():
    parser = argparse.ArgumentParser(description="Search for pubs in an OSM file and list their names.")
    parser.add_argument('-i', '--input', required=True, help='Path to the input OSM file')

    args = parser.parse_args()

    handler = PubHandler()
    handler.apply_file(args.input)

    for pub_name in handler.pubs:
        print(pub_name)

if __name__ == '__main__':
    main()
