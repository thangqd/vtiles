# Reference: 
# https://github.com/mapbox/mbtiles-spec/blob/master/1.3/spec.md
# https://github.com/mapbox/tippecanoe/blob/master/main.cpp#L2033

import sqlite3
import os, sys
import logging
from tiles_util.utils.geopreocessing import check_vector, get_zoom_levels,get_bounds_center
logging.basicConfig(level=logging.INFO)


def fix_metadata(input_mbtiles, compression_type):
    conn = sqlite3.connect(input_mbtiles)       
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS metadata (name TEXT, value TEXT);')
    cursor.execute('create unique index IF NOT EXISTS name on metadata (name);')    

    # Update name and description
    name = os.path.basename(input_mbtiles)
    cursor.execute("INSERT OR IGNORE INTO metadata (name, value) VALUES (?, ?)", ('name', name))
    desc = 'Update metadata by tiles_util.mbtilesfixmeta'
    cursor.execute("INSERT OR IGNORE INTO metadata (name, value) VALUES (?, ?)", ('description', desc))

    # Update format to pbf for vector MBTiles
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('format', 'pbf'))
   
    # Update compression
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('compression', compression_type))
    
    # Update min zoom, max zoom
    min_zoom, max_zoom = get_zoom_levels(input_mbtiles)
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('minzoom', min_zoom))
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('maxzoom', max_zoom))

    # Update bounds and center
    bounds, center = get_bounds_center(input_mbtiles)
    if bounds:
        cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('bounds', bounds))
    if center:
        cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('center', center))
    conn.commit()
    conn.close() 
    print('Fix metadata done!')

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
