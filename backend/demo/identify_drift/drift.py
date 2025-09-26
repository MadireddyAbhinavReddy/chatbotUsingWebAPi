import geopandas as gpd
from shapely.geometry import Point
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
shapefile_path = os.path.join(BASE_DIR, "World_Seas_IHO_v3", "World_Seas_IHO_v3.shp")
target_seas = gpd.read_file(shapefile_path)

# regions = ['Bay of Bengal', 'Arabian Sea', 'Indian Ocean']

# target_seas = seas[seas['NAME'].isin(regions)]


def get_sea_from_lat_lon(lat, lon):
    point = Point(lon, lat)
    matched = target_seas[target_seas.contains(point)]
    
    if not matched.empty:
        return matched.iloc[0].iloc[0]

    else:
        return "Unknown"




# import plotly.express as px
# import pandas as pd

# float_df = pd.read_csv('../argo_data/2901092/2901092_prof.csv')

# fig = px.line_geo(float_df,
#                   lat='Latitude',
#                   lon='Longitude',
#                   hover_name='Date',
#                   title=f'Argo Float {1900121} Drift Trajectory',
#                   markers=True)

# fig.update_geos(projection_type="natural earth")
# fig.show()



