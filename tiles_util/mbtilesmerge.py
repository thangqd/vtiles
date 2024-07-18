import subprocess
import os
import logging
import argparse

def mbtiles_merge(tippecanoe_dir, mbtiles_file1, mbtiles_file2, maxzoom, minzoom, output):
    logging.basicConfig(level=logging.INFO)
    
    args = [
        os.path.join(tippecanoe_dir, 'tile-join'),
        mbtiles_file1,
        mbtiles_file2,
        '-z', str(maxzoom),
        '-Z', str(minzoom),
        '-o', output
    ]

    try:
        logging.info('Running Tippecanoe with arguments: %s', ' '.join(args))
        output = subprocess.check_output(args, stderr=subprocess.STDOUT)
        logging.info('Tippecanoe output written to: %s', output.decode('utf8'))
    except subprocess.CalledProcessError as e:
        logging.error('Error running Tippecanoe:\n%s', e.output.decode('utf8'))
        raise


def main():
    parser = argparse.ArgumentParser(description='Merge MBTiles using Tippecanoe.')
    parser.add_argument('-i1', '--mbtiles1', required=True, help='Input MBTiles file 1')
    parser.add_argument('-i2', '--mbtiles2', required=True, help='Input MBTiles file 1')
    parser.add_argument('-o', '--output', required=True, help='Output MBTiles file')
    parser.add_argument('-t', '--tippecanoe-dir', default='/usr/local/bin/', help='Directory where the Tippecanoe executable is located')
    parser.add_argument('-z', '--maxzoom', type=int, default=16, help='Maximum zoom level')
    parser.add_argument('-Z', '--minzoom', type=int, default=0, help='Minimum zoom level')
    args = parser.parse_args()

    mbtiles_merge(
        tippecanoe_dir=args.tippecanoe_dir,
        mbtiles_file1=args.mbtiles1,
        mbtiles_file2=args.mbtiles2,
        maxzoom=args.maxzoom,
        minzoom=args.minzoom,
        output=args.output
    )

if __name__ == '__main__':
    main()
