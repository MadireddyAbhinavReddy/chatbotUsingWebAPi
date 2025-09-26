from retrieve_data_from_db.postgres_db import retrieve_data_from_postgres
from generate_sql.sql import sql_generator
from query_enhancement.enhance import query_enhancer
from final_ans.final_llm_call import get_ans_with_relevant_data
from store_in_vector_db.vector_db import query_documents
from typing import List, Dict, Tuple, Any
import io, csv, base64, json

# ----------------- Helper functions -----------------
def clean_response(res: str) -> Any:
    """Safely parse JSON response, fallback to string if invalid."""
    try:
        return json.loads(res)
    except Exception:
        return res

def generate_csv_base64(data: List[Dict]) -> str:
    """Generate CSV data as a base64-encoded string."""
    if not data:
        return ""
    try:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        return base64.b64encode(output.getvalue().encode("utf-8")).decode("utf-8")
    except Exception as e:
        print(f"[generate_csv_base64] Error generating CSV: {e}")
        return ""

# ----------------- Enhanced response -----------------
def get_enhanced_response(query: str, history: List[Dict]) -> Tuple[Any, List[Dict]]:
    """
    Handles theory-type queries with vector retrieval and LLM generation.
    Updates chat history and returns the answer.
    """
    # Append question to history
    history.append({"question": query})

    try:
        enhanced_query = query_enhancer(query, history)
        response = clean_response(enhanced_query)

        # If LLM suggests vector retrieval
        if isinstance(response, dict) and response.get("need_retrieval") and response.get("enhanced_query"):
            filters = response.get("where") or {}
            retrieved_vectors = query_documents(response['enhanced_query'], filters)
            generated_sql = sql_generator(query, retrieved_vectors)
            data = retrieve_data_from_postgres(generated_sql)
            data_json = data.to_json(orient="records") if not data.empty else "[]"
            ans = get_ans_with_relevant_data(enhanced_query, data_json, history)

        # If LLM returns a simple reply
        elif isinstance(response, dict) and response.get("reply"):
            ans = response["reply"]

        # Fallback: return raw LLM output
        else:
            ans = response

    except Exception as e:
        print(f"[get_enhanced_response] Error: {e}")
        ans = f"Error generating answer: {str(e)}"

    # Update history with answer
    history[-1]["answer"] = ans
    return ans, history

# ----------------- Table response -----------------
def get_table_response(query: str) -> Tuple[List[List[Any]], str, str]:
    """
    Handles table-type queries with vector retrieval and SQL execution.
    Returns table (list of lists), explanation string, CSV download string.
    """
    try:
        # Step 1: Enhance query
        try:
            enhanced_query = query_enhancer(query, history=[])
            response = clean_response(enhanced_query)
        except Exception:
            response = {"enhanced_query": query}

        # Step 2: Retrieve vectors if needed
        retrieved_vectors = []
        if isinstance(response, dict) and response.get("need_retrieval") and response.get("enhanced_query"):
            filters = response.get("where") or {}
            retrieved_vectors = query_documents(response["enhanced_query"], filters)

        # Step 3: Generate SQL
        sql_query = sql_generator(query, retrieved_vectors)

        # Step 4: Fetch data
        df = retrieve_data_from_postgres(sql_query)
        if df.empty:
            return [], "No data found.", ""

        # Step 5: Build table component (header + rows, max 100)
        table_component = [list(df.columns)]  # header row
        for row in df.itertuples(index=False):
            table_component.append(list(row))
        table_component = table_component[:101]  # first 100 rows + header

        # Step 6: Explanation
        explanation = f"Query returned {len(df)} row(s). Showing first {min(len(df), 100)} rows."

        # Step 7: CSV
        data_list = df.to_dict(orient="records")
        csv_download = generate_csv_base64(data_list)

        return table_component, explanation, csv_download

    except Exception as e:
        print(f"[get_table_response] Error: {e}")
        return [], f"Error retrieving table: {str(e)}", ""
