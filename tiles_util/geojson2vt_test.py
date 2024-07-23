from geojson2vt.geojson2vt import geojson2vt
from geojson2vt.vt2geojson import vt2geojson
from vt2pbf import vt2pbf
from vt2pbf import parse_from_string
from vt2pbf import Tile


import json
import mercantile
import sqlite3
import os
# from mapboxvectortile import encode, decode

def convert_geojson_to_mbtiles(geojson_file, mbtiles_file):
    # Read GeoJSON data
    with open(geojson_file, 'r') as f:
        geojson_data = json.load(f)

    # Create a vector tile source
    vt_layer = geojson2vt(
        geojson_data,
        {
            'maxZoom': 6,
            'extent': 4096,
            'buffer': 256,
            'debug': 0
        }
    )
    # print(vt_layer.get_tile(0,0,0))
    # # Create or open MBTiles database
    # if os.path.exists(mbtiles_file):
    #     os.remove(mbtiles_file)
    
    # conn = sqlite3.connect(mbtiles_file)
    # c = conn.cursor()

    # # Create the MBTiles schema
    # c.execute('''CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB, PRIMARY KEY (zoom_level, tile_column, tile_row))''')
    # c.execute('''CREATE TABLE metadata (name TEXT, value TEXT)''')
    # metadata = {
    #     'name': 'Example MBTiles',
    #     'description': 'Example MBTiles created from GeoJSON',
    #     'version': '1.0',
    #     'type': 'overlay'
    # }
    # for key, value in metadata.items():
    #     c.execute('INSERT INTO metadata (name, value) VALUES (?, ?)', (key, value))

    # # Add tiles to MBTiles database
    # for z in range(0, 7):
    #     for x in range(0, 2**z):
    #         for y in range(0, 2**z):
    #             tile_key = mercantile.tile(x, y, z)
    #             tile_data = vt_layer.get_tile(z, x, y)
    #             print(tile_data)
    #             if tile_data:
    #                 c.execute('INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)',
    #                           (z, x, y, encode(tile_data)))

    # conn.commit()
    # conn.close()

# Usage
# build an initial index of tiles
with open('./data/polygon.geojson', 'r') as f:
    geojson_data = json.load(f)
# print(geojson_data)

tile_index = geojson2vt(geojson_data,{})
# print('#### tile_index:', tile_index)
# get a specific tile
vector_tile  = tile_index.get_tile(0, 0, 0)
# encoded = encode(tile)
# print (encoded)
print('#### vector_tile:', vector_tile)
pbf = vt2pbf(vector_tile)
print('encoded:', pbf)
tile = parse_from_string(pbf)
print(tile)

# convert a specific vector tile to GeoJSON
# geojson = vt2geojson(vector_tile)
# print('#### geojson:', geojson)
# convert a specific
# convert_geojson_to_mbtiles('./data/polygon.geojson', './data/polygon.mbtiles')
# decoded = b'\n\x11vector_tile.proto\x12\x0bvector_tile\"\xbd\x04\n\x04tile\x12\'\n\x06layers\x18\x03 \x03(\x0b\x32\x17.vector_tile.tile.layer\x1a\xa1\x01\n\x05value\x12\x14\n\x0cstring_value\x18\x01 \x01(\t\x12\x13\n\x0b\x66loat_value\x18\x02 \x01(\x02\x12\x14\n\x0c\x64ouble_value\x18\x03 \x01(\x01\x12\x11\n\tint_value\x18\x04 \x01(\x03\x12\x12\n\nuint_value\x18\x05 \x01(\x04\x12\x12\n\nsint_value\x18\x06 \x01(\x12\x12\x12\n\nbool_value\x18\x07 \x01(\x08*\x08\x08\x08\x10\x80\x80\x80\x80\x02\x1ap\n\x07\x66\x65\x61ture\x12\n\n\x02id\x18\x01 \x01(\x04\x12\x10\n\x04tags\x18\x02 \x03(\rB\x02\x10\x01\x12\x31\n\x04type\x18\x03 \x01(\x0e\x32\x1a.vector_tile.tile.GeomType:\x07Unknown\x12\x14\n\x08geometry\x18\x04 \x03(\rB\x02\x10\x01\x1a\xad\x01\n\x05layer\x12\x12\n\x07version\x18\x0f \x02(\r:\x01\x31\x12\x0c\n\x04name\x18\x01 \x02(\t\x12+\n\x08\x66\x65\x61tures\x18\x02 \x03(\x0b\x32\x19.vector_tile.tile.feature\x12\x0c\n\x04keys\x18\x03 \x03(\t\x12\'\n\x06values\x18\x04 \x03(\x0b\x32\x17.vector_tile.tile.value\x12\x14\n\x06\x65xtent\x18\x05 \x01(\r:\x04\x34\x30\x39\x36*\x08\x08\x10\x10\x80\x80\x80\x80\x02\"?\n\x08GeomType\x12\x0b\n\x07Unknown\x10\x00\x12\t\n\x05Point\x10\x01\x12\x0e\n\nLineString\x10\x02\x12\x0b\n\x07Polygon\x10\x03*\x05\x08\x10\x10\x80@B\x02H\x03'
# print (decode(decoded))

tile = Tile(extend=4096)
tile.add_layer('a', features=vector_tile['features'])  # features in vector_tile format (close to vector_tile['features'])
tile.add_layer('b', features=vector_tile['features'])
pbf_string = tile.serialize_to_bytestring()
print(pbf_string)