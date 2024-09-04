import json, math
import argparse
from vtiles.utils.mapbox_vector_tile import encode
import vtiles.utils.mercantile as mercantile
import sqlite3
from shapely.geometry import shape, mapping
from shapely.ops import transform
from shapely.wkt import dumps as wkt_dumps
import gzip
from vtiles.mbtiles import mbtilesfixmeta
import pyproj

def create_mbtiles(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE metadata (name TEXT, value TEXT);')
    cursor.execute('CREATE UNIQUE INDEX name on metadata (name);')
    cursor.execute('CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB);')
    cursor.execute('CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row);')
    conn.commit()
    conn.close()

def geojson_to_custom_format(geojson):
    layer_name = geojson.get('name', 'geojson_layer')
    layers = {}
    # Process each feature
    for feature in geojson['features']:
        if layer_name not in layers:
            layers[layer_name] = []

        # Convert GeoJSON feature geometry to WKT format
        geom = shape(feature['geometry'])  # Convert GeoJSON to Shapely geometry
        geom_wkt = wkt_dumps(geom)  # Convert Shapely geometry to WKT

        # Prepare feature dictionary
        feature_dict = {
            "geometry": geom_wkt,
            "properties": feature["properties"]
        }

        # Add feature to the appropriate layer
        layers[layer_name].append(feature_dict)

    # Convert layers dictionary to the desired format
    formatted_layers = [
        {
            "name": layer_name,
            "features": features
        }
        for layer_name, features in layers.items()
    ]
    return formatted_layers

# def reproject_geojson_to_tile_extent(geojson_data, tile_x, tile_y, zoom, tile_size=4096):
#     # Get the bounds of the specified tile
#     tile_bounds = mercantile.bounds(tile_x, tile_y, zoom)

#     # Calculate scale factors
#     minx, miny, maxx, maxy = tile_bounds
#     scale_x = tile_size / (maxx - minx)
#     scale_y = tile_size / (maxy - miny)

#     def scale_coords(x, y, z=None):
#         return (x - minx) * scale_x, (y - miny) * scale_y

#     # Convert and scale features
#     reprojected_features = []
#     for feature in geojson_data["features"]:
#         geometry = shape(feature["geometry"])
#         scaled_geometry = transform(scale_coords, geometry)
#         reprojected_features.append({
#             "type": "Feature",
#             "properties": feature["properties"],
#             "geometry": mapping(scaled_geometry)
#         })

#     # Create the new GeoJSON structure
#     reprojected_geojson = {
#         "type": "FeatureCollection",
#         "name": geojson_data.get("name", "reprojected_geojson"),
#         "crs": geojson_data.get("crs"),
#         "features": reprojected_features
#     }

#     return reprojected_geojson

def reproject_geojson_to_tile_extent(geojson_data, tile_x, tile_y, zoom, tile_size=4096):
    # Define the projections
    proj_wgs84 = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    proj_web_mercator = pyproj.Transformer.from_crs("EPSG:3857", "EPSG:3857", always_xy=True)

    # Get the bounds of the specified tile in Web Mercator coordinates
    tile_bounds = mercantile.xy_bounds(tile_x, tile_y, zoom)
    # tile_bounds = mercantile.bounds(tile_x, tile_y, zoom)

    # Calculate scale factors
    minx, miny, maxx, maxy = tile_bounds
    if maxx == minx or maxy == miny:
        raise ValueError("Invalid tile bounds: zero-width or zero-height tile")
    scale_x = tile_size / (maxx - minx)
    scale_y = tile_size / (maxy - miny)

    # Define the transformation functions
    def reproject_geom(geometry):
        return transform(lambda x, y: proj_wgs84.transform(x, y), geometry)

    def scale_coords(x, y, z=None):
        x_scaled = (x - minx) * scale_x
        # y_scaled = tile_size - (y - miny) * scale_y  # Flip y-axis
        y_scaled = (y - miny) * scale_y   
        return x_scaled, y_scaled
        

    def scale_geom(geometry):
        # return transform(lambda x, y: scale_coords(x, y), geometry)
        return transform(lambda x, y: scale_coords(x, y), geometry)

    # Reproject and scale features
    reprojected_features = []
    for feature in geojson_data["features"]:
        geometry = shape(feature["geometry"])
        
        # Reproject from WGS84 to Web Mercator
        reprojected_geometry = reproject_geom(geometry)
        
        # Scale the reprojected geometry to tile extent
        scaled_geometry = scale_geom(reprojected_geometry)
        
        # Store the reprojected geometry
        reprojected_features.append({
            "type": "Feature",
            "properties": feature["properties"],
            "geometry": mapping(scaled_geometry)
        })

    # Create the new GeoJSON structure
    reprojected_geojson = {
        "type": "FeatureCollection",
        "name": geojson_data.get("name", "reprojected_geojson"),
        "crs": geojson_data.get("crs"),
        "features": reprojected_features
    }

    return reprojected_geojson

def add_tile_to_mbtiles(db_path, z, x, y, tile_data):
    """Add a tile to the MBTiles database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO tiles (zoom_level, tile_column, tile_row, tile_data) VALUES (?, ?, ?, ?);', (z, x, y, tile_data))
    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Convert GeoJSON to MBTiles.")
    parser.add_argument('-i', '--input', required=True, help="Input GeoJSON file.")
    parser.add_argument('-o', '--output', required=True, help="Output MBTiles file.")
    parser.add_argument('-z', '--zoom', type=int, default=0, help="Zoom level for the tile.")
    parser.add_argument('-x', '--x', type=int, default=0, help="Tile column.")
    parser.add_argument('-y', '--y', type=int, default=0, help="Tile row.")
    args = parser.parse_args()

    # Read the input GeoJSON file
    with open(args.input, 'r',encoding='utf-8') as f:
        geojson_data = json.load(f)

    # Define tile coordinates
    z, x, y = args.zoom, args.x, args.y

    # Create MBTiles file
    create_mbtiles(args.output)
    
    geojson_reprojected = reproject_geojson_to_tile_extent(geojson_data,z, x, y)
    # print (geojson_reprojected)
    geojson_reprojected_processed = geojson_to_custom_format(geojson_reprojected)
    print (geojson_reprojected_processed[0]['name'])
    geojson_reprojected_processed_encoded = encode(geojson_reprojected_processed)
    geojson_reprojected_processed_encoded_compressed = gzip.compress(geojson_reprojected_processed_encoded)

    # Add tile to MBTiles
    add_tile_to_mbtiles(args.output, z, x, y, geojson_reprojected_processed_encoded_compressed)
    mbtilesfixmeta.fix_metadata(args.output, 'GZIP') 

if __name__ == "__main__":
    main()
