import subprocess
import os
import logging
import argparse

def mbtiles_to_geojson(tippecanoe_dir, mbtiles_file, layer, maxzoom, minzoom, geojson_file):
    logging.basicConfig(level=logging.INFO)
    
    args = [
        os.path.join(tippecanoe_dir, 'tippecanoe-decode'),
        mbtiles_file,
        '-l', layer,
        '-c',  # merge all tiles into one unique GeoJSON file
        '-z', str(maxzoom),
        '-Z', str(minzoom)
    ]

    command = ' '.join(args) + f" > {geojson_file}"
    
    try:
        logging.info('Running Tippecanoe with command: %s', command)
        subprocess.run(command, shell=True, check=True)
        logging.info('Tippecanoe output written to: %s', geojson_file)
    except subprocess.CalledProcessError as e:
        logging.error('Error running Tippecanoe:\n%s', e.stderr.decode('utf8'))
        raise

def main():
    parser = argparse.ArgumentParser(description='Convert MBTiles to GeoJSON using Tippecanoe.')
    parser.add_argument('-i', '--input', required=True, help='Input MBTiles file')
    parser.add_argument('-o', '--output', required=True, help='Output GeoJSON file')
    parser.add_argument('-t', '--tippecanoe-dir', default='/usr/local/bin/', help='Directory where the Tippecanoe executable is located')
    parser.add_argument('-z', '--maxzoom', type=int, default=6, help='Maximum zoom level')
    parser.add_argument('-Z', '--minzoom', type=int, default=6, help='Minimum zoom level')
    parser.add_argument('-l', '--layer', required=True, help='Layer to be extracted')
    args = parser.parse_args()

    mbtiles_to_geojson(
        tippecanoe_dir=args.tippecanoe_dir,
        mbtiles_file=args.input,
        layer=args.layer,
        maxzoom=args.maxzoom,
        minzoom=args.minzoom,
        geojson_file=args.output
    )

if __name__ == '__main__':
    main()
