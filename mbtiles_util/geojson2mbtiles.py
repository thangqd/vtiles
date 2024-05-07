import argparse
import json
import sqlite3
from mercantile import bounds, ul
import zlib

def geojson_to_mbtiles(input_file, output_file):
    # Read GeoJSON data
    with open(input_file, 'r') as f:
        geojson_data = json.load(f)

    # Initialize SQLite database for MBTiles
    conn = sqlite3.connect(output_file)
    c = conn.cursor()
    c.execute('''CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob);''')
    conn.commit()

    # Process features
    for feature in geojson_data['features']:
        geometry = feature['geometry']
        properties = feature.get('properties', {})

        # Get bounds of the feature
        lon_min, lat_min, lon_max, lat_max = bounds(geometry)

        # Calculate tile coordinates for upper-left corner
        zoom_level = 14
        tile_ul = ul(lon_min, lat_max, zoom_level)

        # Insert feature data into SQLite database for each tile in the bounding box
        tile_data = zlib.compress(json.dumps(feature).encode('utf-8'))
        for tile_x in range(tile_ul.x, tile_ul.x + 2):
            for tile_y in range(tile_ul.y, tile_ul.y + 2):
                c.execute("INSERT INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)",
                          (zoom_level, tile_x, tile_y, tile_data))

    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='Convert GeoJSON to MBTiles format')
    parser.add_argument('-i', '--input', type=str, required=True, help='Input GeoJSON file')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output MBTiles file')
    args = parser.parse_args()

    input_file = args.input
    output_file = args.output

    geojson_to_mbtiles(input_file, output_file)

if __name__ == "__main__":
    main()
