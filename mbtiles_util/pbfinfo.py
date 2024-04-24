import sys
import struct

class PBFReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file = open(file_path, 'rb')

    def read_varint(self):
        result = 0
        shift = 0
        while True:
            byte = self.file.read(1)
            if len(byte) == 0:
                raise EOFError("Unexpected end of file")
            byte = ord(byte)
            result |= (byte & 0x7F) << shift
            shift += 7
            if not byte & 0x80:
                break
        return result

    def read_primitive(self, type):
        if type == 0:
            return self.read_varint()
        elif type == 1:
            return struct.unpack('d', self.file.read(8))[0]
        elif type == 2:
            length = self.read_varint()
            return self.file.read(length)
        elif type == 5:
            return struct.unpack('I', self.file.read(4))[0]

    def read_message(self):
        while True:
            field_info = self.read_varint()
            if field_info == 0:
                break
            field_number = field_info >> 3
            field_type = field_info & 0x07
            value = self.read_primitive(field_type)
            if field_number == 1:
                print("Layer:", value)

    def read_file(self):
        while True:
            header = self.file.read(4)
            if len(header) == 0:
                break
            message_length = struct.unpack('i', header)[0]
            self.read_message()

    def close(self):
        self.file.close()

if __name__ == "__main__":
    # Check if a filename is provided as a command-line argument
    if len(sys.argv) != 2:
        print("Usage: python script.py <file_name.pbf>")
        sys.exit(1)
    
    # Get the file name from command-line arguments
    pbf_file_path = sys.argv[1]
    
    # Create the PBFReader instance
    reader = PBFReader(pbf_file_path)
    
    # Read and process the .pbf file
    reader.read_file()
    
    # Close the file
    reader.close()
