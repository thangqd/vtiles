import sys
import json
import osmium as o
from tqdm import tqdm  # Import tqdm for progress bar
import os 

geojsonfab = o.geom.GeoJSONFactory()

class GeoJsonWriter(o.SimpleHandler):
    def __init__(self, output_file):
        super().__init__()
        self.output_file = output_file
        self.features = []
    
    def finish(self):
        try:
            with open(self.output_file, 'w') as f:
                f.write('{"type": "FeatureCollection", "features": [\n')
                for i, feature in enumerate(tqdm(self.features, desc='Writing GeoJSON')):
                    if i > 0:
                        f.write(',\n')
                    json.dump(feature, f)
                f.write('\n]}')
            print(f"GeoJSON file '{self.output_file}' successfully created.")
        except Exception as e:
            print(f"Error: Failed to write GeoJSON file '{self.output_file}': {e}")

    def node(self, n):
        if n.tags:
            self.add_feature(geojsonfab.create_point(n), n.tags)

    def way(self, w):
        if w.tags and not w.is_closed():
            self.add_feature(geojsonfab.create_linestring(w), w.tags)

    def area(self, a):
        if a.tags:
            self.add_feature(geojsonfab.create_multipolygon(a), a.tags)

    def add_feature(self, geojson, tags):
        geom = json.loads(geojson)
        if geom:
            feature = {'type': 'Feature', 'geometry': geom, 'properties': dict(tags)}
            self.features.append(feature)

def main():
    if len(sys.argv) != 5 or sys.argv[1] != '-i' or sys.argv[3] != '-o':
        print(f"Usage: {sys.argv[0]} -i <path_to_osm_file.osm.pbf> -o <output_file.geojson>")
        sys.exit(1)
    
    osmfile = sys.argv[2]
    output_file = sys.argv[4]
    
    if not os.path.isfile(osmfile):
        print(f"Error: File {osmfile} not found.")
        sys.exit(1)

    handler = GeoJsonWriter(output_file)
    handler.apply_file(osmfile)
    handler.finish()

if __name__ == '__main__':
    main()
