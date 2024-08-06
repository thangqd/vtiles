import json
import argparse
import sqlite3
from tiles_util.utils.vt2geojson.tools import vt_bytes_to_geojson
import gzip
import zlib
import logging
from tqdm import tqdm

def tile_data_to_geojson(tile_data, x, y, z, layers):
    """
    Convert tile data to GeoJSON format, filtering by specified layers, and add zoom level to each feature's properties.

    Args:
        tile_data (bytes): The binary tile data.
        x (int): The x coordinate of the tile.
        y (int): The y coordinate of the tile.
        z (int): The zoom level of the tile.
        layers (list): List of layer names to include in the output.

    Returns:
        dict: The filtered GeoJSON features with zoom level included.
    """
    try:
        features = vt_bytes_to_geojson(tile_data, x, y, z)
        if layers:
            filtered_features = {layer: features[layer] for layer in layers if layer in features}
        else:
            filtered_features = features

        # Add zoom level to each feature's properties
        for layer, feature_collection in filtered_features.items():
            for feature in feature_collection['features']:
                if 'properties' not in feature:
                    feature['properties'] = {}
                feature['properties']['zoom_level'] = z
        
        return filtered_features
    except Exception as e:
        logging.error(f"Error converting tile data to GeoJSON at tile ({x}, {y}, {z}): {e}")
        return None

def decompress_tile_data(tile_data):
    """
    Decompress tile data if it is compressed.

    Args:
        tile_data (bytes): The binary tile data.

    Returns:
        bytes: The decompressed tile data.
    """
    try:
        if tile_data[:2] == b'\x1f\x8b':  # Check for gzip magic number
            return gzip.decompress(tile_data)
        elif tile_data[:2] in {b'\x78\x9c', b'\x78\x01', b'\x78\xda'}:
            return zlib.decompress(tile_data)
        return tile_data
    except Exception as e:
        logging.error(f"Failed to decompress tile data: {e}")
        return tile_data
    
def merge_geojsons(geojson_list):
    """
    Merge a list of GeoJSON feature collections into a single feature collection.

    Args:
        geojson_list (list): List of GeoJSON feature collections.

    Returns:
        dict: Merged GeoJSON feature collection.
    """
    merged_geojson = {}

    for geojson in geojson_list:
        for key, feature_collection in geojson.items():
            if key not in merged_geojson:
                merged_geojson[key] = {'type': 'FeatureCollection', 'features': []}
            merged_geojson[key]['features'].extend(feature_collection['features'])
    
    return merged_geojson

def mbtiles_to_geojson(input_mbtiles, output_geojson, min_zoom, max_zoom, flip_y, layers):
    """
    Convert MBTiles data to GeoJSON format.

    Args:
        input_mbtiles (str): Path to the input MBTiles file.
        output_geojson (str): Path to the output GeoJSON file.
        min_zoom (int): Minimum zoom level to extract.
        max_zoom (int): Maximum zoom level to extract.
        flip_y (bool): Whether to flip the y coordinate (TMS format).
        layers (list): List of layer names to include in the output.
    """
    all_features = []
    try:
        conn = sqlite3.connect(input_mbtiles)
        cursor = conn.cursor()

        for zoom_level in range(min_zoom, max_zoom + 1):
            cursor.execute('''
                SELECT tile_column, tile_row, tile_data 
                FROM tiles 
                WHERE zoom_level=?''', (zoom_level,))
            rows = cursor.fetchall()

            for x, y, tile_data in tqdm(rows, desc=f"Converting tiles at zoom level {zoom_level} to GeoJSON"):
                if flip_y:
                    y = (1 << zoom_level) - 1 - y
                tile_data = decompress_tile_data(tile_data)
                if tile_data:
                    features = tile_data_to_geojson(tile_data, x, y, zoom_level, layers)
                    if features:
                        all_features.append(features)

        conn.close()

        merged_geojson = merge_geojsons(all_features)
        with open(output_geojson, 'w') as f:
            json.dump(merged_geojson, f, indent=2)
        logging.info(f"GeoJSON data has been saved to {output_geojson}")

    except sqlite3.Error as e:
        logging.error(f"Failed to read MBTiles file {input_mbtiles}: {e}")
    except Exception as e:
        logging.error(f"Failed to convert {input_mbtiles} to GeoJSON: {e}")

def main():
    """
    Main function to parse arguments and convert MBTiles to GeoJSON.
    """
    parser = argparse.ArgumentParser(description='Convert Tile data from PBF file, MBTiles file, or URL to GeoJSON.')
    parser.add_argument('-i', '--input', type=str, required=True, help='Input PBF file, MBTiles file, or URL')
    parser.add_argument('-o', '--output', type=str, required=True, help='Output GeoJSON file')
    parser.add_argument('-minzoom','--minzoom', type=int, required=True, help='Minimum tile zoom level')
    parser.add_argument('-maxzoom','--maxzoom', type=int, required=True, help='Maximum tile zoom level')
    parser.add_argument('-flipy', '--flipy', type=int, choices=[0, 1], default=0, help='Use TMS (flip y) format (1 for True, 0 for False)')
    parser.add_argument('-l', '--layers', type=str, nargs='*', help='List of layer names to filter')

    args = parser.parse_args()
    
    mbtiles_to_geojson(args.input, args.output, args.minzoom, args.maxzoom, args.flipy == 1, args.layers)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
