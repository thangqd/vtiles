import sqlite3
import argparse
import gzip, zlib

def extract_tile_to_pbf(mbtiles_file, z, x, y, output_pbf):
    try:
        # Connect to the MBTiles database
        conn = sqlite3.connect(mbtiles_file)
        cursor = conn.cursor()        
       
        # Query the tile data
        cursor.execute('SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=?', (z, x, y))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            tile_data = row[0]            
            # # Check for GZIP compression
            # if tile_data[:2] == b'\x1f\x8b':
            #     tile_data = gzip.decompress(tile_data)
            #     print('GZIP')
            # # Check for ZLIB compression
            # elif tile_data[:2] == b'\x78\x9c' or tile_data[:2] == b'\x78\x01' or tile_data[:2] == b'\x78\xda':
            #     tile_data = zlib.decompress(tile_data)
            #     print('ZLIB')

            # # Write the decompressed tile data to the output PBF file
            with open(output_pbf, 'wb') as f:
                f.write(tile_data)
            print(f"Tile {z}/{x}/{y} successfully extracted to {output_pbf}")
        else:
            print("Tile not found in MBTiles file")
    except sqlite3.Error as e:
        print(f"Failed to read MBTiles file: {e}")
    except (OSError, zlib.error, gzip.BadGzipFile) as e:
        print(f"Failed to decompress tile data: {e}")

def main():
    parser = argparse.ArgumentParser(description='Extract a tile from MBTiles to PBF.')
    parser.add_argument('-i', '--input', required=True, help='Input MBTiles file')
    parser.add_argument('-z', '--zoom', type=int, required=True, help='Zoom level')
    parser.add_argument('-x', '--x', type=int, required=True, help='X coordinate')
    parser.add_argument('-y', '--y', type=int, required=True, help='Y coordinate')
    parser.add_argument('-o', '--output', required=True, help='Output PBF file')
    
    args = parser.parse_args()
    
    extract_tile_to_pbf(args.input, args.zoom, args.x, args.y, args.output)

if __name__ == '__main__':
    main()
