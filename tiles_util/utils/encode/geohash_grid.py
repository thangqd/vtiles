import geohash
from shapely.geometry import Polygon, mapping
import geojson

def geohash_to_polygon(gh):
    # Get bounding box coordinates for the geohash
    bbox = geohash.bbox(gh)
    
    # Create a polygon from the bounding box
    polygon = Polygon([
        (bbox['w'], bbox['s']),
        (bbox['w'], bbox['n']),
        (bbox['e'], bbox['n']),
        (bbox['e'], bbox['s']),
        (bbox['w'], bbox['s'])
    ])
    
    return polygon

def generate_geohashes(precision):
    # Generate geohashes for the given precision
    geohashes = set()
    
    # Generate geohashes for all possible values at the given precision
    def recursive_generate(current, length):
        if length == precision:
            geohashes.add(current)
            return
        
        for char in "0123456789bcdefghjkmnpqrstuvwxyz":
            recursive_generate(current + char, length + 1)
    
    recursive_generate("", 0)
    return geohashes

def create_world_polygons_at_precision(precision):
    geohash_polygons = []
    
    # Generate geohashes for the given precision
    geohashes = generate_geohashes(precision)
    
    for gh in geohashes:
        polygon = geohash_to_polygon(gh)
        geohash_polygons.append(geojson.Feature(
            geometry=mapping(polygon),
            properties={"geohash": gh}
        ))
    
    # Create a FeatureCollection
    feature_collection = geojson.FeatureCollection(geohash_polygons)
    
    return feature_collection

def save_to_geojson(feature_collection, filename):
    # Write GeoJSON to file
    with open(filename, 'w') as f:
        geojson.dump(feature_collection, f)

# Example usage
precision = 0  # Precision level for the entire world grid
world_polygons = create_world_polygons_at_precision(precision)
output_filename = f'world_geohash_polygons_precision_{precision}.geojson'
save_to_geojson(world_polygons, output_filename)

print(f"GeoJSON file saved as: {output_filename}")
