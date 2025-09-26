def create_summary(data):

    summary = f"""

    Float {data['FLOAT_ID']} (WMO {data['WMO_INST_TYPE']}), deployed by {data['PI_NAME']} from {data['OPERATING_INSTITUTION']} under {data['PROJECT_NAME']} with start date qc : {data['START_DATE_QC']}, 
    was launched on {data['LAUNCH_DATE']} at Latitude {data['LAUNCH_LATITUDE']}, Longitude {data['LAUNCH_LONGITUDE']}.

    Mission Duration: {data['START_DATE']} to {data['END_MISSION_DATE']} ({data['END_MISSION_STATUS']}), 
    collecting {data['NUM_PROFILES']} profiles over {data['MISSION_DURATION_YEARS']} years or {data['MISSION_DURATION_DAYS']} days.

    Platform Maker: {data['PLATFORM_MAKER']} and Platform Type: {data['PLATFORM_TYPE']}

    Sensors: {data['SENSORS']}

    Drift Summary:
    - Dominant Region: {data['DOMINANT_REGION']} ({data['PCT_IN_DOMINANT_REGION']}% of profiles)
    - Regions Visited: {data['REGIONS_VISITED']}
    - Latitude: {data['LAT_MIN']} to {data['LAT_MAX']}, Longitude: {data['LON_MIN']} to {data['LON_MAX']}
    - Centroid: Latitude {data['CENTROID_LAT']}, Longitude {data['CENTROID_LON']}
    - First Visited Region: {data['FIRST_REGION']}, Last Visited Region: {data['LAST_REGION']}

    """


    return summary