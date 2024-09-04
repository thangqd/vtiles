import sqlite3
import vtiles.utils.mercantile as mercantile

def get_max_zoom(mbtiles_input):
    # Connect to the MBTiles SQLite database
    conn = sqlite3.connect(mbtiles_input)
    cursor = conn.cursor()

    # Query to find the minimum zoom level from the tiles table
    cursor.execute("SELECT MAX(zoom_level) FROM tiles")
    min_zoom = cursor.fetchone()[0]

    conn.close()
    return min_zoom

def get_bounds_at_zoom(mbtiles_input, zoom_level):
    # Connect to the MBTiles SQLite database
    conn = sqlite3.connect(mbtiles_input)
    cursor = conn.cursor()

    # Query tiles at the specified zoom level
    cursor.execute("SELECT tile_column, tile_row FROM tiles WHERE zoom_level = ?", (zoom_level,))
    tiles = cursor.fetchall()

    # Calculate bounding boxes for each tile
    bounds = []
    for tile in tiles:
        x, y = tile
        flip_y = (1 << zoom_level) - 1 - y # TMS scheme
        # Calculate bounds for the given tile coordinates
        tile_bounds = mercantile.bounds(x,y, zoom_level)
        bounds.append(tile_bounds)

    conn.close()
    return bounds

def compute_max_bound(bounds):
    # Initialize min and max coordinates with extreme values
    min_lat = min_lon = float('inf')
    max_lat = max_lon = float('-inf')

    for bound in bounds:
        # Unpack bounding box coordinates (west, south, east, north)
        west, south, east, north = bound

        # Update min and max values
        min_lat = min(min_lat, south)
        max_lat = max(max_lat, north)
        min_lon = min(min_lon, west)
        max_lon = max(max_lon, east)

    # Return the overall bounding box
    return min_lon, min_lat, max_lon, max_lat

# Main execution
mbtiles_input = './data/nepal.mbtiles'
min_zoom = get_max_zoom(mbtiles_input)
print(f"Maximum Zoom Level: {min_zoom}")

bounds = get_bounds_at_zoom(mbtiles_input, min_zoom)
max_bound = compute_max_bound(bounds)
print(f"Maximum Bounding Box: {max_bound}")
