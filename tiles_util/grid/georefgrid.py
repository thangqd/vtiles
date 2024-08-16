
from tiles_util.utils.geocode import georef
georef_code = georef.encode(10.534535345,106.4343242,3)
print(georef_code)
georef_decode = georef.decode(georef_code)
print(georef_decode)