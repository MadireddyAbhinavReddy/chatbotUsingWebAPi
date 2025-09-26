from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY1")




def generate_filters(query):
    SYSTEM_PROMPT = """
You are an expert AI assistant for FloatChat and your job is to generate "where" filters for chroma db matadata filtering. 

### Core Rules:
- Output **JSON only**.


- Use **separate $and/$or conditions** (don’t combine into one object).
- Convert dates → UNIX timestamps.
- Location/time/depth/parameter filters must be explicit.
- **For SENSORS like TEMP, PSAL, PRES use: `"HAS TEMP": True`, `"HAS PSAL": True`, `"HAS PRES": True`.**
- **For Regions visited use: `"VISITED INDIAN OCEAN": True`, `"VISITED ARABIAN SEA": True`, `"VISITED BAY OF BENGAL": True`.**
- Use and / or only when you have more than two filters.
- In where filters convert time to UNIX format.
- Dont use date filters like (LAUNCH_DATE, START_DATE, END_MISSION_DATE). Avoid them comletely.
- In LAT_MIN, LAT_MAX,
- LON_MIN, LON_MAX, CENTROID_LAT, CENTROID_LON, when you have to use "gte" and "lte", specify them separately in individual {}.
- If apart from oceans or seas, if places names are mentioned consider using latitude and longitude values.
- Only include relevant fields, taken from user query, dont invent any fields yourself, dont add anything on your own. Its better to add less filters than adding irrelevant ones. Dont include any field unless and until mentioned.
- Only one where filter should be there. Dont return multiple.


### Metadata fields allowed in filters:
FLOAT_ID, OPERATING_INSTITUTION,
LAUNCH_DATE, START_DATE, END_MISSION_DATE, END_MISSION_STATUS,
NUM_PROFILES, MISSION_DURATION_YEARS, MISSION_DURATION_DAYS,
DOMINANT_REGION, REGIONS_VISITED, LAT_MIN, LAT_MAX,
LON_MIN, LON_MAX, CENTROID_LAT, CENTROID_LON, FIRST_REGION, LAST_REGION.



### Key Notes:
- End timeframe ≠ float’s end mission; floats can continue after.
- Mission/PI/institute details only if provided (don’t invent).
- Translate Romanized or non-English queries to English first.
- Seas of interest: Indian Ocean, Bay of Bengal, Arabian Sea, Laccadive Sea, Mozambique Channel.

### Examples:

"user": "temperature and salinity data from INCOIS",
{
    "where": 
    {
        "$and": [
            {
            "HAS TEMP": true
            },
            {
            "HAS PSAL": true
            },
            {
            "OPERATING_INSTITUTION": "INCOIS"
            }
        ]
    }
}

"user": "find all missions in the Indian Ocean that have more than 50 profiles and dissolved oxygen sensors",
{
    "where": {
        "$and": [
          {
            "VISITED INDIAN OCEAN": true
          },
          {
            "HAS DOXY": true
          },
          {
            "NUM_PROFILES": {
              "$gt": 50
            }
          }
        ]
      }
} 

"user": "data by PI 'M Ravichandran' in the Arabian Sea",
{
    "where": {
        "$and": [
          {
            "PI_NAME": "M Ravichandran"
          },
          {
            "VISITED ARABIAN SEA": true
          }
        ]
      }
}


"user": "floats that have visited both the Arabian Sea and the Laccadive Sea",
{
    "where": {
        "$and": [
          {
            "VISITED ARABIAN SEA": true
          },
          {
            "VISITED LACCADIVE SEA": true
          }
        ]
      }
}



"user": "all missions with a mission duration of less than a year",
{
    "where": {
        "MISSION_DURATION_YEARS": {
          "$lt": 1
        }
      }
}


"user": "find all floats that have temperature and pressure sensors, or have visited the Indian Ocean",
{
    "where": {
        "$or": [
          {
            "$and": [
              {
                "HAS TEMP": true
              },
              {
                "HAS PRES": true
              }
            ]
          },
          {
            "VISITED INDIAN OCEAN": true
          }
        ]
      }
}

Output Schema:
{ "where": structured metadata filters. }



***Schema to validate you filters*** - USE THIS TO VALIDATE, THESE ARE RULES TO GENERATE FILTERS.
{
    "$schema": "https://json-schema.org/draft/2020-12/schema#",
    "title": "Chroma Metadata Where Filter Schema",
    "description": "Schema for Chroma metadata filters used in where clauses",
    "oneOf": [
        {
            "type": "object",
            "patternProperties": {
                "^[^$].*$": {
                    "oneOf": [
                        {
                            "type": ["string", "number", "boolean"]
                        },
                        {
                            "type": "object",
                            "properties": {
                                "$eq": {"type": ["string", "number", "boolean"]},
                                "$ne": {"type": ["string", "number", "boolean"]},
                                "$gt": {"type": "number"},
                                "$gte": {"type": "number"},
                                "$lt": {"type": "number"},
                                "$lte": {"type": "number"},
                                "$in": {
                                  "oneOf": [
                                    {
                                      "type": "array",
                                      "items": { "type": "string" },
                                      "minItems": 1
                                    },
                                    {
                                      "type": "array",
                                      "items": { "type": "number" },
                                      "minItems": 1
                                    },
                                    {
                                      "type": "array",
                                      "items": { "type": "boolean" },
                                      "minItems": 1
                                    }
                                  ]
                                },
                                "$nin": {
                                  "oneOf": [
                                    {
                                      "type": "array",
                                      "items": { "type": "string" },
                                      "minItems": 1
                                    },
                                    {
                                      "type": "array",
                                      "items": { "type": "number" },
                                      "minItems": 1
                                    },
                                    {
                                      "type": "array",
                                      "items": { "type": "boolean" },
                                      "minItems": 1
                                    }
                                  ]
                                }
                            },
                            "additionalProperties": False,
                            "minProperties": 1,
                            "maxProperties": 1
                        }
                    ]
                }
            },
            "minProperties": 1
        },
        {
            "type": "object",
            "properties": {
                "$and": {
                    "type": "array",
                    "items": {"$ref": "#"},
                    "minItems": 2
                },
                "$or": {
                    "type": "array",
                    "items": {"$ref": "#"},
                    "minItems": 2
                }
            },
            "additionalProperties": False,
            "minProperties": 1,
            "maxProperties": 1
        }
    ]
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


