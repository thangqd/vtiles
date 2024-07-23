import sqlite3
import argparse

def extract_tile_to_pbf(mbtiles_file, z, x, y, output_pbf):
    conn = sqlite3.connect(mbtiles_file)
    cursor = conn.cursor()
    cursor.execute("SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?", (z, x, y))
    tile_data = cursor.fetchone()
    
    if tile_data:
        with open(output_pbf, 'wb') as f:
            f.write(tile_data[0])
    else:
        print("Tile not found.")

    conn.close()

def main():
    parser = argparse.ArgumentParser(description='Extract a tile from MBTiles to PBF.')
    parser.add_argument('-i', '--input', required=True, help='Input MBTiles file')
    parser.add_argument('-z', '--zoom', type=int, required=True, help='Zoom level')
    parser.add_argument('-x', '--xcoord', type=int, required=True, help='X coordinate')
    parser.add_argument('-y', '--ycoord', type=int, required=True, help='Y coordinate')
    parser.add_argument('-o', '--output', required=True, help='Output PBF file')
    
    args = parser.parse_args()
    
    extract_tile_to_pbf(args.input, args.zoom, args.xcoord, args.ycoord, args.output)

if __name__ == '__main__':
    main()
