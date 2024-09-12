#!/usr/bin/env python
import sys
import pprint
from .pmtiles.reader import Reader, MmapSource

def print_usage():
    print("Usage: pmtilesinfo PMTILES_FILE")
    print("Usage: pmtilesinfo PMTILES_FILE Z X Y")
    exit(1)

def main():
    if len(sys.argv) <= 1:
        print_usage()

    pmtiles_file = sys.argv[1]

    try:
        with open(pmtiles_file, "r+b") as f:
            reader = Reader(MmapSource(f))
            if len(sys.argv) == 2:
                pprint.pprint(reader.header())
                pprint.pprint(reader.metadata())
            elif len(sys.argv) == 5:
                z = int(sys.argv[2])
                x = int(sys.argv[3])
                y = int(sys.argv[4])
                tile_data = reader.get(z, x, y)
                sys.stdout.buffer.write(tile_data)
            else:
                print_usage()
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
