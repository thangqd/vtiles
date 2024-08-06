import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon

def create_hex_grid(bounds, hex_size):
    """Create a grid of hexagons with the given size."""
    minx, miny, maxx, maxy = bounds
    dx = 3/2 * hex_size
    dy = np.sqrt(3) * hex_size
    
    x_coords = np.arange(minx, maxx, dx)
    y_coords = np.arange(miny, maxy, dy)
    
    polygons = []
    for x in x_coords:
        for y in y_coords:
            for i in range(2):
                for j in range(2):
                    hex_x = x + i * dx
                    hex_y = y + j * dy
                    hexagon = Polygon([
                        (hex_x + hex_size * np.cos(np.pi / 3 * k), hex_y + hex_size * np.sin(np.pi / 3 * k))
                        for k in range(6)
                    ])
                    polygons.append(hexagon)
    
    return gpd.GeoDataFrame({'geometry': polygons}, crs='EPSG:4326')

# Example usage
bounds = (-180, -90, 180, 90)  # World bounds
hex_size = 1.0  # Size of each hexagon
hex_grid = create_hex_grid(bounds, hex_size)

# Save to GeoJSON
hex_grid.to_file("hex_grid.geojson", driver="GeoJSON")

print("Hexagonal grid saved as hex_grid.geojson")
