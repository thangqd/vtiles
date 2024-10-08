import sqlite3, json
import os, sys, datetime
from vtiles.utils.geopreocessing import check_vector,count_tiles

# Read vector metadata
def read_vector_metadata(mbtiles):
    try:
        """Read metadata from vector MBTiles file."""
        connection = sqlite3.connect(mbtiles)
        cursor = connection.cursor()
        # Extract metadata
        # cursor.execute("SELECT name, value FROM metadata where name <>'json'")
        cursor.execute("SELECT name, value FROM metadata where name <> 'json'")
        metadata = dict(cursor.fetchall())     
        return metadata
    except sqlite3.Error as e:
            print(f"error reading metadata: {e}")
            print(f"Please use mbtilesfixmeta to create metadata or use mbtilesinspect")
            return None
    finally:
        cursor.close()
        connection.close()  

# Read raster metadata
def read_raster_metadata(mbtiles):
    try:
        """Read metadata from raster MBTiles file."""
        connection = sqlite3.connect(mbtiles)
        cursor = connection.cursor()
        # Extract metadata
        cursor.execute("SELECT name, value FROM metadata")
        metadata = dict(cursor.fetchall())
        return metadata
    except sqlite3.Error as e:
        print(f"error reading metadata: {e}")
        print(f"Please use mbtilesfixmeta to create metadata or use mbtilesinspect")
        return None
    finally:
        cursor.close()
        connection.close() 

# list all vector layers
def read_vector_layers(mbtiles):    
    connection = sqlite3.connect(mbtiles)
    cursor = connection.cursor()
    
    # Fetch the JSON from the metadata
    cursor.execute("SELECT value FROM metadata WHERE name = 'json'")
    row = cursor.fetchone()
    
    if row is not None:
        json_content = row[0]
        try:
            layers_json = json.loads(json_content)
            # Print vector layers information
            if "vector_layers" in layers_json:
                vector_layers = layers_json["vector_layers"]
                print("######:")
                print("Vector layers:")
                for index, layer in enumerate(vector_layers):
                    row_index = index + 1
                    layer_id = layer["id"]
                    description = layer.get("description", "")
                    minzoom = layer.get("minzoom", "")
                    maxzoom = layer.get("maxzoom", "")
                    fields = layer.get("fields", {})                    
                    print(f"{row_index}. {layer_id}: minzoom {minzoom}, maxzoom {maxzoom}")
        except Exception as e:
            print(f'Reading vector_layers error: {e}')
            pass
 
        # Print tilestats information
        # if "tilestats" in layers_json:
        #     tilestats = layers_json["tilestats"]
        #     print("######:")
        #     print("Tile Stats:")
        #     layer_count = tilestats.get("layerCount", 0)
        #     print(f"  Layer Count: {layer_count}")
            
        #     if "layers" in tilestats:
        #         for index, layer in enumerate(tilestats["layers"]):
        #             row_index = index + 1
        #             layer_name = layer.get("layer", "")
        #             count = layer.get("count", "")
        #             geometry = layer.get("geometry", "")
        #             attribute_count = layer.get("attributeCount", 0)
                    
        #             print(f"{row_index}: {layer_name}")
        #             print(f"  Count: {count}")
        #             print(f"  Geometry: {geometry}")
        #             print(f"  Attribute Count: {attribute_count}")
                    
        #             if "attributes" in layer:
        #                 for attr_index, attribute in enumerate(layer["attributes"]):
        #                     attr_name = attribute.get("attribute", "")
        #                     attr_count = attribute.get("count", 0)
        #                     attr_type = attribute.get("type", "")
        #                     attr_values = attribute.get("values", [])
                            
        #                     print(f"    Attribute {attr_index + 1}: {attr_name}")
        #                     print(f"      Count: {attr_count}")
        #                     print(f"      Type: {attr_type}")
        #                     print(f"      Values: {attr_values}")
        #                     print(" ")            
    cursor.close()
    connection.close()
   
def main():
    if len(sys.argv) != 2:
      print("Please provide MBTiles input filename.")
      return
    mbtiles = sys.argv[1]
    file_stat = os.stat(mbtiles)
    file_size_mb = round(file_stat.st_size / (1024 * 1024),2)
    # file_created = datetime.datetime.fromtimestamp(file_stat.st_ctime).strftime("%Y-%m-%d %I:%M:%S %p")
    file_last_modified = datetime.datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %I:%M:%S %p")
    # file_size = os.path.getsize(mbtiles)
    # file_size_mb = round(file_size / (1024 * 1024),2)
    print('######')
    print("File size: ", file_size_mb, 'MB')
    # print("Date created: ", file_created)
    print("Last modified: ", file_last_modified)
    if (os.path.exists(mbtiles)):
        is_vector, _ = check_vector(mbtiles) 
        num_tiles = count_tiles(mbtiles)
        if is_vector: # vector
            metadata = read_vector_metadata(mbtiles)
            if metadata:      
                print("######")
                print("Metadata:")
                for key, value in metadata.items():
                    print(f"{key}: {value}")
                read_vector_layers(mbtiles)
            print('######')
            print(f"Total number of tiles: {num_tiles}")
            
        else:
            metadata = read_raster_metadata(mbtiles)   
            if metadata:         
                print("###### Metadata:")
                for key, value in metadata.items():
                    print(f"{key}: {value}")
            print("######")
            print(f"Total number of tiles: {num_tiles}")
    else: 
        print ('MBTiles file does not exist!. Please recheck and input a correct file path.')
        return

if __name__ == "__main__":
    main()
