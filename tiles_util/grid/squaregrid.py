import sqlite3
import numpy as np
from tiles_util.utils.mapbox_vector_tile import encode
import json
import gzip
import os

def generate_vector_tile(zoom, x, y):
    """Generate a vector tile for the specified zoom level and tile coordinates."""
    # Dummy data for demonstration purposes
    features = [
        {   
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [x * 0.1, y * 0.1]  # Example coordinates
            },
            "properties": {
                "name": "Example Point"
            }
        }
    ]
    tile_data = {
        'name': 'vectortile_grid',
        'features': features
    }
    # Encode features to Mapbox Vector Tile format
    print(tile_data)
    tile_data_encoded = encode(tile_data)
    tile_data_encoded_gzipped = gzip.compress(tile_data_encoded)
    return tile_data_encoded_gzipped

def save_vector_tile_to_mbtiles(conn, zoom, x, y, tile_data):
    """Save a vector tile to the MBTiles database."""
    cursor = conn.cursor()
    try:
        # Insert tile data into the MBTiles database
        cursor.execute("""
            INSERT INTO tiles (zoom_level, tile_column, tile_row, tile_data)
            VALUES (?, ?, ?, ?)
        """, (zoom, x, y, tile_data))
        conn.commit()
    finally:
        cursor.close()

def create_and_save_mbtiles(zoom_levels, output_mbtiles):
    """Create an MBTiles file with vector tiles for each zoom level."""
    # Connect to SQLite database (create if not exists)
    if os.path.exists(output_mbtiles):
        os.remove(output_mbtiles)
    conn = sqlite3.connect(output_mbtiles)
    
    try:
        # Create tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tiles (
                zoom_level INTEGER,
                tile_column INTEGER,
                tile_row INTEGER,
                tile_data BLOB,
                PRIMARY KEY (zoom_level, tile_column, tile_row)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                name TEXT,
                value TEXT
            )
        """)
        
        conn.execute("""
            INSERT INTO metadata (name, value)
            VALUES ('name', 'Vector Tile MBTiles'),
                   ('description', 'MBTiles file containing vector tiles at each zoom level'),
                   ('minzoom', '0'),
                   ('maxzoom', '3'),
                   ('bounds', '-180.000000,-85.051129,180.000000,85.051129')  
        """)
        
        conn.commit()

        for zoom in zoom_levels:
            num_tiles = 2 ** zoom
            
            for x in range(num_tiles):
                for y in range(num_tiles):
                    # Generate vector tile data
                    tile_data = generate_vector_tile(zoom, x, y)
                    # Save tile data to MBTiles
                    save_vector_tile_to_mbtiles(conn, zoom, x, y, tile_data)
                    print(f"Saved vector tile {zoom}/{x}/{y}")

    finally:
        conn.close()

    print(f"MBTiles file created at {output_mbtiles}")

# Example usage
zoom_levels = [0, 1, 2, 3]  # Define the zoom levels you want
output_mbtiles = "vector_tiles.mbtiles"
create_and_save_mbtiles(zoom_levels, output_mbtiles)

