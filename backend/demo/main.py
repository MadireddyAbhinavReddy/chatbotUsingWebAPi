# Fixed backend/main.py with improved error handling and security
import psutil
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from fastapi.middleware.cors import CORSMiddleware
from google import genai
import re
import csv
import io
import base64
from decimal import Decimal
import os
import json
from typing import Optional, Dict, Any, List
from final_ans.final_llm_call import get_ans_with_relevant_data
from fastapi.responses import JSONResponse
from datetime import date, datetime 

# Import the new vector-based modules
from query_enhancement.enhance import query_enhancer
from store_in_vector_db.vector_db import query_documents
from retrieve_data_from_db.postgres_db import retrieve_data_from_postgres
from final_ans.final_llm_call import get_ans_with_relevant_data

# ----------------- FastAPI setup -----------------
app = FastAPI(title="FloatChat API", version="1.0.0")

# Fixed: Improved CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000","http://localhost:8080", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Database setup with error handling -----------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:SIHPostgreSQL@localhost:5432/floatchat")

try:
    engine = create_engine(DATABASE_URL)
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Database connection successful")
except Exception as e:
    print(f"Database connection failed: {e}")
    engine = None

# ----------------- Gemini setup with error handling -----------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBQoD4oi_BycfHSLbwh_p4YOBpR5H4ej88")

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("Gemini client initialized successfully")
except Exception as e:
    print(f"Gemini client initialization failed: {e}")
    client = None

# ----------------- Database schema -----------------
DB_SCHEMA = """
Table: profiles
Columns with units:
- "Profile" : bigint
- "Date" : text (YYYY-MM-DD)
- "Latitude" : double precision (degrees)
- "Longitude" : double precision (degrees)
- "Pres_raw(dbar)" : double precision (dbar)
- "Pres_adj(dbar)" : double precision (dbar)
- "Pres_raw_qc" : double precision
- "Pres_adj_qc" : double precision
- "Temp_raw(C)" : double precision (°C)
- "Temp_adj(C)" : double precision (°C)
- "Temp_raw_qc" : double precision
- "Temp_adj_qc" : double precision
- "Psal_raw(psu)" : double precision (PSU)
- "Psal_adj(psu)" : double precision (PSU)
- "Psal_raw_qc" : double precision
- "Psal_adj_qc" : double precision
- "float_id" : text
"""

# ----------------- Request/Response models -----------------
class QueryRequest(BaseModel):
    query_type: str
    tab: str  # "Tables", "Plot", or "Theory"
    prompt: str
    language: str

class ContentResponse(BaseModel):
    type: str
    component: Optional[Any] = None
    explanation: Optional[str] = None

class QueryResponse(BaseModel):
    sql_query: Optional[str] = None
    content: Optional[ContentResponse] = None
    raw_data: Optional[List[Dict]] = None
    csv_download: Optional[str] = None
    error: Optional[str] = None

# ----------------- Helper functions with error handling -----------------
def clean_sql(sql_text: str) -> str:
    """Clean SQL text by removing markdown formatting"""
    try:
        sql_text = re.sub(r"```sql", "", sql_text, flags=re.IGNORECASE)
        sql_text = sql_text.replace("```", "")
        return sql_text.strip()
    except Exception as e:
        print(f"Error cleaning SQL: {e}")
        return sql_text

def format_data_for_gemini(data: List[Dict]) -> str:
    """Format database results for Gemini analysis"""
    try:
        if not data:
            return "No results."
        keys = list(data[0].keys())
        lines = [", ".join(keys)]
        for row in data[:50]:  # Limit to first 50 rows
            lines.append(", ".join(str(row.get(k, '')) for k in keys))
        return "\n".join(lines)
    except Exception as e:
        print(f"Error formatting data for Gemini: {e}")
        return "Error formatting data."

def generate_csv_base64(data: List[Dict]) -> str:
    """Generate CSV data as base64 string"""
    try:
        if not data:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return base64.b64encode(output.getvalue().encode("utf-8")).decode("utf-8")
    except Exception as e:
        print(f"Error generating CSV: {e}")
        return ""

# def execute_sql_query(sql_query: str) -> List[Dict]:
#     """Execute SQL query with error handling"""
#     if not engine:
#         raise HTTPException(status_code=500, detail="Database connection not available")
    
