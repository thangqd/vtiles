import sqlite3
import argparse
from io import BytesIO
from PIL import Image
from vtiles.utils.mapbox_vector_tile import decode
import gzip
import zlib


def get_sample_tile_data(db_path):
    """Retrieve a sample tile data from the tiles table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = "SELECT tile_data FROM tiles LIMIT 1;"
    cursor.execute(query)
    tile_data = cursor.fetchone()

    conn.close()
    if tile_data:
        return tile_data[0]
    else:
        return None

def decompress_tile_data(tile_data):
    """Decompress tile data if it is compressed and return decompressed data with a compression flag."""
    try:
        # Check for gzip compression
        with BytesIO(tile_data) as buf:
            buf.seek(0)
            with gzip.GzipFile(fileobj=buf) as gz:
                return gz.read(), 'gzip'
    except (OSError, EOFError):
        try:
            # Check for zlib compression
            return zlib.decompress(tile_data), 'zlib'
        except zlib.error:
            # No compression or unrecognized compression format
            return tile_data, 'none'
    except Exception as e:
        raise RuntimeError(f"Decompression error: {e}")

def check_tile_format(tile_data):
    """Check the format of the tile data and print whether it is compressed."""
    if tile_data:
        try:
            decompressed_data, compression_type = decompress_tile_data(tile_data)  
            print(f"Compression type: {compression_type}")                  
            with BytesIO(decompressed_data) as buf:
                try:
                    # Attempt to open as an image (for raster tiles)
                    with Image.open(buf) as img:
                        return f"Raster Tile (Format: {img.format})"
                except (IOError, OSError):
                    try:
                        # Attempt to decode as vector tile (for vector tiles)
                        decode(decompressed_data)
                        return "Vector Tile"
                    except Exception as e:
                        return f"Error identifying format: {e}"
        except Exception as e:
            return f"Error during decompression or format check: {e}"
    else:
        return "No tile data found."


def get_standard_tile_count(zoom_level):
    """Calculate the standard number of tiles for a given zoom level."""
    num_tiles_per_side = 2 ** zoom_level
    return num_tiles_per_side * num_tiles_per_side

def count_tiles_for_each_zoom(db_path):
    """Count the number of tiles for each zoom level in the tiles table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
    SELECT zoom_level, COUNT(*) AS tile_count
    FROM tiles
    GROUP BY zoom_level
    ORDER BY zoom_level;
    """

    cursor.execute(query)
    results = cursor.fetchall()

    conn.close()
    return results

def find_duplicates(db_path):
    """Find duplicate rows in the tiles table based on zoom_level, tile_column, and tile_row."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
    SELECT zoom_level, tile_column, tile_row, COUNT(*) AS count
    FROM tiles
    GROUP BY zoom_level, tile_column, tile_row
    HAVING COUNT(*) > 1
    ORDER BY count;
    """

    cursor.execute(query)
    duplicates = cursor.fetchall()

    conn.close()
    return duplicates

def count_total_duplicates(duplicates):
    """Calculate the total number of duplicate rows."""
    total_duplicates = sum(count - 1 for _, _, _, count in duplicates)
    return total_duplicates

def get_min_zoom_level(db_path):
    """Get the minimum zoom level from the tiles table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = "SELECT MIN(zoom_level) FROM tiles;"
    cursor.execute(query)
    min_zoom = cursor.fetchone()[0]

    conn.close()
    return min_zoom

def get_max_zoom_level(db_path):
    """Get the maximum zoom level from the tiles table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = "SELECT MAX(zoom_level) FROM tiles;"
    cursor.execute(query)
    max_zoom = cursor.fetchone()[0]

    conn.close()
    return max_zoom

def count_total_tiles(db_path):
    """Calculate the total number of tiles in the tiles table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = "SELECT COUNT(*) FROM tiles;"
    cursor.execute(query)
    total_tiles = cursor.fetchone()[0]

    conn.close()
    return total_tiles

def main():
    parser = argparse.ArgumentParser(description='Analyze an MBTiles file for tile counts and duplicates.')
    parser.add_argument('db_path', type=str, help='Path to the MBTiles database file.')

    args = parser.parse_args()

    db_path = args.db_path

    # Retrieve a sample tile data
    tile_data = get_sample_tile_data(db_path)
    
    # Get the tile counts for each zoom level
    tile_counts = count_tiles_for_each_zoom(db_path)
    
    # Get min and max zoom levels
    min_zoom_level = get_min_zoom_level(db_path)
    max_zoom_level = get_max_zoom_level(db_path)
    
    # Get total number of tiles
    total_tiles = count_total_tiles(db_path)
    
    print(f"Min Zoom Level: {min_zoom_level}")
    print(f"Max Zoom Level: {max_zoom_level}")
    print(f"Total Number of Tiles: {total_tiles}")
    # Check the format of the tile data
    tile_format = check_tile_format(tile_data)    
    print(f"Tile format: {tile_format}")

    print("\nTile count for each zoom level:")
    # Print results with standard number of tiles
    print(f"{'Zoom Level':<12} {'Actual Tile Count':<20} {'Standard Tile Count':<20} {'Matches Standard'}")
    print("="*62)

    for zoom_level, actual_tile_count in tile_counts:
        standard_tile_count = get_standard_tile_count(zoom_level)
        matches_standard = "Yes" if actual_tile_count == standard_tile_count else "No"
        print(f"{zoom_level:<12} {actual_tile_count:<20} {standard_tile_count:<20} {matches_standard}")

    # Find duplicates
    duplicates = find_duplicates(db_path)
    
    # Calculate and print total number of duplicate rows
    total_duplicates = count_total_duplicates(duplicates)
    
    # Print duplicates
    print("\nDuplicate Rows:")
    print(f"Total number of duplicate rows: {total_duplicates}")
    if duplicates:
        print(f"{'Zoom Level':<12} {'Tile Column':<12} {'Tile Row':<12} {'Count':<6}")
        print("="*42)
        for zoom_level, tile_column, tile_row, count in duplicates:
            print(f"{zoom_level:<12} {tile_column:<12} {tile_row:<12} {count:<6}")
    else:
        print("No duplicate rows found.")

if __name__ == '__main__':
    main()