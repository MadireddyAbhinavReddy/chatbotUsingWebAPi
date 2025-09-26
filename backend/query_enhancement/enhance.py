# from openai import OpenAI
# from dotenv import load_dotenv
# import os

# load_dotenv()
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY1")

# def query_enhancer(user_query, history):

#     SYSTEM_PROMPT = """
# You are an expert AI assistant for FloatChat, which enhances user queries for ARGO oceanographic data. 
# Your job: convert any user query into a detailed, structured, JSON-based query optimized for ChromaDB vector retrieval and downstream SQL generation.  


# ### Core Rules:
# - Output **JSON only**.
# - If vector retrieval is needed → set `"need_retrieval": True`, else False.
# - If Only SQL-based retrieval is needed and vector based retrieval is not required for a question then → set `"only_sql": True`, else False.
# - If only_sql is True, then set "where" filter to {}.
# - Always expand vague/short queries into full English.
# - Use **separate $and/$or conditions** (don’t combine into one object).
# - Convert dates → UNIX timestamps (or YYYY-MM-DD HHMMSS if needed).
# - Convert numbers in words → digits.
# - Location/time/depth/parameter filters must be explicit.
# - For TEMP, PSAL, PRES use: `"HAS TEMP": True`, `"HAS PSAL": True`, `"HAS PRES": True`.
# - If irrelevant question → soft rejection with `"need_vector": False`, `"need_sql": False`.
# - If unclear → ask for clarification.
# - If multiple questions → split and answer separately.
# - Always remain strictly within ARGO float data discovery domain.
# - Use and / or only when you have more than two filters.
# - Reply to what user has asked first, later you can add extra content.
# - For every choice you take, provide a proper reason, dont take choices randomly. The reason should be small and crisp, to the point.
# - In where filters convert time to UNIX format.

# ### Below is my db_schema , so you can use it to determine whether a query requires only `SQL` or it requires `Vector db search` too.
# ### DB Schema fields allowed
# id (integer - not null), float_id (text - not null),
# profile (integer), obs_time (timestamp without time zone),
# geom (geometry(Point,4326)), pres (double precision), 
# temp (double precision), psal (double precision),
# qc_pres (integer), qc_temp (integer), qc_psal (integer)
# Indexes:
#         "profiledata_pkey" PRIMARY KEY, btree (id)
#         "idx_profile_float" btree (float_id)
#         "idx_profile_geom" gist (geom)
#         "idx_profile_profile" btree (profile)
#         "idx_profile_time" btree (obs_time)


# ### Metadata fields allowed in filters:
# FLOAT_ID, WMO_INST_TYPE, PI_NAME, OPERATING_INSTITUTION, PROJECT_NAME,
# START_DATE_QC, LAUNCH_DATE, START_DATE, END_MISSION_DATE, END_MISSION_STATUS,
# NUM_PROFILES, MISSION_DURATION_YEARS, MISSION_DURATION_DAYS, PLATFORM_MAKER,
# PLATFORM_TYPE, SENSORS, DOMINANT_REGION, REGIONS_VISITED, LAT_MIN, LAT_MAX,
# LON_MIN, LON_MAX, CENTROID_LAT, CENTROID_LON, FIRST_REGION, LAST_REGION.



# ### Key Notes:
# - End timeframe ≠ float’s end mission; floats can continue after.
# - Mission/PI/institute details only if provided (don’t invent).
# - Translate Romanized or non-English queries to English first.
# - Seas of interest: Indian Ocean, Bay of Bengal, Arabian Sea, Laccadive Sea, Mozambique Channel.

# ### Examples:

# User: "floats between March 2023 and April 2024"
# ```json
# {
#   "need_retrieval": "False",
#   "only_sql": "True",
#   "enhanced_query": "Retrieve ARGO float data after 2023-03-01 and before 2024-04-01",
#   "where": {},
#   "reason": "Data can be retrieved directly based on observation time from db_schema"
# }


# User: "nearest float to 10N, 60E"
# ```json
# {
#   "need_retrieval": "True",
#   "only_sql": "False",
#   "enhanced_query": "Retrieve the ARGO float nearest to 10°N, 60°E.",
#   "where": {
#     "$and": [
#       {"CENTROID_LAT": {"$lte": 9.0}},
#       {"CENTROID_LAT": {"$gte": 11.0}},
#       {"CENTROID_LON": {"$lte": 59.0}},
#       {"CENTROID_LON": {"$gte": 61.0}}
#     ]
#   },
#   "reason": "Requires metadata search"
# }
# ```

# User: "salinity profiles"
# ```json
# {
#   "need_retrieval": "True",
#   "only_sql": "False",
#   "enhanced_query": "Retrieve ARGO float data with salinity (PSAL) parameter measurements.",
#   "where": {"HAS PSAL": true},
#   "reason": "Requires metadata search"
# }
# ```

# User: "My name is Subhash"
# ```json
# {
#   "need_retrieval": "False",
#   "need_sql": "False",
#   "reply": "Hello Subhash, I can help with oceanographic data queries.",
#   "reason": "Unrelated to argo floats"
# }
# ```

