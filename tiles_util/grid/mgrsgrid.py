
# Reference: https://github.com/pistell/Leaflet.DumbMGRS
# https://mgrs-mapper.com/app, https://military-history.fandom.com/wiki/Military_Grid_Reference_System
# https://codesandbox.io/s/how-to-toggle-react-leaflet-layer-control-and-rectangle-grid-f43xi?file=/src/App.js:1057-1309
# https://github.com/GeoSpark/gridoverlay/tree/d66ed86636c7ec3f02ca2e9298ac3086c2023f1d
# https://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#//00700000001n000000
# https://storymaps.arcgis.com/stories/842edf2b4381438b9a4edefed124775b
# https://github.com/dnlbaldwin/React-Leaflet-MGRS-Graticule
# https://dnlbaldwin.github.io/React-Leaflet-MGRS-Graticule/

from tiles_util.utils.geocode import mgrs
mgrs_code = mgrs.toMgrs(10.63038542, 106.12923131,3)
mgrs_code = mgrs.toMgrs(-84.65698112, -80.69068228,3)


print('mgrs_code: ', mgrs_code)
mgrs_encode = mgrs.toWgs(mgrs_code)
mgrs_encode = mgrs.toWgs('48QYD214738')
print('mgrs_encode: ', mgrs_encode)