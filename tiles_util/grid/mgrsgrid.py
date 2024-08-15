
# Reference: https://github.com/pistell/Leaflet.DumbMGRS
# https://mgrs-mapper.com/app, https://military-history.fandom.com/wiki/Military_Grid_Reference_System
# https://codesandbox.io/s/how-to-toggle-react-leaflet-layer-control-and-rectangle-grid-f43xi?file=/src/App.js:1057-1309
# https://github.com/GeoSpark/gridoverlay/tree/d66ed86636c7ec3f02ca2e9298ac3086c2023f1d
# https://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#//00700000001n000000
# https://storymaps.arcgis.com/stories/842edf2b4381438b9a4edefed124775b
# https://github.com/dnlbaldwin/React-Leaflet-MGRS-Graticule
# https://dnlbaldwin.github.io/React-Leaflet-MGRS-Graticule/

# from tiles_util.utils.geocode import mgrs
# mgrs_code = mgrs.toMgrs(10.63038542, 106.12923131,3)
# # mgrs_code = mgrs.toMgrs(-84.65698112, -80.69068228,3)


# print('mgrs_code: ', mgrs_code)
# mgrs_encode = mgrs.toWgs(mgrs_code)
# # mgrs_encode = mgrs.toWgs('48QYD214738')
# print('mgrs_encode: ', mgrs_encode)
import argparse
import geopandas as gpd
from shapely.geometry import box
from tqdm import tqdm

bands = ['C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']

def generate_mgrs_grid(polar=True):
    features = []

    def export_polygon(lon, lat, width, height, mgrs):
        rect = box(lon, lat, lon + width, lat + height)
        features.append({
            'geometry': rect,
            'mgrs': mgrs
        })

    if polar:
        export_polygon(-180, -90, 180, 10, 'A')
        export_polygon(0, -90, 180, 10, 'B')

    lat = -80
    for b in bands:
        if b == 'X':
            height = 12
            lon = -180
            for i in range(1, 31):
                mgrs = '{:02d}{}'.format(i, b)
                width = 6
                export_polygon(lon, lat, width, height, mgrs)
                lon += width
            export_polygon(lon, lat, 9, height, '31X')
            lon += 9
            export_polygon(lon, lat, 12, height, '33X')
            lon += 12
            export_polygon(lon, lat, 12, height, '35X')
            lon += 12
            export_polygon(lon, lat, 9, height, '37X')
            lon += 9
            for i in range(38, 61):
                mgrs = '{:02d}{}'.format(i, b)
                width = 6
                export_polygon(lon, lat, width, height, mgrs)
                lon += width
        else:
            height = 8
            lon = -180
            for i in range(1, 61):
                mgrs = '{:02d}{}'.format(i, b)
                if b == 'V' and i == 31:
                    width = 3
                elif b == 'V' and i == 32:
                    width = 9
                else:
                    width = 6
                export_polygon(lon, lat, width, height, mgrs)
                lon += width
        lat += height

    if polar:
        export_polygon(-180, 84, 180, 6, 'Y')
        export_polygon(0, 84, 180, 6, 'Z')

    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(features, crs="EPSG:4326")
    return gdf


def main():
    parser = argparse.ArgumentParser(description="Generate MGRS Grid Zone Designators and save as GeoJSON.")
    parser.add_argument('-o', '--output', type=str, required=True, help="Output GeoJSON file path.")
    args = parser.parse_args()

    try:
        # Generate MGRS grid
        gdf = generate_mgrs_grid()

        # Save to file
        gdf.to_file(args.output, driver='GeoJSON')
        print(f"GeoJSON file saved to {args.output}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()

