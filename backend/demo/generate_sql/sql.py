import os
from dotenv import load_dotenv
from openai import OpenAI
import json


load_dotenv()
GEMINI_API_KEY=os.getenv('GEMINI_API_KEY')
db_schema = """

        Column      |            Type             | Collation | Nullable |                 Default
    ---------------+-----------------------------+-----------+----------+-----------------------------------------
    id             | bigserial                   |           | not null | nextval('profiles_id_seq'::regclass)
    Profile        | bigint                      |           |          |
    Date           | text (YYYY-MM-DD)            |           |          |
    Latitude       | double precision (degrees)   |           |          |
    Longitude      | double precision (degrees)   |           |          |
    Pres_raw(dbar) | double precision (dbar)      |           |          |
    Pres_adj(dbar) | double precision (dbar)      |           |          |
    Pres_raw_qc    | double precision             |           |          |
    Pres_adj_qc    | double precision             |           |          |
    Temp_raw(C)    | double precision (°C)        |           |          |
    Temp_adj(C)    | double precision (°C)        |           |          |
    Temp_raw_qc    | double precision             |           |          |
    Temp_adj_qc    | double precision             |           |          |
    Psal_raw(psu)  | double precision (PSU)       |           |          |
    Psal_adj(psu)  | double precision (PSU)       |           |          |
    Psal_raw_qc    | double precision             |           |          |
    Psal_adj_qc    | double precision             |           |          |
    float_id       | text                        |           |          |

    Indexes:
        "profiles_pkey" PRIMARY KEY, btree (id)
        "idx_profiles_float" btree (float_id)
        "idx_profiles_profile" btree ("Profile")
        "idx_profiles_date" btree (("Date")::date)
        "idx_profiles_latlon" btree ("Latitude","Longitude")

"""

def clean_response(res):
    if isinstance(res, str):
        s = res.strip()

        # print(s)
        if(s.startswith("```")):
            s = s.strip("`")
        
        # print(s)
        if(s.startswith("sql")):
            s = s.strip("sql")
        

        try:
            cleaned_response = json.loads(s)
        
        except json.JSONDecodeError:
            cleaned_response = s
    
    else:
        cleaned_response = res


    # print("TYPE: ", type(cleaned_response))
    return cleaned_response




def sql_generator(query, retrieved_data):
    print("Retrieved data : ", retrieved_data)
    SYSTEM_PROMPT = f"""
You are an expert PostgreSQL query generator. You always produce one and only one valid SQL SELECT statement.

Database schema:
{db_schema}

User request:
{query}

Relevant float_ids from vector DB:
{retrieved_data}

STRICT RULES:

1. Output only a single valid SQL SELECT query; no explanations, comments, markdown, code fences or formatting.
2. The table name is always exactly "profiles".
3. Always wrap column names exactly as shown in the schema in double quotes.
   - Example: SELECT COUNT(DISTINCT "float_id") FROM "profiles";
4. Date column "Date" is TEXT in YYYY-MM-DD format.
   - Always cast to DATE for comparisons: "Date"::DATE
   - Example: EXTRACT(YEAR FROM "Date"::DATE) = 2022
   - Example: "Date"::DATE BETWEEN '2022-01-01' AND '2022-12-31'
5. "float_id" is TEXT. Wrap numeric IDs in single quotes when filtering.
   - Example: WHERE "float_id" IN ('2902291','3902292')
6. When filtering by location use the exact ranges provided (Latitude/Longitude).
   - Example: "Latitude" BETWEEN 5 AND 15 AND "Longitude" BETWEEN 85 AND 95
7. Always include the "float_id" column in the SELECT list along with any other requested columns.
8. Only include columns needed to answer the user’s question. Do not select * unnecessarily.
9. NULL handling:
   - Filter out NULL values only for the columns actually used in the query or explicitly requested non-NULL by the user.
10. Data volume handling:
    - If the query is narrow (small date range, few float_ids, single profile):
        * Return raw rows directly, but LIMIT to 500 rows for safety.
    - If the query is broad (large date range, many float_ids, whole dataset):
        * DO NOT return all rows.
        * Instead, summarise with aggregates (COUNT, AVG, MIN, MAX) or sample with LIMIT 500.
11. Sorting:
    - Use ORDER BY only if the user explicitly asks for a particular order (e.g. earliest, latest).
12. Always terminate the query with a semicolon.

GOAL:
Return only the minimal, correct SQL SELECT query that retrieves exactly what the user asked, optimised for performance, with correct filters, quoting, and aggregation when needed.
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
        ]
    )



    return clean_response(response.choices[0].message.content)