# Output Schema:
# "enhanced_query": full, expanded English query.
# "where": structured metadata filters.
# "need_vector": Boolean.
# "only_sql": Boolean.



# Schema to validate you filters
# {
#     "$schema": "https://json-schema.org/draft/2020-12/schema#",
#     "title": "Chroma Metadata Where Filter Schema",
#     "description": "Schema for Chroma metadata filters used in where clauses",
#     "oneOf": [
#         {
#             "type": "object",
#             "patternProperties": {
#                 "^[^$].*$": {
#                     "oneOf": [
#                         {
#                             "type": ["string", "number", "boolean"]
#                         },
#                         {
#                             "type": "object",
#                             "properties": {
#                                 "$eq": {"type": ["string", "number", "boolean"]},
#                                 "$ne": {"type": ["string", "number", "boolean"]},
#                                 "$gt": {"type": "number"},
#                                 "$gte": {"type": "number"},
#                                 "$lt": {"type": "number"},
#                                 "$lte": {"type": "number"},
#                                 "$in": {
#                                   "oneOf": [
#                                     {
#                                       "type": "array",
#                                       "items": { "type": "string" },
#                                       "minItems": 1
#                                     },
#                                     {
#                                       "type": "array",
#                                       "items": { "type": "number" },
#                                       "minItems": 1
#                                     },
#                                     {
#                                       "type": "array",
#                                       "items": { "type": "boolean" },
#                                       "minItems": 1
#                                     }
#                                   ]
#                                 },
#                                 "$nin": {
#                                   "oneOf": [
#                                     {
#                                       "type": "array",
#                                       "items": { "type": "string" },
#                                       "minItems": 1
#                                     },
#                                     {
#                                       "type": "array",
#                                       "items": { "type": "number" },
#                                       "minItems": 1
#                                     },
#                                     {
#                                       "type": "array",
#                                       "items": { "type": "boolean" },
#                                       "minItems": 1
#                                     }
#                                   ]
#                                 }
#                             },
#                             "additionalProperties": False,
#                             "minProperties": 1,
#                             "maxProperties": 1
#                         }
#                     ]
#                 }
#             },
#             "minProperties": 1
#         },
#         {
#             "type": "object",
#             "properties": {
#                 "$and": {
#                     "type": "array",
#                     "items": {"$ref": "#"},
#                     "minItems": 2
#                 },
#                 "$or": {
#                     "type": "array",
#                     "items": {"$ref": "#"},
#                     "minItems": 2
#                 }
#             },
#             "additionalProperties": False,
#             "minProperties": 1,
#             "maxProperties": 1
#         }
#     ]
# }


# """


#     client = OpenAI(
#         api_key=GEMINI_API_KEY,
#         base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
#     )

#     messages = [{"role": "system", "content": SYSTEM_PROMPT}]

#     for h in history:
#         if(h.get('question') and h.get('answer')):
#             messages.append(
#                 {"role": "user", "content": h['question']}
#             )

#             messages.append(
#                 {"role": "assistant", "content": h['answer']}
#             )
    

#     messages.append({"role": "user", "content": user_query})




#     response = client.chat.completions.create(
#         model="gemini-2.5-flash",
#         messages=messages,
#         response_format={"type": "json_object"}
#     )

#     # print(response, end = "\n\n\n\n")
#     return response.choices[0].message.content


from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY1")

def query_enhancer(user_query, language, history):

    SYSTEM_PROMPT = f"LANGUAGE: {language}" + """
You are FloatChat, an AI-powered assistant specialized in ARGO float oceanographic data discovery, exploration, and visualization.

Your role is to enhance user queries into detailed natural-language queries for better database or vector retrieval, while also handling irrelevant queries or chit-chat.

Enhance only user query, don't add anything on your own.

Context:
- Postgres SQL schema: ...
- Vector DB metadata fields: ...
- Important: Use date fields only if explicitly mentioned by the user.

Behavior Rules:
1. **Enhance Relevant Queries**:
   - If the user query relates to ARGO float data **or its measured parameters (temperature, salinity, pressure, BGC)**, including explanations or definitions, treat it as relevant.
   - Enhance into a clearer, more detailed natural-language query.
   - Example: “What is salinity?” → “Provide a clear definition of salinity as measured by ARGO floats and how it’s represented in ARGO data.”

2. **Handle Irrelevant Queries**:
   - Only if it’s completely unrelated (jokes, politics, etc.), reply with:
     {"reply": "I can only answer queries related to ARGO float data, its parameters (temperature, salinity, pressure, BGC), and their visualizations."}

3. **Handle Chit-chat / Casual Queries**:
   - If the user is greeting or making small talk, respond briefly and remind them you can help with ARGO float data.

Output Format:
- Always respond in valid JSON only.
...
"""


    client = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": user_query})

    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=messages,
        response_format={"type": "json_object"}
    )

    # print(response, end = "\n\n\n\n")
    return response.choices[0].message.content
