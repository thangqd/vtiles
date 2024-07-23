import mercantile
from shapely.geometry import Polygon, shape, mapping
from shapely.affinity import affine_transform
import sqlite3
import argparse
from .mapbox_vector_tile import encode
import gzip

def tile_to_polygon(tile):
    bbox = mercantile.bounds(tile)
    return Polygon([
        (bbox.west, bbox.south),
        (bbox.west, bbox.north),
        (bbox.east, bbox.north),
        (bbox.east, bbox.south),
        (bbox.west, bbox.south),
    ])

def transform_geometry(geometry, tile_bounds, extent=4096):
    minx, miny, maxx, maxy = tile_bounds
    x_factor = extent / (maxx - minx)
    y_factor = extent / (maxy - miny)
    transform = [x_factor, 0, 0, y_factor, -minx * x_factor, -miny * y_factor]
    return affine_transform(geometry, transform)

def generate_debug_grid_mbtiles(zoom_level, output_file):
    conn = sqlite3.connect(output_file)
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE metadata (name TEXT, value TEXT);
    CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB);
    CREATE UNIQUE INDEX name ON metadata (name);
    CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row);
    """)

    metadata = [
        ("name", "Debug Grid"),
        ("type", "overlay"),
        ("version", "1.0"),
        ("description", "Debug grid for visualizing tile boundaries."),
        ("format", "pbf"),
        # ("bounds", "-180.0,-85.0511,180.0,85.0511"),
        ("minzoom", '0'),
        ("maxzoom", str(zoom_level))
    ]
    cursor.executemany("INSERT INTO metadata (name, value) VALUES (?, ?)", metadata)

    world_bounds = (-180.0, -85.0511, 180.0, 85.0511)
    for tile in mercantile.tiles(world_bounds[0], world_bounds[1], world_bounds[2], world_bounds[3], zoom_level):
        polygon = tile_to_polygon(tile)
        feature = {
            "type": "Feature",
            "geometry": mapping(polygon),
            "properties": {
                "tile_id": f"{tile.z}/{tile.x}/{tile.y}",
                "z": tile.z,
                "x": tile.x,
                "y": tile.y
            }
        }
        feature_collection = {
            "type": "FeatureCollection",
            "features": [feature]
        }

        tile_bounds = mercantile.bounds(tile)
        mvt_features = []
        for feature in feature_collection["features"]:
            geometry = transform_geometry(shape(feature["geometry"]), (tile_bounds.west, tile_bounds.south, tile_bounds.east, tile_bounds.north))
            mvt_features.append({
                "geometry": geometry,
                "properties": feature["properties"]
            })

        mvt_layer = {
            "name": "debug_grid",
            "features": mvt_features
        }

        # print(mvt_layer)
        aaa = [{"name": "water", "features": [{"geometry": "POLYGON((3257.6188764017343 1924.195788997867, 3257.4962116230354 1924.0964889389206, 3257.7263541125944 1924.032235959602, 3257.8957483307977 1924.2682196290993, 3257.65509171735 1924.2623784491611, 3257.65509171735 1924.2623784491611, 3257.6188764017343 1924.195788997867))", "properties": {"name": "1"}}]}]
        tile_data_encoded = encode(aaa)
        print(tile_data_encoded)
        tile_data_encoded_gzipped = gzip.compress(tile_data_encoded)
        tile_column = tile.x
        tile_row = tile.y
        # tile_row = (1 << zoom_level) - 1 - tile.y

        cursor.execute(
            "INSERT INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?)",
            (zoom_level, tile_column, tile_row, tile_data_encoded_gzipped)
        )

    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Generate a debug grid MBTiles file.")
    parser.add_argument("-z", "--zoom", type=int, required=True, help="Zoom level for the debug grid.")
    parser.add_argument("-o", "--output", type=str, required=True, help="Output MBTiles file.")

    args = parser.parse_args()

    generate_debug_grid_mbtiles(args.zoom, args.output)

if __name__ == "__main__":
    main()
