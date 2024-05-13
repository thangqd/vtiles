import sys
import struct

def list_layers(osm_pbf_file):
    layers = []
    with open(osm_pbf_file, 'rb') as f:
        # Skip the file header
        f.seek(4)

        while True:
            # Read the blob header length
            header_length_bytes = f.read(4)
            if not header_length_bytes:
                break

            blob_header_length = struct.unpack('!I', header_length_bytes)[0]

            # Read the blob header
            blob_header = f.read(blob_header_length)
            blob_data = f.read()

            # Extract layer information
            if b'OSMDataLayer' in blob_header:
                layer_info = {}
                layer_info['header'] = blob_header
                # Extract other information about the layer if needed
                layers.append(layer_info)

    return layers

def main():
    if len(sys.argv) != 2:
        print("Usage: python list_osm_layers.py <osm_pbf_file>")
        sys.exit(1)
    
    osm_file = sys.argv[1]

    try:
        layers = list_layers(osm_file)
        if layers:
            print("Layers in the OSM PBF file:")
            for index, layer in enumerate(layers, start=1):
                print(f"Layer {index}: {layer}")
        else:
            print("No layers found in the OSM PBF file.")
    except Exception as e:
        print("Error:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
