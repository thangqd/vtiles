from shapely.geometry import LineString, Polygon
from shapely.ops import transform
import mercantile
import mapbox_vector_tile
from pyproj import Transformer

SRID_LNGLAT = 4326
SRID_SPHERICAL_MERCATOR = 3857

def linestring_in_tile(tile_bounds, line):
    # `mapbox-vector-tile` has a hardcoded tile extent of 4096 units.
    MVT_EXTENT = 4096

    # Convert the bounds to a polygon if it's not already
    if not isinstance(tile_bounds, Polygon):
        tile_bounds = Polygon(tile_bounds)

    # Get the bounds of the tile
    (x0, y0, x_max, y_max) = tile_bounds.bounds
    x_span = x_max - x0
    y_span = y_max - y0

    tile_based_coords = []
    for x_merc, y_merc in line.coords:
        tile_based_coord = (int((x_merc - x0) * MVT_EXTENT / x_span),
                            int((y_merc - y0) * MVT_EXTENT / y_span))
        tile_based_coords.append(tile_based_coord)

    return LineString(tile_based_coords)

# Create a Transformer for coordinate transformation
transformer = Transformer.from_crs(SRID_LNGLAT, SRID_SPHERICAL_MERCATOR, always_xy=True)

# Example tile XYZ and bounds
tile_xyz = (1,1,1)
tile_bounds = mercantile.bounds(*tile_xyz)

# Convert bounds to a Polygon
tile_bounds_polygon = Polygon([(tile_bounds.west, tile_bounds.south),
                               (tile_bounds.east, tile_bounds.south),
                               (tile_bounds.east, tile_bounds.north),
                               (tile_bounds.west, tile_bounds.north),
                               (tile_bounds.west, tile_bounds.south)])

# Transform tile bounds polygon to spherical mercator
tile_bounds_polygon = transform(lambda x, y: transformer.transform(x, y), tile_bounds_polygon)

# Create and transform LineString
lnglat_line = LineString([(-122.1, 45.1), (-80.2, 35.2)])
mercator_line = transform(lambda x, y: transformer.transform(x, y), lnglat_line)

# Convert line to tile-based coordinates
tile_line = linestring_in_tile(tile_bounds_polygon, mercator_line)

# Convert LineString to GeoJSON-like format for Mapbox Vector Tile
features = [{
    "geometry": {
        "type": "LineString",
        "coordinates": list(tile_line.coords)
    },
    "properties": {
        "stuff": "things"
    }
}]

tile_pbf = mapbox_vector_tile.encode({
    "name": "my-layer",
    "features": features
},default_options={"extents":4096})

print(tile_pbf)
decoded = mapbox_vector_tile.decode(tile_pbf)
print(decoded)
