# import os
# from dotenv import load_dotenv
# from openai import OpenAI
# import json


# load_dotenv()
# GEMINI_API_KEY=os.getenv('GEMINI_API_KEY3')
# db_schema = """

#         Column  |            Type             | Collation | Nullable |                 Default                 
#     ----------+-----------------------------+-----------+----------+-----------------------------------------
#     id       | integer                     |           | not null | nextval('profiledata_id_seq'::regclass)
#     float_id | text                        |           | not null | 
#     profile  | integer                     |           |          | 
#     obs_time | timestamp without time zone |           |          | 
#     geom     | geometry(Point,4326)        |           |          | 
#     pres     | double precision            |           |          | 
#     temp     | double precision            |           |          | 
#     psal     | double precision            |           |          | 
#     qc_pres  | integer                     |           |          | 
#     qc_temp  | integer                     |           |          | 
#     qc_psal  | integer                     |           |          | 
#     Indexes:
#         "profiledata_pkey" PRIMARY KEY, btree (id)
#         "idx_profile_float" btree (float_id)
#         "idx_profile_geom" gist (geom)
#         "idx_profile_profile" btree (profile)
#         "idx_profile_time" btree (obs_time)

# """


# def clean_response(res):
#     if isinstance(res, str):
#         s = res.strip()

#         # print(s)
#         if(s.startswith("```")):
#             s = s.strip("`")
        
#         # print(s)
#         if(s.startswith("sql")):
#             s = s.strip("sql")
        

#         try:
#             cleaned_response = json.loads(s)
        
#         except json.JSONDecodeError:
#             cleaned_response = s
    
#     else:
#         cleaned_response = res


#     # print("TYPE: ", type(cleaned_response))
#     return cleaned_response




# def sql_generator(query, retrieved_data):
#     # print("Retrieved data : ", retrieved_data)

#     SYSTEM_PROMPT = f"""
# You are an expert PostgreSQL query generator whose primary goal is to provide **accurate and efficient SQL** to answer user queries.

# Database schema:
# {db_schema}

# User request:
# {query}

# Relevant float_ids from vector DB:
# {retrieved_data}

# Rules for generating SQL:
# - Use only SELECT statements (no INSERT/UPDATE/DELETE/DDL).
# - Table: profileData (do not quote or pluralize the name).
# - Always wrap column names in double quotes, exactly as in schema.
# - Always use releveant data type for that particular data you are representing
# - For dates:
#   • User input is TEXT in YYYY-MM-DD format.
#   • Cast to DATE when filtering, e.g. "obs_time"::DATE BETWEEN '2022-01-01' AND '2022-12-31'.
# - "float_id" is TEXT → wrap numeric IDs in single quotes.
# - Always terminate with a semicolon (;).
# - Return output ONLY in valid JSON (see format below), no commentary or extra text.
# - In general assume that data will be very large, so prefer performing aggregations most of the times.

# Handling data volume:
# 1. For **small/narrow queries** (short date range, few float_ids, or single profile):
#    - Return raw rows directly.
#    - Set "data_size": "small", "aggregation_used": false, "suggest_plot": false.
# 2. For **large/broad queries** (long date ranges, many float_ids, or entire dataset):
#    - Do NOT return all rows.
#    - Use meaningful aggregates (AVG, MIN, MAX, COUNT, SUM) for numeric columns.
#    - Group data to reduce volume (e.g., by month, float_id, or profile).
#    - Ensure the aggregates are representative and accurate.
#    - Set "data_size": "large", "aggregation_used": true, "suggest_plot": true.
# 3. If the volume is unclear, **default to aggregation and summarization**, and mark "data_size": "large".
# 4. Finally provide sources to cite for user to verify from the data you have. Dont invent sources yourself.

# Optimization & Accuracy:
# - Only select columns necessary to answer the user query.
# - Ensure numeric data types are aggregated correctly and NULLs are handled appropriately.
# - Always filter using relevant float_ids and date ranges to minimize output.
# - Avoid sending excessive rows to the LLM; summarize whenever possible.

# Return Format (JSON only):
# {{
#   "sql_query": "VALID_SQL_QUERY;",
#   "data_size": "small" | "large",
#   "aggregation_used": true | false,
#   "suggest_plot": true | false,
#   "sources_to_cite": string
# }}
# """

#     client = OpenAI(
#         api_key=GEMINI_API_KEY,
#         base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
#     )


