# Reference: 
# https://github.com/mapbox/mbtiles-spec/blob/master/1.3/spec.md
# https://github.com/mapbox/tippecanoe/blob/master/main.cpp#L2033

import sqlite3
import os, sys
import logging
from vtiles.utils.geopreocessing import check_vector, determine_tileformat, get_zoom_levels,get_bounds_center
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_vectormetadata(input_mbtiles, compression_type, desc):
    conn = sqlite3.connect(input_mbtiles)       
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS metadata (name TEXT, value TEXT);')
    cursor.execute('create unique index IF NOT EXISTS name on metadata (name);')    

    # Update name and description
    name = os.path.basename(input_mbtiles)
    cursor.execute("INSERT OR IGNORE INTO metadata (name, value) VALUES (?, ?)", ('name', name))
    
    cursor.execute("INSERT OR IGNORE INTO metadata (name, value) VALUES (?, ?)", ('description', desc))

    # Update format to pbf 
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
    # logger.info(f'Fix metadata for {name} done!')

def fix_rastermetadata(input_mbtiles, format,desc):
    conn = sqlite3.connect(input_mbtiles)       
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS metadata (name TEXT, value TEXT);')
    cursor.execute('create unique index IF NOT EXISTS name on metadata (name);')    

    # Update name and description
    name = os.path.basename(input_mbtiles)
    cursor.execute("INSERT OR IGNORE INTO metadata (name, value) VALUES (?, ?)", ('name', name))
    cursor.execute("INSERT OR IGNORE INTO metadata (name, value) VALUES (?, ?)", ('description', desc))
   
    # Update format to raster
    cursor.execute("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", ('format',format))

  
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

def main():
    if len(sys.argv) != 2:
      logger.error("Please provide the MBTiles input filename.")
      sys.exit(1)
    input_mbtiles = sys.argv[1]
    
    if (os.path.exists(input_mbtiles)):
        is_vector, compression_type = check_vector(input_mbtiles) 
        tile_format = determine_tileformat(input_mbtiles)
        desc = 'Update metadata by vtiles.mbtiles.mbtilesfixmeta' 
        if is_vector:
            fix_vectormetadata(input_mbtiles, compression_type,desc)   
        else:
            fix_rastermetadata(input_mbtiles, tile_format,desc)        
    else: 
        logger.error ('MBTiles file does not exist!. Please recheck and input a correct file path.')
        sys.exit(1)

if __name__ == "__main__":
    main()
