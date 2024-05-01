import sqlite3, argparse, sys, logging, time, os, json
from tqdm import tqdm

logger = logging.getLogger(__name__)

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

def import_metadata(con, cur, metadata_json):
  for name, value in metadata_json.items():
    cur.execute('insert into metadata (name, value) values (?, ?)',
                (name, value))
    

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
  try:
    metadata = json.load(open(os.path.join(input_folder, 'metadata.json'), 'r'))
    import_metadata(con, cur, metadata)
    logger.info('importing metadata done.')
  except IOError:      
    logger.warning('metadata.json not found')

  count = 0
  start_time = time.time()
  total_files = sum(len(files) for _, _, files in os.walk(input_folder))
  with tqdm(total=total_files, desc="Coverting", unit="file") as pbar:
    for zoom_dir in get_dirs(input_folder):   
      z = int(zoom_dir)
      for row_dir in get_dirs(os.path.join(input_folder, zoom_dir)):
        x = int(row_dir)
        for current_file in os.listdir(os.path.join(input_folder, zoom_dir, row_dir)):
          if current_file == ".DS_Store":
            logger.warning("The .DS_Store file will be ignored.")
          else:
            file_name, ext = current_file.split('.',1)
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
                (z, x, y, sqlite3.Binary(file_content)))
            pbar.update(1)
            # count = count + 1
            # if (count % 100) == 0:
            #   logger.info(" %s tiles inserted (%d tiles/sec)" % (count, count / (time.time() - start_time)))
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

  if not os.path.isdir(args.i):
    print('Input folder does not exist!. Please recheck and input a correct one.')
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
