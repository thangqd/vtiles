import osmium
import geojson
import sys

class OSMToGeoJSONHandler(osmium.SimpleHandler):
    def __init__(self):
        super(OSMToGeoJSONHandler, self).__init__()
        self.features = []

    def node(self, n):
        feature = geojson.Feature(
            geometry=geojson.Point((n.location.lon, n.location.lat)),
            properties={"id": n.id, "type": "node"}
        )
        self.features.append(feature)

    def way(self, w):
        if w.is_closed():
            geometry = geojson.Polygon([[(n.lon, n.lat) for n in w.nodes]])
        else:
            geometry = geojson.LineString([(n.lon, n.lat) for n in w.nodes])
        
        feature = geojson.Feature(
            geometry=geometry,
            properties={"id": w.id, "type": "way"}
        )
        self.features.append(feature)

    def relation(self, r):
        geometry = None
        if r.is_multipolygon():
            polygons = []
            for outer_ring in r.outer_rings():
                outer_polygon = [(n.lon, n.lat) for n in outer_ring]
                inner_polygons = []
                for inner_ring in outer_ring.inner_rings():
                    inner_polygon = [(n.lon, n.lat) for n in inner_ring]
                    inner_polygons.append(inner_polygon)
                polygons.append(geojson.Polygon([outer_polygon] + inner_polygons))
            geometry = geojson.MultiPolygon(polygons)
        
        feature = geojson.Feature(
            geometry=geometry,
            properties={"id": r.id, "type": "relation"}
        )
        self.features.append(feature)

def convert_osm_to_geojson(osm_file, geojson_file):
    handler = OSMToGeoJSONHandler()
    handler.apply_file(osm_file)
    
    feature_collection = geojson.FeatureCollection(handler.features)
    
    with open(geojson_file, "w") as f:
        geojson.dump(feature_collection, f)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py input.osm.pbf output.geojson")
        sys.exit(1)
    
    input_osm_file = sys.argv[1]
    output_geojson_file = sys.argv[2]
    
    convert_osm_to_geojson(input_osm_file, output_geojson_file)
