import geopandas as gpd
import pyrosm
from pyrosm import get_data
from pyrosm.data import sources
from pyrosm import OSM
import matplotlib.pyplot as plt

# # Initialize the OSM parser object
# osm = pyrosm.OSM(fp)
# buildings = osm.get_buildings()
# print(buildings.head())
# buildings.plot()
# fp = get_data("Helsinki")
# print(fp)
# print("\nDownload will happen:")
# fp = get_data("Helsinki", update=True)
fp = "../data/yemen-latest.osm.pbf"
osm = OSM(fp)
# drive_net = osm.get_network(network_type="driving")
# buildings = osm.get_buildings()
# # Initialize the OSM parser object
# # drive_net.plot()
# # print(drive_net.head(10))
# print(buildings.head(10))
# custom_filter = {'amenity': True, "shop": True}
# pois = osm.get_pois(custom_filter=custom_filter)

# # Gather info about POI type (combines the tag info from "amenity" and "shop")
# pois["poi_type"] = pois["amenity"]
# pois["poi_type"] = pois["poi_type"].fillna(pois["shop"])

# # Plot
# ax = pois.plot(column='poi_type', markersize=3, figsize=(12,12), legend=True, legend_kwds=dict(loc='upper left', ncol=5, bbox_to_anchor=(1, 1)))
# plt.show()
buildings = osm.get_network(network_type="driving")
buildings.plot()
plt.show()