#     try:
#         with engine.connect() as conn:
#             result = conn.execute(text(sql_query)).fetchall()
#             rows = []
#             for row in result:
#                 mapped = {}
#                 for key, val in row._mapping.items():
#                     # convert Decimal to float for JSON serialization
#                     if isinstance(val, Decimal):
#                         mapped[key] = float(val)
#                     else:
#                         mapped[key] = val
#                 rows.append(mapped)
#             return rows
#     except Exception as e:
#         print(f"SQL execution error: {e}")
#         raise HTTPException(status_code=400, detail=f"SQL execution failed: {str(e)}")
def execute_sql_query(sql_query: str) -> List[Dict]:
    """Execute SQL query with error handling"""
    if not engine:
        raise HTTPException(status_code=500, detail="Database connection not available")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query)).fetchall()
            rows = []
            for row in result:
                mapped = {}
                for key, val in row._mapping.items():
                    # convert Decimal to float for JSON serialization
                    if isinstance(val, Decimal):
                        mapped[key] = float(val)
                    # convert date/datetime to ISO string for JSON serialization
                    elif isinstance(val, (date, datetime)):
                        mapped[key] = val.isoformat()
                    else:
                        mapped[key] = val
                rows.append(mapped)
            return rows
    except Exception as e:
        print(f"SQL execution error: {e}")
        raise HTTPException(status_code=400, detail=f"SQL execution failed: {str(e)}")
def clean_response(res):
    """Clean response from query enhancer"""
    try:
        if isinstance(res, str):
            return json.loads(res)
        return res
    except json.JSONDecodeError:
        return res

def generate_sql_with_vector_enhancement(prompt: str, language: str, history: list = []) -> str:
    """Generate SQL query using vector enhancement approach"""
    try:
        # Enhance the query
        enhanced_query = query_enhancer(prompt, language, history)
        response = clean_response(enhanced_query)
        
        # Check if we need to use vector retrieval
        if isinstance(response, dict) and response.get('need_retrieval') and response.get('enhanced_query'):
            print(f"Enhanced Query: {response['enhanced_query']}")
            
            # Get filters if available
            filters = response.get('where', {})
            
            # Query documents using vector search
            retrieved_vectors = query_documents(response['enhanced_query'], filters)
            
            # Generate SQL using the retrieved vectors with the original Gemini SQL generator
            generated_sql = generate_sql_with_gemini(prompt, retrieved_vectors)
            
            return generated_sql
        else:
            # Fall back to the original Gemini SQL generation
            return generate_sql_with_gemini(prompt)
            
    except Exception as e:
        print(f"Vector enhancement error: {e}")
        # Fall back to the original Gemini SQL generation
        return generate_sql_with_gemini(prompt)

