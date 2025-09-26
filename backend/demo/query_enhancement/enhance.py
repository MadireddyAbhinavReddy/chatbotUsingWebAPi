from openai import OpenAI
from dotenv import load_dotenv
from final_ans.final_llm_call import get_ans_with_relevant_data
import os

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def is_generic_question(text: str) -> bool:
    # crude detection; you can improve with keywords, regex or even a small model
    generic_keywords = ["what is", "why", "explain", "define", "meaning", "how does"]
    return any(k in text.lower() for k in generic_keywords)

def query_enhancer(user_query, language, history):
    if is_generic_question(user_query):
        # Directly call your function for conceptual questions
        return get_ans_with_relevant_data(user_query, None, history, language)

    SYSTEM_PROMPT = """
You are an expert AI assistant for FloatChat, which enhances user queries for ARGO oceanographic data. 

Your main task is to convert user queries into detailed, structured, JSON-based queries optimized for ChromaDB vector retrieval.

────────────────────────────────────
Core Rules:
────────────────────────────────────
- Default behaviour: Output **JSON only** for data-discovery type questions.
- If retrieval is needed → set "need_retrieval": "True", else "False".
- Always expand vague/short queries into full English.
- Use separate $and/$or conditions (don’t combine into one object).
- Convert dates → UNIX timestamps (or YYYY-MM-DD HHMMSS if needed).
- Convert numbers in words → digits.
- Location/time/depth/parameter filters must be explicit.
- For TEMP, PSAL, PRES use: "HAS TEMP": True, "HAS PSAL": True, "HAS PRES": True.
- If irrelevant question → soft rejection with "need_retrieval": "False".
- If unclear → ask for clarification.
- If multiple questions → split and answer separately.
- Always remain strictly within ARGO float data discovery domain.
- Use and/or only when you have more than two filters.
- Reply to what the user has asked first; add extra context only afterwards.


────────────────────────────────────
Metadata fields allowed in filters:
────────────────────────────────────
FLOAT_ID, WMO_INST_TYPE, PI_NAME, OPERATING_INSTITUTION, PROJECT_NAME,
START_DATE_QC, LAUNCH_DATE, START_DATE, END_MISSION_DATE, END_MISSION_STATUS,
NUM_PROFILES, MISSION_DURATION_YEARS, MISSION_DURATION_DAYS, PLATFORM_MAKER,
PLATFORM_TYPE, SENSORS, DOMINANT_REGION, REGIONS_VISITED, LAT_MIN, LAT_MAX,
LON_MIN, LON_MAX, CENTROID_LAT, CENTROID_LON, FIRST_REGION, LAST_REGION.

────────────────────────────────────
Key Notes:
────────────────────────────────────
- End timeframe ≠ float’s end mission; floats can continue after.
- Mission/PI/institute details only if provided (don’t invent).
- Translate Romanized or non-English queries to English first.
- Seas of interest: Indian Ocean, Bay of Bengal, Arabian Sea, Laccadive Sea, Mozambique Channel.

────────────────────────────────────
Examples:
────────────────────────────────────

User: "floats between March 2023 and April 2024"
```json
{
  "need_retrieval": "True",
  "enhanced_query": "Retrieve ARGO float data after 2023-03-01 and before 2024-04-01",
  "where": {
    "$and": [
      {"LAUNCH_DATE": {"$gte": 1677628800}},
      {"LAUNCH_DATE": {"$lte": 1711929599}}
    ]
  }
}
"""



    client = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for h in history[:-1]:
        if(h.get('question') and h.get('answer')):
            messages.append(
                {"role": "user", "content": h['question']}
            )

            messages.append(
                {"role": "assistant", "content": h['answer']}
            )
    

    messages.append({"role": "user", "content": user_query})




    response = client.chat.completions.create(
        model="gemini-2.0-flash-lite",
        messages=messages,
        response_format={"type": "json_object"}
    )

    # print(response, end = "\n\n\n\n")
    return response.choices[0].message.content
