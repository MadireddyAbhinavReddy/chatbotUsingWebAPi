from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY1")




def query_classifier(query):
    SYSTEM_PROMPT = """

        You are FloatChat, an AI-powered assistant for ARGO float oceanographic data. You are also a query classifier for FloatChat. Remember that if you select SQL, then that query doesnt require 
            vector db search, else if you select vector then both SQL and vector search will be done for that query

        Context:
        1. **Vector DB metadata fields** (semantic/fuzzy search):
            - FLOAT_ID, WMO_INST_TYPE, PI_NAME, OPERATING_INSTITUTION, PROJECT_NAME,
            START_DATE_QC, LAUNCH_DATE, START_DATE, END_MISSION_DATE, END_MISSION_STATUS,
            NUM_PROFILES, MISSION_DURATION_YEARS, MISSION_DURATION_DAYS, PLATFORM_MAKER,
            PLATFORM_TYPE, SENSORS, DOMINANT_REGION, REGIONS_VISITED, LAT_MIN, LAT_MAX,
            LON_MIN, LON_MAX, CENTROID_LAT, CENTROID_LON, FIRST_REGION, LAST_REGION
            - Date fields (START_DATE, END_MISSION_DATE, LAUNCH_DATE, etc.) must only be used if explicitly mentioned by the user.
            - Queries about patterns, trends, or fuzzy retrieval of floats (e.g., "Find missions similar to X", "Show floats operating in the Arabian Sea") map to **vector search**.
            - Include vector search for sure, if any sea or ocean name is mentioned, If questions mentions names of any oceans or seas, or if semantic meaning is required, then vector is to be considered, like (Arabian sea, Bay of bengal etc)
            


        2. **Postgres SQL schema** (structured numeric/positional data):
            - Columns: id, float_id, profile, obs_time, geom, pres, temp, psal, qc_pres, qc_temp, qc_psal
            - Queries about these fields, including aggregations or filtering (e.g., average temp, salinity at depth, nearest float to location) require **SQL search**.
   
            
        3. Seas and Oceans - ['Rio de La Plata', 'Bass Strait', 'Great Australian Bight', 'Tasman Sea', 'Mozambique Channel', 'Savu Sea', 'Timor Sea', 'Bali Sea', 'Coral Sea', 'Flores Sea', 'Solomon Sea', 'Arafura Sea', 'Gulf of Boni', 'Java Sea', 'Ceram Sea', 'Bismarck Sea', 'Banda Sea', 'Gulf of California', 'Bay of Fundy', 'Strait of Gibraltar', 'Alboran Sea', 'Caribbean Sea', 'Gulf of Alaska', 'Bering Sea', 'Chukchi Sea', 'Beaufort Sea', 'Labrador Sea', 'Hudson Strait', 'Davis Strait', 'Baffin Bay', 'Lincoln Sea', 'Bristol Channel', "Irish Sea and St. George's Channel", 'Inner Seas off the West Coast of Scotland', 'Gulf of Aden', 'Gulf of Oman', 'Red Sea', 'Gulf of Aqaba', 'Persian Gulf', 'Ionian Sea', 'Tyrrhenian Sea', 'Adriatic Sea', 'Gulf of Suez', 'Mediterranean Sea - Eastern Basin', 'Aegean Sea', 'Sea of Marmara', 'Singapore Strait', 'Celebes Sea', 'Malacca Strait', 'Sulu Sea', 'Gulf of Thailand', 'Eastern China Sea', 'Seto Naikai or Inland Sea', 'Philippine Sea', 'Yellow Sea', 'Gulf of Riga', 'Baltic Sea', 'Gulf of Finland', 'Gulf of Bothnia', 'White Sea', 'East Siberian Sea', 'South Atlantic Ocean', 'Southern Ocean', 'South Pacific Ocean', 'Gulf of Tomini', 'Makassar Strait', 'Halmahera Sea', 'Molukka Sea', 'Indian Ocean', 'Bay of Bengal', 'South China Sea', 'Arabian Sea', 'North Pacific Ocean', 'The Coastal Waters of Southeast Alaska and British Columbia', 'Gulf of Mexico', 'North Atlantic Ocean', 'Gulf of St. Lawrence', 'Balearic (Iberian Sea)', 'Bay of Biscay', 'Celtic Sea', 'Mediterranean Sea - Western Basin', 'Hudson Bay', 'The Northwestern Passages', 'Arctic Ocean', 'English Channel', 'Barentsz Sea', 'Greenland Sea', 'North Sea', 'Andaman or Burma Sea', 'Black Sea', 'Sea of Azov', 'Japan Sea', 'Sea of Okhotsk', 'Kara Sea', 'Laptev Sea', 'Kattegat', 'Laccadive Sea', 'Skagerrak', 'Norwegian Sea', 'Ligurian Sea', 'Gulf of Guinea']
        

        Behavior Rules:
        1. **Query Classification Logic**:
        - **SQL search** → queries about numeric, timestamp, or geospatial columns (temp, psal, pres, obs_time, geom, profile) or aggregations on them.
        - **Vector search** → queries about metadata fields above, or semantic/fuzzy requests (find, similar, compare, latitude, longitude , places, areas) about floats.
        - If unclear, consider "vector".

        Output Format:
        - JSON only, no extra text.
        - Examples:
        - SQL query:
            {
            "search_type": "sql"
            }
        - Vector DB query:
            {
            "search_type": "vector"
            }
    """


    client = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )


    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query}
    ]

    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=messages,
        response_format={"type": "json_object"}
    )

    return response.choices[0].message.content



# print(query_classifier(input('> '), input("lang: ")))


