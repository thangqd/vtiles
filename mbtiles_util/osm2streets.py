import osmium
import pandas as pd
import geopandas as gpd
import shapely.wkb as wkblib
from shapely import geometry


region = "yemen"

class StreetsHandler(osmium.SimpleHandler):
    def __init__(self):
        osmium.SimpleHandler.__init__(self)
        self.num_nodes = 0
        self.num_relations = 0
        self.num_ways = 0
        self.street_relations = []
        self.street_relation_members = []
        self.street_ways = []
        # A global factory that creates WKB from a osmium geometry
        self.wkbfab = osmium.geom.WKBFactory()

    def way(self, w):
        if w.tags.get("highway") is not None and w.tags.get("name") is not None:
            try:
                wkb = self.wkbfab.create_linestring(w)
                geo = wkblib.loads(wkb, hex=True)
            except:
                return

            row = { "w_id": w.id, "geo": geo }
           
            for key, value in w.tags:
                row[key] = value
                
            self.street_ways.append(row)
            self.num_ways += 1 
        
    def relation(self, r):
        if r.tags.get("type") == "associatedStreet" and r.tags.get("name") is not None:
            row = { "r_id": r.id }
            for key, value in r.tags:
                row[key] = value
            self.street_relations.append(row)
            
            for member in r.members:
                self.street_relation_members.append({ 
                    "r_id": r.id, 
                    "ref": member.ref, 
                    "role": member.role, 
                    "type": member.type, })

            self.num_relations += 1

handler = StreetsHandler()

# path to file to local drive
# download from https://download.geofabrik.de/index.html
osm_file = f"../data/yemen.pbf"

# start data file processing
handler.apply_file(osm_file, locations=True, idx='flex_mem') # 'flex_mem'

# show stats
print("Pbf info: ")
print(f"num_relations: {handler.num_relations}")
print(f"num_ways: {handler.num_ways}")
print(f"num_nodes: {handler.num_nodes}")

# create dataframes
street_relations_df = pd.DataFrame(handler.street_relations)
street_relation_members_df = pd.DataFrame(handler.street_relation_members)
street_ways_df = pd.DataFrame(handler.street_ways)

streets_df = pd.merge(street_ways_df, street_relation_members_df, left_on="w_id", right_on="ref", how="left", suffixes=["_way", ""])
streets_df = pd.merge(streets_df, street_relations_df, left_on="r_id", right_on="r_id", how="left", suffixes=["", "_rel"])
streets_df["id"] = 'w' + streets_df['w_id'].astype(str)

# merge name and wikidata property from both ways and relations data

if "wikidata_rel" in streets_df.columns:
    streets_df['wikidata_merged'] = streets_df.wikidata.combine_first(streets_df.wikidata_rel)
else:
    streets_df['wikidata_merged'] = streets_df.wikidata
streets_df['name_merged'] = streets_df.name.combine_first(streets_df.name_rel)
streets_df['name_merged'] = streets_df.name.combine_first(streets_df.name_rel)

if "uk_rel" in streets_df.columns:
    streets_df['name:uk_merged'] = streets_df["name:uk"].combine_first(streets_df["name:uk_rel"])
elif "name:uk" in streets_df.columns:
    streets_df['name:uk_merged'] = streets_df["name:uk"]
else:
    streets_df['name:uk_merged'] = None

if "en_rel" in streets_df.columns:
    streets_df['name:en_merged'] = streets_df["name:en"].combine_first(streets_df["name:en_rel"])
else:
    streets_df["name:en"]

streets_gdf = gpd.GeoDataFrame(streets_df, geometry="geo")
print("Street GDF:")
print(streets_gdf)


relation_streets = []
for street_relation in street_relations_df.iterrows():
    r_id = street_relation[1]["r_id"]
    name = street_relation[1]["name"]
    if "name:uk" in street_relation[1]:
        name_uk = street_relation[1]["name:uk"]
    else:
        name_uk = None
        
    if "name:ru" in street_relation[1]:
        name_ru = street_relation[1]["name:ru"]
    else:
        name_ru = None
    
    if "name:en" in street_relation[1]:
        name_en = street_relation[1]["name:en"]
    else:
        name_en = None
    
    if "wikidata" in street_relation[1]:
        wikidata = street_relation[1]["wikidata"]
    else:
        wikidata = None
    
    mline = geometry.MultiLineString(streets_gdf[streets_gdf.r_id == r_id].geo.array)
    
    relation_streets.append({ "id": f"r{r_id}", "geo": mline, "name": name, 
                             "name:uk": name_uk, "name:en": name_en,
                             "wikidata": wikidata })
        
relation_streets_df = pd.DataFrame(relation_streets)
way_streets_df = streets_df[streets_df["r_id"].isna()][["id", "geo", "name", "name:en", "wikidata"]]

rw_streets_df = pd.concat([relation_streets_df, way_streets_df])
rw_streets_gdf = gpd.GeoDataFrame(rw_streets_df, geometry="geo", crs=4326)
rw_streets_gdf.to_csv(f"../data_{region}.csv")
print('rw_streets_gdf')

print (rw_streets_gdf)
# rw_streets_gdf.plot(figsize=(20,30))

