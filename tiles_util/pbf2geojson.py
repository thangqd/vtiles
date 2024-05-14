# https://python.plainenglish.io/debugging-mbtiles-in-python-8f4db8fbeacc
import sqlite3

# connect to tiles
MBTILES = "/data/yemen.mbtiles"
con = sqlite3.connect(MBTILES)
cursor = con.cursor()

# tile coordinates
zoom = 0
col = 0
row = 0

cursor.execute(
    """SELECT tile_data FROM tiles 
    WHERE zoom_level=:zoom 
    AND tile_column=:column AND tile_row=:row;""",
    {"zoom": zoom, "column": col, "row": row},
)
data = cursor.fetchall()
tile_data = data[0][0]

import gzip
from io import BytesIO
import mapbox_vector_tile as mvt

raw_data = BytesIO(tile_data)

with gzip.open(raw_data, "rb") as f:
 tile = f.read()
decoded_data = mvt.decode(tile)
