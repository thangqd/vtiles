import argparse
import gzip
from vtiles.utils.pmtiles.writer import write
from vtiles.utils.pmtiles.tile import TileType, zxy_to_tileid, tileid_to_zxy, Compression
import sqlite3
from tqdm import tqdm

def mbtiles_to_header_json(mbtiles_metadata):
    header = {}

    header["min_zoom"] = int(mbtiles_metadata["minzoom"])

    header["max_zoom"] = int(mbtiles_metadata["maxzoom"])

    bounds = mbtiles_metadata["bounds"].split(",")
    header["min_lon_e7"] = int(float(bounds[0]) * 10000000)
    header["min_lat_e7"] = int(float(bounds[1]) * 10000000)
    header["max_lon_e7"] = int(float(bounds[2]) * 10000000)
    header["max_lat_e7"] = int(float(bounds[3]) * 10000000)

    center = mbtiles_metadata["center"].split(",")
    header["center_lon_e7"] = int(float(center[0]) * 10000000)
    header["center_lat_e7"] = int(float(center[1]) * 10000000)
    header["center_zoom"] = int(center[2])

    tile_format = mbtiles_metadata["format"]
    if tile_format == "pbf":
        header["tile_type"] = TileType.MVT
    elif tile_format == "png":
        header["tile_type"] = TileType.PNG
    elif tile_format == "jpeg":
        header["tile_type"] = TileType.JPEG
    elif tile_format == "webp":
        header["tile_type"] = TileType.WEBP
    elif tile_format == "avif":
        header["tile_type"] = TileType.AVIF
    else:
        header["tile_type"] = TileType.UNKNOWN

    if tile_format == "pbf" or mbtiles_metadata.get("compression") == "gzip":
        header["tile_compression"] = Compression.GZIP
    else:
        header["tile_compression"] = Compression.NONE

    return header, mbtiles_metadata

def mbtiles_to_pmtiles(input, output, maxzoom=None):
    conn = sqlite3.connect(input)
    cursor = conn.cursor()

    with write(output) as writer:
        # collect a set of all tile IDs
        tileid_set = []
        for row in cursor.execute(
            "SELECT zoom_level,tile_column,tile_row FROM tiles WHERE zoom_level <= ?",
            (maxzoom or 99,),
        ):
            flipped = (1 << row[0]) - 1 - row[2]
            tileid_set.append(zxy_to_tileid(row[0], row[1], flipped))

        tileid_set.sort()

        mbtiles_metadata = {}
        for row in cursor.execute("SELECT name,value FROM metadata"):
            mbtiles_metadata[row[0]] = row[1]
        is_pbf = mbtiles_metadata["format"] == "pbf"

        # query the db in ascending tile order
        for tileid in tqdm(tileid_set, desc="Converting tiles"):
            z, x, y = tileid_to_zxy(tileid)
            flipped = (1 << z) - 1 - y
            res = cursor.execute(
                "SELECT tile_data FROM tiles WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?",
                (z, x, flipped),
            )
            data = res.fetchone()[0]
            # force gzip compression only for vector
            if is_pbf and data[0:2] != b"\x1f\x8b":
                data = gzip.compress(data)
            writer.write_tile(tileid, data)

        pmtiles_header, pmtiles_metadata = mbtiles_to_header_json(mbtiles_metadata)
        if maxzoom:
            pmtiles_header["max_zoom"] = int(maxzoom)
            mbtiles_metadata["maxzoom"] = maxzoom
        result = writer.finalize(pmtiles_header, pmtiles_metadata)

    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Convert MBTiles to PMTiles.")
    parser.add_argument("-i", "--input", required=True, help="Input MBTiles file path.")
    parser.add_argument("-o", "--output", required=True, help="Output PMTiles file path.")
    parser.add_argument("-z", "--maxzoom", type=int, help="Maximum zoom level to process.")
    args = parser.parse_args()

    mbtiles_to_pmtiles(args.input, args.output, args.maxzoom)

if __name__ == "__main__":
    main()
