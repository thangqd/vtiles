import argparse
import mercantile
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import box
import geojson

def generate_debug_grid(bbox, zoom_levels):
    """
    Generate tile coordinates for a debug grid.
    
    :param bbox: A tuple (min_longitude, min_latitude, max_longitude, max_latitude)
    :param zoom_levels: A list of zoom levels to generate tiles for
    :return: A list of tile coordinates
    """
    tiles = []
    min_lon, min_lat, max_lon, max_lat = bbox
    for zoom in zoom_levels:
        for tile in mercantile.tiles(min_lon, min_lat, max_lon, max_lat, zoom):
            tiles.append(tile)
    return tiles

def visualize_debug_grid(tiles):
    """
    Visualize the debug grid using matplotlib.
    
    :param tiles: A list of tile coordinates
    """
    fig, ax = plt.subplots()
    for tile in tiles:
        # Calculate the bounds of the tile
        bounds = mercantile.xy_bounds(tile)
        rect = patches.Rectangle(
            (bounds[0], bounds[1]), 
            bounds[2] - bounds[0], 
            bounds[3] - bounds[1], 
            linewidth=1, edgecolor='r', facecolor='none'
        )
        ax.add_patch(rect)
    
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Debug Grid')
    plt.grid(True)
    plt.show()

def tiles_to_geojson(tiles):
    """
    Convert tile coordinates to GeoJSON format.
    
    :param tiles: A list of tile coordinates
    :return: A GeoJSON FeatureCollection
    """
    features = []
    for tile in tiles:
        bounds = mercantile.xy_bounds(tile)
        geom = box(bounds[0], bounds[1], bounds[2], bounds[3])
        features.append(geojson.Feature(geometry=geom, properties={}))
    
    return geojson.FeatureCollection(features)

def save_geojson(geojson_data, filename):
    """
    Save GeoJSON data to a file.
    
    :param geojson_data: GeoJSON data to be saved
    :param filename: Name of the file to save the GeoJSON data
    """
    with open(filename, 'w') as f:
        geojson.dump(geojson_data, f)

def main():
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='Generate a debug grid for vector tiles.')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output GeoJSON file')
    args = parser.parse_args()

    # Define the bounding box and zoom levels
    bbox = (-180, -85.0511, 180, 85.0511)  # World bounds
    zoom_levels = [0, 1, 2, 3]  # Example zoom levels

    # Generate the debug grid
    tiles = generate_debug_grid(bbox, zoom_levels)
    
    # Visualize the debug grid
    visualize_debug_grid(tiles)
    
    # Convert to GeoJSON and save to file
    feature_collection = tiles_to_geojson(tiles)
    save_geojson(feature_collection, args.output)

if __name__ == '__main__':
    main()
