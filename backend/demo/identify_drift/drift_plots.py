import geopandas as gpd
from shapely.geometry import Point
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
shapefile_path = os.path.join(BASE_DIR, "World_Seas_IHO_v3", "World_Seas_IHO_v3.shp")
seas = gpd.read_file(shapefile_path)

l = []
for idx, row in seas.iterrows():
    l.append(row['NAME'])

print(l)