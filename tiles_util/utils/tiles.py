import math

EarthRadius = 6378137
MinLatitude = -85.05112878
MaxLatitude = 85.05112878
MinLongitude = -180
MaxLongitude = 180
extend = 4096 

from dataclasses import dataclass
from collections import namedtuple

@dataclass
class Tile:
    x: int
    y: int
    z: int

@dataclass
class LngLatBbox:
    west: float
    south: float
    east: float
    north: float

Tile = namedtuple('Tile', ['x', 'y', 'z'])

def lat_lon_to_tile(lat: float, lon: float, zoom: int) -> Tile:
    """Convert latitude and longitude to tile coordinates (x, y) at a specific zoom level."""
    scale = 1 << zoom
    world_size = scale * extend

    x_pixel = (lon + 180.0) / 360.0 * world_size
    sin_lat = math.sin(math.radians(lat))
    y_pixel = (0.5 - (math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi))) * world_size

    tile_x = int(x_pixel / extend)
    tile_y = int((world_size - y_pixel) / extend)

    return Tile(x=tile_x, y=tile_y, z=zoom)

def clip(n, minValue, maxValue):
    return min(max(n, minValue), maxValue)

def map_size(levelOfDetail):
    return extend << levelOfDetail

def ground_resolution(latitude, levelOfDetail):
    latitude = clip(latitude, MinLatitude, MaxLatitude)
    return math.cos(latitude * math.pi / 180) * 2 * math.pi * EarthRadius / map_size(levelOfDetail)

def map_scale(latitude, levelOfDetail, screenDpi):
    return ground_resolution(latitude, levelOfDetail) * screenDpi / 0.0254

def long_lat_to_pixel_xy( longitude, latitude, levelOfDetail):
    longitude = clip(longitude, MinLongitude, MaxLongitude)
    latitude = clip(latitude, MinLatitude, MaxLatitude)    

    x = (longitude + 180) / 360
    sinLatitude = math.sin(latitude * math.pi / 180)
    y = 0.5 - math.log((1 + sinLatitude) / (1 - sinLatitude)) / (4 * math.pi)

    mapSize = map_size(levelOfDetail)
    pixelX = int(clip(x * mapSize + 0.5, 0, mapSize - 1))
    pixelY = int(clip(y * mapSize + 0.5, 0, mapSize - 1))

    return pixelX, pixelY

def pixel_xy_to_long_lat(pixelX, pixelY, levelOfDetail):
    mapSize = map_size(levelOfDetail)
    x = (clip(pixelX, 0, mapSize - 1) / mapSize) - 0.5
    y = 0.5 - (clip(pixelY, 0, mapSize - 1) / mapSize)

    latitude = 90 - 360 * math.atan(math.exp(-y * 2 * math.pi)) / math.pi
    longitude = 360 * x

    return longitude, latitude

def pixel_xy_to_tile_xy(pixelX, pixelY):
    tileX = pixelX // extend
    tileY = pixelY // extend
    return tileX, tileY

def tile_xy_to_pixel_xy(tileX, tileY):
    pixelX = tileX * extend
    pixelY = tileY * extend
    return pixelX, pixelY

def tile_xy_to_quad_key(tileX, tileY, levelOfDetail):
    quadKey = []
    for i in range(levelOfDetail, 0, -1):
        digit = '0'
        mask = 1 << (i - 1)
        if (tileX & mask) != 0:
            digit = chr(ord(digit) + 1)
        if (tileY & mask) != 0:
            digit = chr(ord(digit) + 2)
        quadKey.append(digit)
    return ''.join(quadKey)

def quad_key_to_tile_xy(quadKey):
    tileX = tileY = 0
    levelOfDetail = len(quadKey)
    for i in range(levelOfDetail):
        mask = 1 << (levelOfDetail - i - 1)
        if quadKey[i] == '1':
            tileX |= mask
        elif quadKey[i] == '2':
            tileY |= mask
        elif quadKey[i] == '3':
            tileX |= mask
            tileY |= mask
        elif quadKey[i] != '0':
            raise ValueError("Invalid QuadKey digit sequence.")
    return tileX, tileY, levelOfDetail

def get_tile_bounds(tileX, tileY, zoomLevel):
    # Get the upper-left pixel coordinates of the tile
    pixelX1, pixelY1 = tile_xy_to_pixel_xy(tileX, tileY)
    # Get the lower-right pixel coordinates of the tile
    pixelX2, pixelY2 = tile_xy_to_pixel_xy(tileX + 1, tileY + 1)
    # Convert pixel coordinates to latitude/longitude coordinates
    west, north = pixel_xy_to_long_lat(pixelX1, pixelY1, zoomLevel)
    east, south = pixel_xy_to_long_lat(pixelX2, pixelY2, zoomLevel)
    return LngLatBbox(west=west, south=south, east=east, north=north)

def tiles(min_lon, min_lat, max_lon, max_lat, zoom_level):
    """Generate a list of Tile objects for the given bounding box and zoom level."""
    tiles = []
    
    # Get the tile coordinates for the bounding box at the specified zoom level
    min_tile = lat_lon_to_tile(min_lat, min_lon, zoom_level)
    max_tile = lat_lon_to_tile(max_lat, max_lon, zoom_level)
    
    for x in range(min_tile.x, max_tile.x + 1):
        for y in range(min_tile.y, max_tile.y + 1):
            tiles.append(Tile(x=x, y=y, z=zoom_level))
    
    return tiles

