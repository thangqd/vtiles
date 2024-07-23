import requests
import json
from tiles_util.utils.vt2geojson.tools import vt_bytes_to_geojson

MAPBOX_ACCESS_TOKEN = "your_mapbox_access_token_here"

x = 11833
y = 6734
z = 14

url = f"https://api.mapbox.com/v4/mapbox.mapbox-streets-v6/{z}/{x}/{y}.vector.pbf?access_token=pk.eyJ1IjoidGhhbmdxZCIsImEiOiJucHFlNFVvIn0.j5yb-N8ZR3d4SJAYZz-TZA"
url= f"https://map-api-new.sovereignsolutions.net/sovereign/v20240410/nepal/{z}/{x}/{y}.pbf"

try:
    r = requests.get(url)
    r.raise_for_status()  # Will raise an HTTPError for bad responses
    vt_content = r.content
    # with open('./data/1.pbf', 'rb') as f:
    #     vt_content = f.read()

    print(vt_content)
    features = vt_bytes_to_geojson(vt_content, x, y, z)

    # Specify the output file path
    output_file = './data/6734.geojson'

    # Save the features to a GeoJSON file
    with open(output_file, 'w') as f:
        json.dump(features, f, indent=2)

    print(f"GeoJSON data has been saved to {output_file}")

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
