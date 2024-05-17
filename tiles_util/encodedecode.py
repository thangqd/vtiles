from mapbox_vector_tile import encode, decode

pbf_tile = encode([
      {
        "name": "water",
        "features": [
          {
            "geometry":"POLYGON ((0 0, 0 10, 10 10, 10 0, 0 0))",
            "properties":{
              "uid":123,
              "foo":"bar",
              "cat":"flew"
            }
          }
        ]
      }])
# print (pbf_tile)

print (decode(b'\x1aH\n\x05water\x12\x18\x12\x06\x00\x00\x01\x01\x02\x02\x18\x03"\x0c\t\x00\x80@\x1a\x00\x13\x14\x00\x00\x14\x0f\x1a\x03uid\x1a\x03foo\x1a\x03cat"\x02 {"\x05\n\x03bar"\x06\n\x04flew(\x80 x\x02'))