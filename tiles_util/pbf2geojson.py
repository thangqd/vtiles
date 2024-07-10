import mapbox_vector_tile
import geojson
import sys
import argparse
from collections import defaultdict

def read_pbf_tile(pbf_file):
    # Read the .pbf file
    with open(pbf_file, 'rb') as f:
        tile_data = f.read()

    # Parse the .pbf tile data
    tile = mapbox_vector_tile.decode(tile_data)

    return tile

def convert_to_geojson(tile_data):
    layer_features = defaultdict(list)

    # Iterate through each layer in the tile
    for layer_name, layer_data in tile_data.items():
        for feature in layer_data['features']:
            # Extract geometry and properties
            geometry = feature['geometry']
            properties = feature['properties']

            # Create a GeoJSON feature
            geojson_feature = {
                'type': 'Feature',
                'geometry': geometry,
                'properties': properties
            }

            # Append the feature to the corresponding layer list
            layer_features[layer_name].append(geojson_feature)

    # Create GeoJSON FeatureCollection for each layer
    geojson_layers = {}
    for layer_name, features in layer_features.items():
        feature_collection = {
            'type': 'FeatureCollection',
            'features': features
        }
        geojson_layers[layer_name] = feature_collection

    return geojson_layers


def main():
    parser = argparse.ArgumentParser(description='Convert Mapbox Vector Tile (.pbf) to GeoJSON format.')
    parser.add_argument('-i', '--input', required=True, help='Input .pbf file path')
    parser.add_argument('-o', '--output', required=True, help='Output GeoJSON file path')
    args = parser.parse_args()

    pbf_file = args.input
    output_file = args.output

    # Read and parse the .pbf tile
    tile_data = read_pbf_tile(pbf_file)

    # Convert to GeoJSON format
    geojson_data = convert_to_geojson(tile_data)

    # Write GeoJSON data to the output file
    with open(output_file, 'w') as f:
        geojson.dump(geojson_data, f, indent=2)

    print(f"Converted .pbf to GeoJSON: {output_file}")

if __name__ == "__main__":
    main()