def generate_sql_with_gemini(prompt: str, retrieved_vectors: str = "") -> str:
    """Generate SQL query using Gemini with error handling and vector context"""
    if not client:
        raise HTTPException(status_code=500, detail="Gemini client not available")
    
    # Prepare the context from retrieved vectors
    vector_context = ""
    if retrieved_vectors:
        vector_context = f"""
        
Additional context from similar queries:
{retrieved_vectors}

Please use this context to better understand the user's intent and generate a more accurate SQL query.
"""
    print("Vector Content : ",vector_context)
    
    gemini_prompt = f"""
You are an expert PostgreSQL query generator.

Database schema:
{DB_SCHEMA}

User request:
{prompt}
{vector_context}

STRICT RULES:
1. Only generate a single valid SQL SELECT query; no INSERT, UPDATE, DELETE, or DDL.
2. Always wrap column names exactly as shown in the schema in double quotes.
   - Example: SELECT COUNT(DISTINCT "float_id") FROM profiles;
3. The table name is always "profiles" (do not pluralize or change).
4. The "Date" column is TEXT in YYYY-MM-DD format.
   - When filtering by date use CAST: "Date"::DATE
   - Example: EXTRACT(YEAR FROM "Date"::DATE) = 2022
   - Example: "Date"::DATE BETWEEN '2022-01-01' AND '2022-12-31'
5. The "float_id" column is TEXT. Wrap numeric IDs in single quotes when filtering.
6. Always filter out NULL values for adjusted columns ("*_adj").
7. Always include the "float_id" column in the SELECT list along with any other requested columns so results can be matched to the IDs.
8. If multiple float IDs are requested, filter using WHERE "float_id" IN ('id1','id2',...).
9. For adjusted salinity use the column exactly as in the schema (e.g. "Psal_adj(psu)").
10. Use aggregate functions (AVG, SUM, COUNT, MIN, MAX) only if the user asks for summaries.
11. For trend analysis requests:
    - Use AVG over the relevant numeric column(s) to capture overall trend.
    - Limit the dataset to the minimal required range (e.g. recent dates) for efficiency.
12. For anomaly detection requests:
    - Identify abrupt changes using MAX or MIN of the relevant column(s).
    - Return extreme values along with "float_id" and "Date" for context.
13. Always terminate the query with a semicolon.
14. Return only valid SQL text. No explanations, no markdown, no code fences.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=gemini_prompt
        )
        sql_query = clean_sql(response.text)
        
        # Fixed: Ensure proper quoting
        if "float_id" in sql_query and '"float_id"' not in sql_query:
            sql_query = sql_query.replace("float_id", '"float_id"')
        
        return sql_query
    except Exception as e:
        print(f"Gemini SQL generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate SQL: {str(e)}")


# ----------------- Health check endpoint -----------------
@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database_connected": engine is not None,
        "gemini_available": client is not None
    }

# ----------------- Main query endpoint with comprehensive error handling -----------------
@app.post("/query", response_model=QueryResponse)
def run_query(req: QueryRequest):
    """Process user query and return results based on selected tab"""
    print(f"Processing query - Type: {req.query_type}, Tab: {req.tab}, Prompt: {req.prompt}, Language: {req.language}")

    # Validate request
    if req.query_type != "user_query":
        raise HTTPException(status_code=400, detail="Only 'user_query' is supported")
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")
    if req.tab not in ["Tables", "Plot", "Theory"]:
        raise HTTPException(status_code=400, detail="Invalid tab. Must be 'Tables', 'Plot', or 'Theory'")

    try:
        # Step 1: Generate SQL query using vector enhancement approach
        sql_query = generate_sql_with_vector_enhancement(req.prompt, req.language)
        print(f"Generated SQL: {sql_query}")

        # Step 2: Execute SQL query
        data = execute_sql_query(sql_query)
        print(f"Query returned {len(data)} rows")

        # Step 3: Process based on tab type
        if req.tab == "Tables":
            # Fixed: Ensure proper table format
            table_component = []
            if data:
                # Header row
                table_component.append(list(data[0].keys()))
                # Data rows (limit to first 100 for performance)
                for row in data[:100]:
                    table_component.append(list(row.values()))
            
            return QueryResponse(
                sql_query=sql_query,
                content=ContentResponse(
                    type="table",
                    component=table_component,
                    explanation=f"Query returned {len(data)} row(s). Showing first {min(len(data), 100)} rows."
                ),
                raw_data=data,
                csv_download=generate_csv_base64(data)
            )

        elif req.tab == "Plot":
            return QueryResponse(
                sql_query=sql_query,
                content=ContentResponse(
                    type="plot",
                    component=data,
                    explanation="Data prepared for plotting visualization."
                ),
                raw_data=data
            )

        elif req.tab == "Theory":
            # convert your dataframe (or list of dicts) into JSON string for the LLM
            if isinstance(data, (list, tuple)):
                data_json = json.dumps(data, indent=2)
            else:
                # e.g. pandas DataFrame
                data_json = data.to_json(orient="records")

            # call your new function instead of analyze_data_with_gemini
            analysis = get_ans_with_relevant_data(req.prompt, data_json, [],req.language)
            # analysis = get_ans_with_relevant_data(req.prompt, data_json, history)


            return QueryResponse(
                sql_query=sql_query,
                content=ContentResponse(
                    type="theory",
                    component=analysis
                ),
                raw_data=data  # still send raw_data so frontend can access if needed
            )


    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Unexpected error in run_query: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# ----------------- Error handlers -----------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )
    
if __name__ == "__main__":
    import uvicorn
    print("Starting FloatChat API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)