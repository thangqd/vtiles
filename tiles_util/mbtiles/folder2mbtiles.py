import sqlite3, argparse, sys, math, logging, time, os, json
from tqdm import tqdm
logger = logging.getLogger(__name__)
from tiles_util.utils.geopreocessing import flip_y
import tiles_util.utils.mercantile as mercantile

def mbtiles_connect(mbtiles_file):
  try:
    conn = sqlite3.connect(mbtiles_file)
    return conn
  except Exception as e:
    logger.error("Could not connect to MBTiles file")
    logger.exception(e)
    sys.exit(1)

def mbtiles_setup(cursor):
  cursor.execute("""
    create table tiles (
      zoom_level integer,
      tile_column integer,
      tile_row integer,
      tile_data blob);
      """)
  cursor.execute("""create table metadata (name text, value text);""")
  cursor.execute("""create unique index name on metadata (name);""")
  cursor.execute("""create unique index tile_index on tiles(zoom_level, tile_column, tile_row);""")

def import_metadata(cursor, metadata_json):
  for name, value in metadata_json.items():
    cursor.execute('insert into metadata (name, value) values (?, ?)',
                (name, value))

def get_zoom_levels(cursor):   
    # Query to get min and max zoom levels
    cursor.execute('''
        SELECT MIN(zoom_level) AS min_zoom, MAX(zoom_level) AS max_zoom
        FROM tiles
    ''')    
    result = cursor.fetchone()    
    min_zoom = result[0] if result else None
    max_zoom = result[1] if result else None  

    return min_zoom, max_zoom

def get_bounds_at_zoom(cursor, zoom_level):
    # Query tiles at the specified zoom level
    cursor.execute("SELECT tile_column, tile_row FROM tiles WHERE zoom_level = ?", (zoom_level,))
    tiles = cursor.fetchall()

    # Calculate bounding boxes for each tile
    bounds = []
    for tile in tiles:
        x, y = tile
        flip_y = (1 << zoom_level) - 1 - y # TMS scheme
        # Calculate bounds for the given tile coordinates
        tile_bounds = mercantile.bounds(x,flip_y, zoom_level)
        bounds.append(tile_bounds)

    return bounds

def compute_max_bound(bounds):
    # Initialize min and max coordinates with extreme values
    min_lat = min_lon = float('inf')
    max_lat = max_lon = float('-inf')

    for bound in bounds:
        # Unpack bounding box coordinates (west, south, east, north)
        west, south, east, north = bound

        # Update min and max values
        min_lon = min(min_lon, west)
        max_lon = max(max_lon, east)    
        min_lat = min(min_lat, south)
        max_lat = max(max_lat, north)
            
    center_lon = (min_lon + max_lon) / 2
    center_lat = (min_lat + max_lat) / 2

    # Return the overall bounding box
    return min_lon, min_lat, max_lon, max_lat,center_lon,center_lat

def get_bounds_center(cursor):   
    boundsString, centerString = None, None
    try:    
        _,max_zoom = get_zoom_levels(cursor)
        bounds_at_max_zoom = get_bounds_at_zoom(cursor, max_zoom)
        bounds = compute_max_bound(bounds_at_max_zoom)
        boundsString = ','.join(map(str, bounds[:4]))
        centerString = ','.join(map(str, bounds[4:]))+ f',{max_zoom}'     
        return boundsString, centerString
    except Exception as e:
        logging.error(f"Get bounds and center erros: {e}")        
        boundsString = '-180.000000,-85.051129,180.000000,85.051129'
        centerString = '0,0,0'
        return boundsString, centerString


# Create metadata table in case no metadata.json found in the tiles folder
def create_metadata(cursor, name, format, tms=0): 
  try:
    minzoom, maxzoom = get_zoom_levels(cursor)
    bounds, center = get_bounds_center(cursor)
    cursor.executemany("INSERT INTO metadata (name, value) VALUES (?, ?);", [
      ("name", name),
      ("format", format), 
      ("bounds", bounds), 
      ("center", center), 
      ("minzoom", minzoom), 
      ("maxzoom", maxzoom), 
      ("desccription", 'MBTiles converted from a tiles folder using tiles-util'), 
      ("attribution", '<a href="https://github.com/thangqd/tiles_util" target="_blank">&copy; tiles-util</a>'),
      ("type", ''),
      ("version", '1')
    ])
    logger.info('Creating metadata done.')
  except Exception as e:
      print(f"Error creating metadata: {e}")

