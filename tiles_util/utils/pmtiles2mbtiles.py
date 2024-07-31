import argparse
import json
from .pmtiles.reader import Reader, MmapSource, all_tiles
from .pmtiles.tile import TileType
import sqlite3
from tqdm import tqdm

def pmtiles_to_mbtiles(input, output):
    conn = sqlite3.connect(output)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE metadata (name text, value text);")
    cursor.execute("""create unique index name on metadata (name);""")
    cursor.execute(
        "CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob);"
    )
    cursor.execute(
        "CREATE UNIQUE INDEX tile_index on tiles (zoom_level, tile_column, tile_row);"
    )

    with open(input, "r+b") as f:
        source = MmapSource(f)

        reader = Reader(source)
        header = reader.header()
        metadata = reader.metadata()

        # Set default metadata if not present
        metadata.setdefault("minzoom", header["min_zoom"])
        metadata.setdefault("maxzoom", header["max_zoom"])

        if "bounds" not in metadata:
            min_lon = header["min_lon_e7"] / 10000000
            min_lat = header["min_lat_e7"] / 10000000
            max_lon = header["max_lon_e7"] / 10000000
            max_lat = header["max_lat_e7"] / 10000000
            metadata["bounds"] = f"{min_lon},{min_lat},{max_lon},{max_lat}"

        if "center" not in metadata:
            center_lon = header["center_lon_e7"] / 10000000
            center_lat = header["center_lat_e7"] / 10000000
            center_zoom = header["center_zoom"]
            metadata["center"] = f"{center_lon},{center_lat},{center_zoom}"

        if "format" not in metadata and header["tile_type"] == TileType.MVT:
            metadata["format"] = "pbf"

        json_metadata = {}
        for k, v in metadata.items():
            if k in ["vector_layers", "tilestats"]:
                json_metadata[k] = v
                continue
            elif not isinstance(v, str):
                v = json.dumps(v, ensure_ascii=False)
            cursor.execute("INSERT INTO metadata VALUES(?,?)", (k, v))

        if json_metadata:
            cursor.execute(
                "INSERT INTO metadata VALUES(?,?)",
                ("json", json.dumps(json_metadata, ensure_ascii=False)),
            )

        tile_count = sum(1 for _ in all_tiles(source))
        for zxy, tile_data in tqdm(all_tiles(source), total=tile_count, desc="Converting tiles"):
            flipped_y = (1 << zxy[0]) - 1 - zxy[2]
            cursor.execute(
                "INSERT INTO tiles VALUES(?,?,?,?)",
                (zxy[0], zxy[1], flipped_y, tile_data),
            )

    
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Convert PMTiles to MBTiles.")
    parser.add_argument("-i", "--input", required=True, help="Input PMTiles file path.")
    parser.add_argument("-o", "--output", required=True, help="Output MBTiles file path.")
    args = parser.parse_args()

    pmtiles_to_mbtiles(args.input, args.output)

if __name__ == "__main__":
    main()
