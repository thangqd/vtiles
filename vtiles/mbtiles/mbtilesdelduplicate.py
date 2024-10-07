import argparse, sys, os
import shutil
import sqlite3
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def remove_duplicates(input_mbtiles, output_mbtiles):
    # Copy the original MBTiles file to the output path
    shutil.copyfile(input_mbtiles, output_mbtiles)
    conn = sqlite3.connect(output_mbtiles)
    cursor = conn.cursor()

    try:
        # Check if 'tiles' is a view
        cursor.execute("SELECT type FROM sqlite_master WHERE name = 'tiles'")
        result = cursor.fetchone()

        if result and result[0] == 'view':
            logging.info("'tiles' is a view. Converting to a table...")

            # Step 1: Create a temporary table from the view
            cursor.execute("CREATE TABLE IF NOT EXISTS temp_tiles AS SELECT * FROM tiles")
            cursor.execute("DROP VIEW IF EXISTS tiles")
        else:
            logging.info("'tiles' is a table. Proceeding with the table directly.")
            cursor.execute("ALTER TABLE tiles RENAME TO temp_tiles")

        # Step 2: Remove duplicates by keeping only the first occurrence
        logger.info("Removing duplicates from the 'temp_tiles' table...")

        # Create a new table to store unique rows
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clean_tiles AS 
            SELECT zoom_level, tile_column, tile_row, tile_data 
            FROM temp_tiles
            GROUP BY zoom_level, tile_column, tile_row
        """)

        # Drop the temporary table with duplicates
        cursor.execute("DROP TABLE IF EXISTS temp_tiles")

        # Rename the clean table to 'tiles'
        cursor.execute("ALTER TABLE clean_tiles RENAME TO tiles")

        # Add a unique index to prevent future duplicates
        cursor.execute("""
            CREATE UNIQUE INDEX tile_index
            ON tiles(zoom_level, tile_column, tile_row)
        """)

        # Commit the changes
        conn.commit()
        logger.info("Duplicates removed and 'tiles' table updated successfully.")

    except sqlite3.Error as e:
        logger.error(f"An error occurred: {e}")
    finally:
        # Close the connection
        conn.close()

def main():
    # Create argument parser inside the main function
    parser = argparse.ArgumentParser(description="Remove duplicate tiles from an MBTiles file.")
    parser.add_argument('input', help='Path to the input MBTiles file.')
    parser.add_argument('-o', '--output', help='Path to the output MBTiles file.')

    args = parser.parse_args()
    if not os.path.exists(args.input):
        logging.error('Input MBTiles file does not exist! Please recheck and input a correct file path.')
        sys.exit(1)
        
    input_file_abspath = os.path.abspath(args.input)
    # Determine the output filename
    if args.output:
        output_file_abspath = os.path.abspath(args.output)
        if os.path.exists(output_file_abspath):
            logger.error(f'Output MBTiles file {output_file_abspath} already exists!. Please recheck and input a correct one. Ex: -o tiles.mbtiles')
            sys.exit(1)
        elif not output_file_abspath.endswith('mbtiles'):
            logger.error(f'Output MBTiles file {output_file_abspath} must end with .mbtiles. Please recheck and input a correct one. Ex: -o tiles.mbtiles')
            sys.exit(1)
    else:
        output_file_name = os.path.basename(input_file_abspath).replace('.mbtiles', '_delduplicate.mbtiles')
        output_file_abspath = os.path.join(os.path.dirname(input_file_abspath), output_file_name)
 
        if os.path.exists(output_file_abspath): 
            logger.error(f'Output MBTiles file {output_file_abspath} already exists! Please recheck and input a correct one. Ex: -o tiles.mbtiles')
            sys.exit(1)          

    logging.info(f'Starting to remove duplicates in {input_file_abspath} and save to {output_file_abspath}.') 
    remove_duplicates(input_file_abspath, output_file_abspath)
    logging.info("Processing complete.")

if __name__ == '__main__':
    main()
