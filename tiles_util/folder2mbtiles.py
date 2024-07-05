import sqlite3, argparse, sys, math, logging, time, os, json
from tqdm import tqdm
logger = logging.getLogger(__name__)

def num2deg(xtile, ytile, zoom):
		n = 2.0 ** zoom
		lon_deg = xtile / n * 360.0 - 180.0
		lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
		lat_deg = math.degrees(lat_rad)
		return (lat_deg, lon_deg)

def flip_y(zoom, y):
  return (2**zoom-1) - y

def mbtiles_connect(mbtiles_file):
  try:
    con = sqlite3.connect(mbtiles_file)
    return con
  except Exception as e:
    logger.error("Could not connect to MBTiles file")
    logger.exception(e)
    sys.exit(1)

def mbtiles_setup(cur):
  cur.execute("""
    create table tiles (
      zoom_level integer,
      tile_column integer,
      tile_row integer,
      tile_data blob);
      """)
  cur.execute("""create table metadata (name text, value text);""")
  cur.execute("""CREATE TABLE grids (zoom_level integer, tile_column integer,
              tile_row integer, grid blob);""")
  cur.execute("""CREATE TABLE grid_data (zoom_level integer, tile_column
              integer, tile_row integer, key_name text, key_json text);""")
  cur.execute("""create unique index name on metadata (name);""")
  cur.execute("""create unique index tile_index on tiles
              (zoom_level, tile_column, tile_row);""")

def import_metadata(cur, metadata_json):
  for name, value in metadata_json.items():
    cur.execute('insert into metadata (name, value) values (?, ?)',
                (name, value))

# Create metadata table in case no metadata.json found in the tiles folder
def create_metadata(cur, name, format, tms=0):      
  cur.execute("SELECT min(zoom_level) FROM tiles")
  minzoom = cur.fetchone()[0]
  # Execute SQL query to find the maximum value
  cur.execute("SELECT max(zoom_level) FROM tiles")
  maxzoom = cur.fetchone()[0]

  cur.execute("SELECT min(tile_row), max(tile_row), min(tile_column), max(tile_column) from tiles WHERE zoom_level = ?", [maxzoom])

  minY, maxY, minX, maxX = cur.fetchone()
  if tms == 1:
    minY = (2 ** maxzoom) - minY - 1
    maxY = (2 ** maxzoom) - maxY - 1

  minLat, minLon = num2deg(minX, minY, maxzoom)
  maxLat, maxLon = num2deg(maxX+1, maxY+1, maxzoom)

  bounds = [minLon, minLat, maxLon, maxLat]
  boundsString = ','.join(map(str, bounds))

  center = [(minLon + maxLon)/2, (minLat + maxLat)/2, maxzoom]
  centerString = ','.join(map(str, center))

  cur.executemany("INSERT INTO metadata (name, value) VALUES (?, ?);", [
  ("name", name),
  ("format", format), 
  ("bounds", boundsString), 
  ("center", centerString), 
  ("minzoom", minzoom), 
  ("maxzoom", maxzoom), 
  ("desccription", 'MBTiles converted from a tiles folder using tiles-util'), 
  ("attribution", '<a href="https://github.com/thangqd/tiles_util" target="_blank">&copy; tiles-util</a>'),
  ("type", ''),
  ("version", '')
])

def optimize_connection(cur):
  cur.execute("""PRAGMA synchronous=0""")
  cur.execute("""PRAGMA locking_mode=EXCLUSIVE""")
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
  total_tiles = sum(len(files) for _, _, files in os.walk(input_folder))
  
  if os.path.exists(metadata_json):
    metadata = json.load(open(metadata_json, 'r'))
    total_tiles = total_tiles - 1 
    import_metadata(cur, metadata)
    logger.info('Importing metadata done.')
  else:
    logger.warning('metadata.json not found')

  # count = 0
  # start_time = time.time()
  
  with tqdm(total=total_tiles, desc="Coverting", unit="file") as pbar:
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
    logger.info('Creating metadata done.')
  except:      
    logger.warning('No metadata created!.')
  
  cur.close()
  con.commit()
  con.close()
    
  logger.info('Converting Folder to MBTiles done.')


def main():
  logging.basicConfig(level=logging.INFO, format='%(message)s')
  parser = argparse.ArgumentParser(description='Convert Tiles folder to MBTiles')
  parser.add_argument('-i', help='Input folder')
  parser.add_argument('-o', help='Output mbtiles file name (optional)', default=None)
  parser.add_argument('-tms', help='Use TMS (flip y) format: 1 or 0', type=int, default=0)

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
  
  folder2mbtiles(input_folder_abspath, output_file_abspath, args.tms)

if __name__ == "__main__":
  main()
