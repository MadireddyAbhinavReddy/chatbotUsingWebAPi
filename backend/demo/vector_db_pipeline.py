from identify_drift.drift import get_sea_from_lat_lon
import pandas as pd
from collections import Counter
import xarray as xr
from datetime import datetime
from generate_summary.summary import create_summary
import numpy as np
from store_in_vector_db.vector_db import add_documents, query_documents, generate_embeddings
import os


def clean_metadata(meta: dict) -> dict:
    """Ensure all metadata values are JSON-serializable for Chroma Cloud."""
    clean = {}
    for k, v in meta.items():
        if v is None:
            # Replace None with safe default
            clean[k] = ""  # or 0 for numeric fields if it makes sense
        elif isinstance(v, (np.float32, np.float64)):
            clean[k] = float(v)
        elif isinstance(v, (np.int32, np.int64)):
            clean[k] = int(v)
        elif isinstance(v, (list, tuple, np.ndarray)):
            # Flatten list/array to string
            for x in v:
                clean[f'HAS {x}'] = True
            clean[k] = ", ".join([str(x) for x in v])
        elif isinstance(v, datetime):
            clean[k] = v.isoformat()
        elif isinstance(v, bool):
            clean[k] = v
        else:
            # everything else as string
            clean[k] = v
    return clean



def decode_bytes_field(field):
    """Decodes scalar metadata field safely into a string."""
    val = field.values if hasattr(field, "values") else field

    if isinstance(val, np.ndarray) and val.ndim == 0:
        val = val.item()

    if isinstance(val, bytes):
        return val.decode("utf-8").strip()
    elif isinstance(val, (np.float32, np.float64, float, int)):
        return str(val).strip()
    elif val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    else:
        return str(val).strip()


def decode_bytes_list(field):
    """Decodes array/list metadata safely into list of strings."""
    val = field.values if hasattr(field, "values") else field

    if isinstance(val, np.ndarray):
        return [decode_bytes_field(x) for x in val.tolist()]
    elif isinstance(val, (list, tuple)):
        return [decode_bytes_field(x) for x in val]
    elif isinstance(val, bytes):
        return [val.decode("utf-8").strip()]
    elif val is None or (isinstance(val, float) and np.isnan(val)):
        return []
    else:
        return [str(val).strip()]

    

def decode_date_field(field):
    val = metadata[field]
    raw = decode_bytes_field(val)   # already safe string now

    if raw == "" or raw.lower() == "nan":
        return None

    try:
        return datetime.strptime(raw, "%Y%m%d%H%M%S")
    except Exception:
        return None


###--- Ikkada start --- ###

BASE_DIR = "./argo_data"
floats_ids = sorted([f for f in os.listdir(BASE_DIR)])


