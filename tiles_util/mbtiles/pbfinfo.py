from tiles_util.utils.mapbox_vector_tile import decode
import sys
import gzip
import zlib
import os
from datetime import datetime

def read_pbf_tile(pbf_file):
    try:
        with open(pbf_file, 'rb') as f:
            tile_data = f.read()

        # Check for GZIP compression
        if tile_data[:2] == b'\x1f\x8b':
            compression_type = 'GZIP'
            tile_data = gzip.decompress(tile_data)
        # Check for ZLIB compression
        elif tile_data[:2] == b'\x78\x9c' or tile_data[:2] == b'\x78\x01' or tile_data[:2] == b'\x78\xda':
            compression_type = 'ZLIB'
            tile_data = zlib.decompress(tile_data)
        else:
            compression_type = 'None'

        # Decode the tile data
        tile = decode(tile_data)
        return tile, compression_type

    except Exception as e:
        print(f"Error reading or decoding the PBF file: {e}")
        sys.exit(1)

def count_feature_types(layer_data):
    from collections import defaultdict
    feature_types_count = defaultdict(int)  # Use defaultdict to count feature types
    for feature in layer_data['features']:
        geometry_type = feature['geometry']['type']
        feature_types_count[geometry_type] += 1
    return feature_types_count

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_pbf_file>")
        sys.exit(1)

    pbf_file = sys.argv[1]

    # Get file size and last modified date
    file_size = os.path.getsize(pbf_file)
    last_modified_timestamp = os.path.getmtime(pbf_file)
    last_modified_date = datetime.fromtimestamp(last_modified_timestamp).strftime('%Y-%m-%d %H:%M:%S')

    # Read and parse the PBF tile
    tile_data, compression_type = read_pbf_tile(pbf_file)

    print(f"File size: {file_size} bytes")
    print(f"Last modified: {last_modified_date}")
    print(f"Compression type: {compression_type}")

    # Print layer information
    for layer_name, layer_data in tile_data.items():
        num_features = len(layer_data['features'])
        feature_types_count = count_feature_types(layer_data)
        
        print(f"Layer '{layer_name}':")
        print(f"  Total features: {num_features} features")
        print("  Feature types:")
        for feature_type, count in feature_types_count.items():
            print(f"    {feature_type}: {count} features")

if __name__ == "__main__":
    main()
