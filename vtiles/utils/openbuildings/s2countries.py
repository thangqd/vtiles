import json
from shapely.geometry import shape

# Load the countries GeoJSON file
with open("./countries.geojson") as f:
    countries_geojson = json.load(f)

# Load the s2 GeoJSON file
with open("./s2.geojson") as f:
    s2_geojson = json.load(f)

# Extract geometries and attributes
countries = [
    {
        'name': feature['properties']['name'],
        'iso': feature['properties']['iso'],
        'geometry': shape(feature['geometry'])
    } 
    for feature in countries_geojson['features']
]

s2 = [
    {
        'tile_id': feature['properties']['tile_id'],
        'tile_url': feature['properties']['tile_url'],
        'size_mb': feature['properties']['size_mb'],
        'geometry': shape(feature['geometry'])
    } 
    for feature in s2_geojson['features']
]

# Prepare CSV data
csv_data = "name,iso,tile_id,tile_url,size_mb\n"  # CSV header

# Check for intersections
for country in countries:
    for grid in s2:
        if country['geometry'].intersects(grid['geometry']):
            csv_data += f"{country['name']},{country['iso']},{grid['tile_id']}\n"

# Write to CSV file
with open("s2countries.csv", "w") as f:
    f.write(csv_data)

print("CSV saved successfully!")