#     response = client.chat.completions.create(
#         model = "gemini-2.5-flash",
#         messages=[
#             {"role": "system", "content": SYSTEM_PROMPT},
#             {
#                 "role": "user",
#                 "content": query
#             }
#         ],
#         response_format={"type": "json_object"}
#     )



#     return clean_response(response.choices[0].message.content)


import os
from dotenv import load_dotenv
from openai import OpenAI
import json


load_dotenv()
GEMINI_API_KEY=os.getenv('GEMINI_API_KEY3')

def clean_response(res):
    if isinstance(res, str):
        s = res.strip()
        if s.startswith("```"):
            s = s.strip("`")
        if s.startswith("sql"):
            s = s.strip("sql")
        
        try:
            cleaned_response = json.loads(s)
        except json.JSONDecodeError:
            cleaned_response = s
    else:
        cleaned_response = res
    
    return cleaned_response

def sql_generator(query, type, retrieved_data=None):
    SYSTEM_PROMPT = f"""
You are an expert PostgreSQL query generator. You always produce one and only one valid SQL SELECT statement.

Context:
Database schema:
    - Postgres SQL schema (structured numeric/geospatial data): 
      "id", "float_id", "Profile", "Date", "Latitude", "Longitude", "Pres_raw(dbar)", "Pres_adj(dbar)", "Pres_raw_qc", "Pres_adj_qc", 
      "Temp_raw(C)", "Temp_adj(C)", "Temp_raw_qc", "Temp_adj_qc", 
      "Psal_raw(psu)", "Psal_adj(psu)", "Psal_raw_qc", "Psal_adj_qc"

User request:
{query}

Relevant float_ids from vector DB:
{retrieved_data}

TYPE : {type}

STRICT RULES:

1. Output only a single valid SQL SELECT query; no explanations, comments, markdown, code fences or formatting. 
   - Never generate INSERT, UPDATE, DELETE, DROP, CREATE, WITH, CTEs, temp tables, or multi-statement SQL.
2. The table name is always exactly profiles.
3. Always wrap column names exactly as shown in the schema in double quotes.
4. "Date" is TEXT in YYYY-MM-DD format.
   - Always cast to DATE for comparisons: "Date"::DATE
   - Valid Postgres date expressions:
       * EXTRACT(YEAR FROM "Date"::DATE) = 2022
       * "Date"::DATE BETWEEN '2022-01-01' AND '2022-12-31'
       * "Date"::DATE >= (CURRENT_DATE - INTERVAL '10 years')
   - DO NOT use DATE('now') or SQLite/MySQL-style functions.
5. "float_id" is TEXT. Always wrap IDs in single quotes.
   - Example: WHERE "float_id" IN ('2902291','3902292')
   - If {retrieved_data} is empty, default to no float_id filter (include all floats).
6. Location filtering:
   - Use "Latitude" and "Longitude" for filtering. If using PostGIS, assume SRID=4326.
7. Only include columns needed to answer the user’s question. Never SELECT * unless explicitly requested.
8. NULL handling:
   - Filter out NULL only if required by query intent or explicitly asked.
9. Data volume handling:
   - Narrow query → return raw rows.
   - Broad query → return aggregates (COUNT, AVG, MIN, MAX, GROUP BY).
10. Sorting:
   - Use ORDER BY only if user explicitly requests ordering.
11. Always terminate query with a semicolon.
12. JSON output:
   - Always return valid JSON in exactly this format, no extra text:
     {{
       "sql": "<generated SQL>",
       "sources_to_cite": "<comma-separated float_ids or 'all' if none provided>"
     }}
13. Safety fallback:
   - If user request is ambiguous, default to a safe aggregated query by "float_id" and year.
14. Strict validation:
   - Double-check your SQL before output. It must run without errors on PostgreSQL.
   - Never hallucinate columns or functions outside the schema above.
15. If type is theory then highly aggregate the data and select random 1000 data points from the data.
16. If possible try including the float_ids, latitude, longitude, and dates. Better if included.

GOAL:
Produce the minimal, correct, performant SQL SELECT query that answers the user’s request, wrapped in valid JSON with cited float_ids.
"""



    client = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )


    response = client.chat.completions.create(
        model = "gemini-2.5-flash",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": query
            }
        ],
        response_format={"type": "json_object"}
    )



    return response.choices[0].message.content

