# Reference: https://github.com/openmaptiles/openmaptiles-tools/blob/master/openmaptiles/mbtile_tools.py

# SELECT zoom_level, COUNT(*) AS count,
#        MIN(tile_column) AS min_column, MAX(tile_column) AS max_column,
#        MIN(tile_row) AS min_row, MAX(tile_row) AS max_row
# FROM map
# GROUP BY zoom_level
# """
#                 res = []
#                 for z, cnt, min_x, max_x, min_y, max_y in sorted(query(conn, sql, [])):
#                     res.append({
#                         'Zoom': z,
#                         'Tile count': f'{cnt:,}',
#                         'Found tile ranges': f'{min_x},{min_y} x {max_x},{max_y}',
#                     })
#                 print('\n' + tabulate(res, headers='keys'))