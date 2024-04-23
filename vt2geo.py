import geopandas as gpd
import requests

from vt2geojson.tools import vt_bytes_to_geojson

MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoidGhhbmdxZCIsImEiOiJucHFlNFVvIn0.j5yb-N8ZR3d4SJAYZz-TZA"

x = 150
y = 194
z = 9

url = f"https://api.mapbox.com/v4/mapbox.mapbox-streets-v6/{z}/{x}/{y}.vector.pbf?access_token={MAPBOX_ACCESS_TOKEN}"
r = requests.get(url)
assert r.status_code == 200, r.content
vt_content = r.content

features = vt_bytes_to_geojson(vt_content, x, y, z)
gdf = gpd.GeoDataFrame.from_features(features)
print(gdf)