def optimize_connection(cur):
  cur.execute("""PRAGMA synchronous=0""")
  # cur.execute("""PRAGMA locking_mode=EXCLUSIVE""")
  cur.execute("""PRAGMA journal_mode=DELETE""")

def get_dirs(path):
  return [name for name in os.listdir(path)
    if os.path.isdir(os.path.join(path, name))]

def folder2mbtiles(input_folder, mbtiles_file, tms=0):
  logger.info("Converting folder to MBTiles")
  logger.debug("%s --> %s" % (input_folder, mbtiles_file))
  con = mbtiles_connect(mbtiles_file)
  cur = con.cursor()
  optimize_connection(cur)
  mbtiles_setup(cur)
  metadata_json = os.path.join(input_folder, 'metadata.json')
 
  if os.path.exists(metadata_json):
    metadata = json.load(open(metadata_json, 'r'))
    import_metadata(cur, metadata)
    logger.info('Importing metadata done.')
  else:
    logger.warning('metadata.json not found')

  # count = 0
  # start_time = time.time()
  
  with tqdm(desc="Coverting tiles", unit=" tiles") as pbar:
    for zoom_dir in get_dirs(input_folder):   
      z = int(zoom_dir)
      for row_dir in get_dirs(os.path.join(input_folder, zoom_dir)):
        x = int(row_dir)
        for current_file in os.listdir(os.path.join(input_folder, zoom_dir, row_dir)):
          if current_file == ".DS_Store":
            logger.warning("The .DS_Store file will be ignored.")
          else:
            # file_name, ext = current_file.split('.',1)
            file_name, ext = os.path.splitext(current_file)       
            if ext in ('.png','.jpg','.jpeg','.webp', '.pbf'):
              f = open(os.path.join(input_folder, zoom_dir, row_dir, current_file), 'rb')
              file_content = f.read()
              f.close()
              if tms == 1:
                y = flip_y(int(z), int(file_name))
              else:
                y = int(file_name)
              logger.debug(' Read tile from Zoom (z): %i\tCol (x): %i\tRow (y): %i' % (z, x, y))
              cur.execute("""insert into tiles (zoom_level,
                  tile_column, tile_row, tile_data) values
                  (?, ?, ?, ?);""",
                  # (z, x, y, file_content))
                  (z, x, y, sqlite3.Binary(file_content)))
              pbar.update(1)
              # count = count + 1
              # if (count % 100) == 0:
              #   logger.info(" %s tiles inserted (%d tiles/sec)" % (count, count / (time.time() - start_time)))
  try:
    name = os.path.basename(input_folder)
    create_metadata(cur, name, ext, tms)    
  except:      
    logger.warning('No metadata created!')
  
  cur.close()
  con.commit()
  con.close()
    
  logger.info('Converting Folder to MBTiles done.')


def main():
  logging.basicConfig(level=logging.INFO, format='%(message)s')
  parser = argparse.ArgumentParser(description='Convert Tiles folder to MBTiles')
  parser.add_argument('-i', help='Input folder')
  parser.add_argument('-o', help='Output mbtiles file name (optional)', default=None)
  parser.add_argument('-flipy', help='Use TMS (flip y) format: 1 or 0', type=int, default=0)

  args = parser.parse_args()

  if not args.i:
    print('Please provide the input folder.')
    exit()

  if not os.path.exists(args.i) or not os.path.isdir(args.i):
    print('Input folder does not exist or invalid!. Please recheck and input a correct one.')
    exit()

  input_folder_abspath =  os.path.abspath(args.i)

  if not args.o:    
    output_file_name = os.path.basename(input_folder_abspath) + '.mbtiles' # Get input folder name
    output_file_abspath  = os.path.abspath(output_file_name)  # Get absolute path of default output file name
    if not os.path.exists(output_file_abspath): 
      print(f'Converting folder {input_folder_abspath} to {output_file_abspath}')        
    else: # the output file is already existed.
      print(f'Output MBTiles file {output_file_abspath} already existed! Please recheck and input a correct one. Ex: -o tiles.mbtiles')
      exit()
  
  else:      
    output_file_abspath = os.path.abspath(args.o)
    if output_file_abspath.endswith('mbtiles') and not os.path.exists(output_file_abspath):
      print(f'Converting folder {input_folder_abspath} to {output_file_abspath}')     
    else:
      print(f'Output MBTiles file {output_file_abspath} is not valid or already existed!. Please recheck and input a correct one. Ex: -o tiles.mbtiles')
      exit()
  
  folder2mbtiles(input_folder_abspath, output_file_abspath, args.flipy)

if __name__ == "__main__":
  main()