count = 1
for float_id in floats_ids:

    try:
        print("Float id : ",float_id)

        data = {}

        float_df = pd.read_csv(f'argo_data/{float_id}/{float_id}_prof.csv')
        float_df['Date'] = pd.to_datetime(float_df['Date'], errors='coerce')
        float_df['Date'] = float_df['Date'].dt.strftime('%y-%m-%d %H:%M:%S')
        metadata = xr.open_dataset(f"argo_data/{float_id}/{float_id}_meta.nc")



        unique_profiles = float_df.groupby(["Profile"], as_index=False).agg({
                            "Latitude": "first",
                            "Longitude": "first" 
                        })



        unique_profiles = unique_profiles[["Profile", "Latitude", "Longitude"]]
        first_loc, last_loc = "", ""

        locations = []
        for idx, row in unique_profiles.iterrows():
            # print("Profile : ", row['Profile'], row['Latitude'], row['Longitude'])
            loc = get_sea_from_lat_lon(row['Latitude'], row['Longitude'])
            locations.append(loc)

            if(idx == 0):
                first_loc = loc
            
            elif(idx == len(unique_profiles) - 1):
                last_loc = loc


        locations_d = Counter(locations)
        # print(locations_d)

        dominant_region = ""
        dominant_count = 0
        mx = 0
        for k, v in locations_d.items():
            if(v > mx):
                mx = v
                dominant_region = k
                dominant_count = mx


        # adv - i just added some that chatgpt gave, if they are wrong or additional are there add.....
        status = {
            "T": "Terminated",
            "D": "Dropped",
            "R": "Recovered",
            "F": "Technical Failure",
            "S": "Stopped",
            "U": "Unknown"
        }


        # drift summary
        data['FIRST_REGION'] = first_loc
        data['LAST_REGION'] = last_loc
        data['LAT_MIN'] = unique_profiles["Latitude"].min()
        data['LAT_MAX'] = unique_profiles['Latitude'].max()
        data['LON_MIN'] = unique_profiles["Longitude"].min()
        data['LON_MAX'] = unique_profiles['Longitude'].max()
        data['CENTROID_LAT'] = unique_profiles['Latitude'].mean()
        data['CENTROID_LON'] = unique_profiles['Longitude'].mean()
        data['REGIONS_VISITED'] = ", ".join(list(locations_d.keys()))
        for reg in locations_d.keys():
            data[f'VISITED {reg.upper()}'] = True
        data['DOMINANT_REGION'] = dominant_region
            

        # float summary
        data['FLOAT_ID'] = float_id
        data['WMO_INST_TYPE'] = decode_bytes_field(metadata['WMO_INST_TYPE'])
        data['PI_NAME'] = decode_bytes_field(metadata['PI_NAME'])
        data['OPERATING_INSTITUTION'] = decode_bytes_field(metadata['OPERATING_INSTITUTION'])
        data['PROJECT_NAME'] = decode_bytes_field(metadata['PROJECT_NAME'])


        # date summary
        ldt = decode_date_field('LAUNCH_DATE')
        ld = None
        if(ldt != None):
            ld = int(ldt.timestamp())
        data['LAUNCH_DATE'] = ld
        data['LAUNCH_LATITUDE'] = np.ndarray.tolist(metadata['LAUNCH_LATITUDE'].values)
        data['LAUNCH_LONGITUDE'] = np.ndarray.tolist(metadata['LAUNCH_LONGITUDE'].values)

        sdt = decode_date_field('START_DATE')
        sd = None
        if(sdt != None):
            sd = int(sdt.timestamp())
        data['START_DATE'] = sd

        edt = decode_date_field('END_MISSION_DATE')
        ed = None
        if(edt != None):
            ed = int(edt.timestamp())
        data['END_MISSION_DATE'] = ed

        if(metadata['END_MISSION_STATUS'] == None):
            s = "Mission not yet completed"
        elif(status.get(decode_bytes_field(metadata['END_MISSION_STATUS'])) == None):
            s = decode_bytes_field(metadata['END_MISSION_STATUS'])
        else:
            s = status.get(decode_bytes_field(metadata['END_MISSION_STATUS']))
        data['END_MISSION_STATUS'] = s

        data['NUM_PROFILES'] = len(unique_profiles)

        data['PCT_IN_DOMINANT_REGION'] = round((dominant_count / len(unique_profiles)) * 100, 2)

        if(sdt and edt):

            data['MISSION_DURATION_YEARS'] = round((edt - sdt).days/365, 2)

            data['MISSION_DURATION_DAYS'] = (edt - sdt).days
        
        else:

            if(edt == None and sdt != None):
                data['MISSION_DURATION_YEARS'] = round((datetime.now().replace(microsecond=0) - sdt).days/365, 2)
                data['MISSION_DURATION_DAYS'] = (datetime.now().replace(microsecond=0) - sdt).days
            
            else:
                data['MISSION_DURATION_YEARS'] = None
                data['MISSION_DURATION_DAYS'] = None


        data['START_DATE_QC'] = decode_bytes_field(metadata['START_DATE_QC'])

        data['PLATFORM_TYPE'] = decode_bytes_field(metadata['PLATFORM_TYPE'])

        data['PLATFORM_MAKER'] = decode_bytes_field(metadata['PLATFORM_MAKER'])

        # sensor summary
        sensors = decode_bytes_list(metadata['SENSOR'])
        makers = decode_bytes_list(metadata['SENSOR_MAKER'])
        models = decode_bytes_list(metadata['SENSOR_MODEL'])
        serials = decode_bytes_list(metadata['SENSOR_SERIAL_NO'])
        params = decode_bytes_list(metadata['PARAMETER'])
        units = decode_bytes_list(metadata['PARAMETER_UNITS'])

        # print(sensors, makers, models, serials, params, units)

        sensor_summary = []
        for s, mkr, mdl, sn, p, u in zip(sensors, makers, models, serials, params, units):
            sensor_summary.append({
                "Sensor": s,
                "Maker": mkr,
                "Model": mdl,
                "SerialNo": sn,
                "Parameter": p,
                "Units": u
            })

        summary = ["Sensor_summary:"]
        for s in sensor_summary:
            summary.append(f"Sensor: {s['Sensor']} | Maker: {s['Maker']} | Model: {s['Model']} | SerialNo: {s['SerialNo']} | Parameter: {s['Parameter']} | Units: {s['Units']}")

        summary = "\n".join(summary)

        data['SENSORS'] = summary
        data['PARAMETER'] = params

        for p in params:
            data[f'HAS {p.upper()}'] = True

        ######################################################################################################

        # data -> metadata ------------------------------------------------------------------- avdaith

        summ = create_summary(data)
        data = clean_metadata(data)
        # here call another function to store summary and data in chroma 


        # print(summ, data, end="\n\n")

        embeddings = generate_embeddings(summ)

        # print("embeddings : ", embeddings[0].values, end="\n\n")

        add_documents(summ, data, embeddings, float_id)
        # query_documents("Indian Ocean")

        print(count)
        count+=1

    

    except Exception as e:
        print(f"Error : {e}", end="\n\n")


    