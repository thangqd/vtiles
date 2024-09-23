import os
import shutil
import sqlite3
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def remove_duplicates(input_mbtiles, output_mbtiles):
    # Check if the output file exists and remove it
    if os.path.exists(output_mbtiles):
        os.remove(output_mbtiles)
        logging.info(f"Removed existing output file: {output_mbtiles}")

    # Copy the original MBTiles file to the output path
    shutil.copyfile(input_mbtiles, output_mbtiles)
    logging.info(f"Copied input file to output: {input_mbtiles} -> {output_mbtiles}")

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
        logging.info("Removing duplicates from the 'temp_tiles' table...")

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
        logging.info("Duplicates removed and 'tiles' table updated successfully.")

    except sqlite3.Error as e:
        logging.error(f"An error occurred: {e}")
    finally:
        # Close the connection
        conn.close()

def main():
    # Create argument parser inside the main function
    parser = argparse.ArgumentParser(description="Remove duplicate tiles from an MBTiles file.")
    parser.add_argument('-i', '--input', required=True, help="Input MBTiles file")
    parser.add_argument('-o', '--output', required=True, help="Output MBTiles file")

    # Parse the command-line arguments
    args = parser.parse_args()

    # Show progress for copying the file
    logging.info("Starting to remove duplicates...")
    remove_duplicates(args.input, args.output)
    logging.info("Processing complete.")

if __name__ == '__main__':
    main()
