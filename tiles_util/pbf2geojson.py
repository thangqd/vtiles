import mapbox_vector_tile
import geojson
import argparse
from collections import defaultdict
import mercantile

def tile_to_latlon(tile, x, y, extent=4096):
    # Convert tile coordinates to geographic coordinates (EPSG:4326)
    bounds = mercantile.bounds(tile['x'], tile['y'], tile['z'])
    min_lon, min_lat, max_lon, max_lat = bounds.west, bounds.south, bounds.east, bounds.north

    # Calculate scale factors
    scale_x = (max_lon - min_lon) / extent
    scale_y = (max_lat - min_lat) / extent

    # Convert coordinates (invert y-axis)
    lon = min_lon + x * scale_x
    lat = min_lat + y * scale_y  
    # invert y
    # lat = max_lat - y * scale_y

    return lon, lat

def read_pbf_tile(pbf_file):
    # Read the .pbf file
    with open(pbf_file, 'rb') as f:
        tile_data = f.read()

    # Parse the .pbf tile data
    tile = mapbox_vector_tile.decode(tile_data)

    return tile

def convert_to_geojson(tile_data, z, x, y, extent=4096):
    layer_features = defaultdict(list)

    # Iterate through each layer in the tile
    for layer_name, layer_data in tile_data.items():
        for feature in layer_data['features']:
            # Extract geometry and properties
            geometry = feature['geometry']
            properties = feature['properties']

            # Convert tile coordinates to geographic coordinates
            if geometry['type'] == 'Point':
                coords = geometry['coordinates']
                lon, lat = tile_to_latlon({'z': z, 'x': x, 'y': y}, coords[0], coords[1], extent)
                geometry = geojson.Point((lon, lat))
            elif geometry['type'] == 'LineString':
                coords = geometry['coordinates']
                line = [tile_to_latlon({'z': z, 'x': x, 'y': y}, coord[0], coord[1], extent) for coord in coords]
                geometry = geojson.LineString(line)
            elif geometry['type'] == 'Polygon':
                coords = geometry['coordinates']
                polygon = [[tile_to_latlon({'z': z, 'x': x, 'y': y}, coord[0], coord[1], extent) for coord in ring] for ring in coords]
                geometry = geojson.Polygon(polygon)

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
    parser.add_argument('-z', required=True, type=int, help='Zoom level of the tile')
    parser.add_argument('-x', required=True, type=int, help='X coordinate of the tile')
    parser.add_argument('-y', required=True, type=int, help='Y coordinate of the tile')
    args = parser.parse_args()

    pbf_file = args.input
    output_file = args.output
    z = args.z
    x = args.x
    y = args.y

    # Read and parse the .pbf tile
    tile_data = read_pbf_tile(pbf_file)

    # Convert to GeoJSON format
    geojson_data = convert_to_geojson(tile_data, z, x, y)

    # Write GeoJSON data to the output file
    with open(output_file, 'w') as f:
        geojson.dump(geojson_data, f, indent=2)

    print(f"Converted .pbf to GeoJSON: {output_file}")

if __name__ == "__main__":
    main()
