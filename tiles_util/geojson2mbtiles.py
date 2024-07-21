import json
import argparse
from mapbox_vector_tile import encode
import mercantile
import sqlite3
from shapely.geometry import shape, mapping
from shapely.ops import transform
from pyproj import Proj, transform as pyproj_transform
from shapely.wkt import loads as wkt_loads, dumps as wkt_dumps

def create_mbtiles(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('CREATE TABLE metadata (name TEXT, value TEXT);')
    c.execute('CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB);')
    c.execute('CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row);')
    conn.commit()
    conn.close()

def fix_wkt(data):
    result = []
    
    for key in data:
        feature_collection = data[key]
        features = []
        
        for feature in feature_collection.get('features', []):
            geom = feature.get('geometry', {})
            geom_type = geom.get('type')
            coords = geom.get('coordinates')
            
            if geom_type is None or coords is None or (isinstance(coords, (list, dict)) and not coords):
                # Handle null or empty geometry
                wkt_geom = f'{geom_type or "GEOMETRY"} EMPTY'
                
            elif geom_type == 'Polygon':
                if not coords or not coords[0]:
                    wkt_geom = 'POLYGON EMPTY'
                else:
                    wkt_geom = 'POLYGON ((' + ', '.join([' '.join(map(str, pt)) for pt in coords[0]]) + '))'
                
            elif geom_type == 'LineString':
                if not coords:
                    wkt_geom = 'LINESTRING EMPTY'
                else:
                    wkt_geom = 'LINESTRING (' + ', '.join([' '.join(map(str, pt)) for pt in coords]) + ')'
                
            elif geom_type == 'MultiPolygon':
                if not coords:
                    wkt_geom = 'MULTIPOLYGON EMPTY'
                else:
                    polygons = []
                    for polygon in coords:
                        if not polygon:
                            polygons.append('EMPTY')
                        else:
                            polygons.append('((' + ', '.join([' '.join(map(str, pt)) for pt in polygon[0]]) + '))')
                    wkt_geom = 'MULTIPOLYGON (' + ', '.join(polygons) + ')'
                
            elif geom_type == 'MultiLineString':
                if not coords:
                    wkt_geom = 'MULTILINESTRING EMPTY'
                else:
                    lines = []
                    for line in coords:
                        if not line:
                            lines.append('EMPTY')
                        else:
                            lines.append('(' + ', '.join([' '.join(map(str, pt)) for pt in line]) + ')')
                    wkt_geom = 'MULTILINESTRING (' + ', '.join(lines) + ')'
                
            elif geom_type == 'Point':
                if not coords:
                    wkt_geom = 'POINT EMPTY'
                else:
                    wkt_geom = 'POINT (' + ' '.join(map(str, coords)) + ')'
                
            elif geom_type == 'MultiPoint':
                if not coords:
                    wkt_geom = 'MULTIPOINT EMPTY'
                else:
                    points = []
                    for point in coords:
                        points.append(' '.join(map(str, point)))
                    wkt_geom = 'MULTIPOINT (' + ', '.join(points) + ')'
                
            else:
                # Skip unsupported geometry types
                continue
            
            features.append({
                'geometry': wkt_geom,
                'properties': feature.get('properties', {})
            })
        
        result.append({
            'name': key,
            'features': features
        })
    
    return result

def geojson_to_custom_format(geojson):
    layers = {}

    # Process each feature
    for feature in geojson['features']:
        layer_name = 'my_layer'  # Customize layer name if needed
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
    # formatted_layers = [{'name': 'my_layer', 'features': [{'geometry': 'POLYGON ((11834838.0505347177386284 1211292.9252088242210448, 11833637.9057463649660349 1212264.4709898722358048, 11835889.6059683244675398 1212893.1182599624153227, 11837546.9487712886184454 1210584.2682861764915287, 11835192.3789960406720638 1210641.4180380033794791, 11835192.3789960406720638 1210641.4180380033794791, 11834838.0505347177386284 1211292.9252088242210448))', 'properties': {'name': '1'}}, {'geometry': 'POLYGON ((11837455.5091683678328991 1209909.9012146256864071, 11838267.0356443021446466 1211327.2150599195156246, 11839615.7697874046862125 1211167.1957548058126122, 11839832.9388443436473608 1210172.7900730269029737, 11838369.9051975868642330 1209452.7032000147737563, 11837455.5091683678328991 1209909.9012146256864071))', 'properties': {'name': '1'}}, {'geometry': 'POLYGON ((11834864.5771230701357126 1209201.3277407283894718, 11836524.3525836132466793 1209498.7441527340561152, 11836015.8664598632603884 1208616.0889945253729820, 11836015.8664598632603884 1208616.0889945253729820, 11834864.5771230701357126 1209201.3277407283894718))', 'properties': {'name': '2'}}]}]
    # formatted_layers = [{
    #     "name": "water",
    #     "features": [
    #       {
    #         "geometry":"POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))",
    #         "properties":{
    #           "uid":123,
    #           "foo":"bar",
    #           "cat":"flew"
    #         }
    #       }
    #     ]
    #   }]
    return formatted_layers

def reproject_feature_to_tile(feature, tile_bounds, extent=4096):
    """Reproject a feature from Web Mercator to tile coordinates within a 4096 extent."""
    geom = wkt_loads(feature['geometry'])

    minx, miny, maxx, maxy = tile_bounds

    def mercator_to_tile(x, y):
        # Scale to tile coordinates
        tx = (x - minx) / (maxx - minx) * extent
        ty = (y - miny) / (maxy - miny) * extent
        # Flip y axis for tile coordinates
        return tx, extent - ty

    reprojected_geom = transform(mercator_to_tile, geom)
    result = {
        "geometry": mapping(reprojected_geom),
        "properties": feature.get("properties", {})
    }
    
    result =[{'name': 'water', 'features': [{'geometry': 'POLYGON((3257.6188764017343,1924.195788997867), (3257.4962116230354,1924.0964889389206), (3257.7263541125944,1924.032235959602), (3257.8957483307977,1924.2682196290993), (3257.65509171735,1924.2623784491611), (3257.65509171735,1924.2623784491611), (3257.6188764017343,1924.195788997867))', 'properties': {'name': '1'}}]}]
    result = [
    {
        "name": "water",
        "features": [
        {
            "geometry": "POLYGON ((0 0, 0 1, 1 1, 1 0, 0 0))",
            "properties": {
            "uid": 123,
            "foo": "bar",
            "cat": "flew"
            }
        }
        ]
    }
]
    return result

def geojson_to_mvt(layers, z, x, y, extent=4096):
    """Convert GeoJSON layers to Mapbox Vector Tile format."""
    tile_bounds = mercantile.xy_bounds(x, y, z)
    reprojected_layers = {}
    
    for layer in layers:
        layer_name = layer['name']
        reprojected_features = [reproject_feature_to_tile(feature, tile_bounds, extent) for feature in layer['features']]
        reprojected_layers[layer_name] = reprojected_features
   
    reprojected_layers_fixed = fix_wkt(reprojected_layers)
    print (reprojected_layers_fixed)
    tile_data = encode(reprojected_layers_fixed, extents=extent)
    return tile_data

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
    with open(args.input, 'r') as f:
        geojson_data = json.load(f)

    # Define tile coordinates
    z, x, y = args.zoom, args.x, args.y

    # Create MBTiles file
    create_mbtiles(args.output)
    
    geojson_data_processed = geojson_to_custom_format(geojson_data)
    # Convert GeoJSON features to tile coordinates
    tile_data = geojson_to_mvt(geojson_data_processed, z, x, y)
    
    # Add tile to MBTiles
    add_tile_to_mbtiles(args.output, z, x, y, tile_data)

if __name__ == "__main__":
    main()
