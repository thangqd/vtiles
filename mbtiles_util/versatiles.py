import versatiletiles
import sys

# Function to convert OSM PBF to MBTiles using Versatile Tiles
def convert_osm_pbf_to_mbtiles(osm_pbf_file, mbtiles_file):
    config = {
        "input": osm_pbf_file,
        "output": mbtiles_file,
        "min_zoom": 0,
        "max_zoom": 14,  # Adjust max zoom level as needed
        "type": "pbf",
        "overwrite": True
    }
    versatiletiles.generate(config)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py input_osm_pbf_file output_mbtiles_file")
        sys.exit(1)

    osm_pbf_file = sys.argv[1]
    mbtiles_file = sys.argv[2]

    convert_osm_pbf_to_mbtiles(osm_pbf_file, mbtiles_file)
