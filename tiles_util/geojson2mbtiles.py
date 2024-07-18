import subprocess
import os
import logging
import argparse

def geojson_to_mbtiles(      
        filepaths,
        tippecanoe_dir,
        mbtiles_file,
        maxzoom,
        minzoom,
        extra_args=()
    ):
    logging.basicConfig(level=logging.INFO)
    
    args = [
        os.path.join(tippecanoe_dir, 'tippecanoe'),   
        # '-zg',   
        '-o', mbtiles_file,
        '-z', str(int(maxzoom)),
        '-Z', str(int(minzoom))
    ]
    
    for arg in extra_args:
        args.append(arg)
    
    for filepath in filepaths:
        args.append(filepath)
    
    try:
        logging.info('Running Tippecanoe with arguments: %s', ' '.join(args))
        output = subprocess.check_output(args, stderr=subprocess.STDOUT)
        logging.info('Tippecanoe output:\n%s', output.decode('utf8'))
    except subprocess.CalledProcessError as e:
        logging.error('Error running Tippecanoe:\n%s', e.output.decode('utf8'))
        raise

def main():
    parser = argparse.ArgumentParser(description='Convert GeoJSON files to MBTiles using Tippecanoe.')
    parser.add_argument('-i', '--input', nargs='+', required=True, help='Input GeoJSON file paths')
    parser.add_argument('-o', '--output', required=True, help='Output MBTiles file')
    parser.add_argument('-t', '--tippecanoe-dir', default='/usr/local/bin/', help='Directory where the Tippecanoe executable is located')
    parser.add_argument('-z', '--maxzoom', type=int, default=6, help='Maximum zoom level')
    parser.add_argument('-Z', '--minzoom', type=int, default=0, help='Minimum zoom level')
    parser.add_argument('--extra-args', nargs='*', default=(), help='Additional arguments for Tippecanoe')
    # parser.add_argument('extra_args', nargs=argparse.REMAINDER, help='Additional arguments for Tippecanoe')
    args = parser.parse_args()
    # -zg: Automatically choose a maxzoom that should be sufficient to clearly distinguish the features and the detail within each feature
    # --drop-densest-as-needed: If the tiles are too big at low zoom levels, drop the least-visible features to allow tiles to be created with those features that remain
    # --extend-zooms-if-still-dropping: If even the tiles at high zoom levels are too big, keep adding zoom levels until one is reached that can represent all the features
    # --coalesce-densest-as-needed: If the tiles are too big at low or medium zoom levels, merge as many features together as are necessary to allow tiles to be created with those features that are still distinguished
    # -z3: Only generate zoom levels 0 through 3
    # -Z4: Only generate zoom levels 4 and beyond

    geojson_to_mbtiles(
        filepaths=args.input,
        tippecanoe_dir=args.tippecanoe_dir, # '/usr/local/bin/'
        mbtiles_file=args.output,
        maxzoom=args.maxzoom,
        minzoom=args.minzoom,
        extra_args=args.extra_args
    )

if __name__ == '__main__':
    main()
