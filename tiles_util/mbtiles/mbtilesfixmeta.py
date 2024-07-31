# Reference: 
# https://github.com/mapbox/mbtiles-spec/blob/master/1.3/spec.md
# https://github.com/mapbox/tippecanoe/blob/master/main.cpp#L2033

import sqlite3
import os, sys
import zlib, gzip
from tiles_util.utils.mapbox_vector_tile import decode
import logging

logging.basicConfig(level=logging.INFO)

# Check if mbtiles is vector
def check_vector(input_mbtiles):    
    try: 
        conn = sqlite3.connect(input_mbtiles)
        cursor = conn.cursor()
        cursor.execute("SELECT tile_data FROM tiles LIMIT 1")
        tile_data = cursor.fetchone()[0]
        compression_type = ''
        if tile_data[:2] == b'\x1f\x8b':
            compression_type = 'GZIP'
            tile_data = gzip.decompress(tile_data)
        elif tile_data[:2] == b'\x78\x9c' or tile_data[:2] == b'\x78\x01' or tile_data[:2] == b'\x78\xda':
            compression_type = 'ZLIB'
            tile_data = zlib.decompress(tile_data)
        decode(tile_data)
        conn.close()
        return True, compression_type
    except:
        conn.close()
        return False, compression_type

def get_zoom_levels(input_mbtiles):
    conn = sqlite3.connect(input_mbtiles)
    cursor = conn.cursor()
    
    # Query to get min and max zoom levels
    cursor.execute('''
        SELECT MIN(zoom_level) AS min_zoom, MAX(zoom_level) AS max_zoom
        FROM tiles
    ''')
    
    result = cursor.fetchone()    
    conn.close()    
    min_zoom = result[0] if result else None
    max_zoom = result[1] if result else None  

    return min_zoom, max_zoom

def get_center_of_bound(bounds_str):
    try:
        # Split the string into individual coordinates
        coords = [float(coord) for coord in bounds_str.split(',')]
        if len(coords) == 4:
            lon1, lat1, lon2, lat2 = coords
            # Calculate the center of the bounding box
            center_lon = (lon1 + lon2) / 2
            center_lat = (lat1 + lat2) / 2
            # Return the center as a formatted string
            return f"{center_lon},{center_lat}"
        else:
            raise ValueError("Invalid bounds string format")
    except Exception as e:
        logging.error(f"Get center of bound error: {e}")
        return ''
    
def fix_metadata(input_mbtiles, compression_type):
    conn = sqlite3.connect(input_mbtiles)       
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS metadata (name TEXT, value TEXT);')
    cursor.execute('create unique index IF NOT EXISTS name on metadata (name);')    

    # Update format to pbf for vector MBTiles
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('format', 'pbf'))
   
    # Update compression
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('compression', compression_type))
    
    # Update min zoom, max zoom
    min_zoom, max_zoom = get_zoom_levels(input_mbtiles)
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('minzoom', min_zoom))
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('maxzoom', max_zoom))

    # Update bounds
    max_bound = '-180.000000,-85.051129,180.000000,85.051129'
    cursor.execute("INSERT OR IGNORE INTO metadata (name, value) VALUES (?, ?)", ('bounds', max_bound))
    conn.commit()

    # Update center
    cursor.execute("SELECT value FROM metadata WHERE name = 'bounds'")
    bound = cursor.fetchone()[0]  
    center = get_center_of_bound(bound)    
    center_of_bound = ''

    if center != '':
        center_of_bound = center +f',{max_zoom}'
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('center', center_of_bound))
    
    conn.commit()
    conn.close() 
    
def main():
    if len(sys.argv) != 2:
      print("Please provide the MBTiles input filename.")
      return
    input_mbtiles = sys.argv[1]
    if (os.path.exists(input_mbtiles)):
        is_vector, compression_type = check_vector(input_mbtiles) 
        if is_vector:
            fix_metadata(input_mbtiles, compression_type)           
    else: 
        print ('MBTiles file does not exist!. Please recheck and input a correct file path.')
        return

if __name__ == "__main__":
    main()
