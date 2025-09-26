# import os 
# from dotenv import load_dotenv
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from main_pipeline import query_to_answer

# load_dotenv()
# DB_URL = os.getenv('DB_URL')

# app = FastAPI()
# origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods={"*"},
#     allow_headers={"*"}
# )

# history = [{"question": "hi", "answer": "Hello, I am float chat, here to assist you with oceanographic data, feel free to ask any question related to it."}]


# class AnswerRequest(BaseModel):
#     user_query: str


# @app.get("/")
# def main():
#     return { "message" : "Welcome to Float chat, what do you want to know today... ?" }


# @app.post("/answer")
# def get_answer(req: AnswerRequest):
#     global history
#     try:
        
#         query = req.user_query
#         res, history = query_to_answer(query, history)
        
#         return res


#     except Exception as e:
#         return HTTPException(status_code=400, detail=str(e))




import os 
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import json
import asyncio
from query_enhancement.enhance import query_enhancer
from query_enhancement.classify import query_classifier
from query_enhancement.filters import generate_filters
from store_in_vector_db.vector_db import query_documents
from generate_sql.sql import sql_generator
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from retrieve_data_from_db.postgres_db import retrieve_data_from_postgres
from final_ans.final_llm_call import get_ans_with_relevant_data

from typing import Optional
from fastapi import File, UploadFile
import speech_recognition as sr
import tempfile
import os


# ENHANCE
# CLASSIFY
# FILTERS
# VECTOR DB
# SQL
# POSTGRES DATA RETRIEVAL
# FINAL ANS




load_dotenv()
DB_URL = os.getenv('DB_URL')

app = FastAPI()
origins = ["http://localhost:5173","http://localhost:8080", "http://127.0.0.1:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods={"*"},
    allow_headers={"*"}
)

history = [{"question": "hi", "answer": "Hello, I am float chat, here to assist you with oceanographic data, feel free to ask any question related to it."}]



class TableResponse(BaseModel):
    type: str
    message: str
    raw_data: list[dict]
    columns: list[str]
    csv_url: str

class PlotResponse(BaseModel):
    type: str
    message: str
    csv_url: str

class TextResponse(BaseModel):
    type: str
    message: str

class QueryRequest(BaseModel):
    tab: str
    query: str
    language: str
    imageData: Optional[str] = None

class SpeechToTextResponse(BaseModel):
    text: str
    confidence: float
    language: Optional[str] = None
    method: str


def clean_response(res):

    if(isinstance(res, str)):
        return json.loads(res)
    
    return res


async def save_pg_data_async(pg_data, path):
    await asyncio.to_thread(pg_data.to_csv, path, index=False)


def text_answer(query, language):
    res = clean_response(query_enhancer(query, language, []))
    print("Query : ",query)
    
    # reply
    if(res.get('reply') != None):
        return {
            "text": res['reply']
        }

    if(res.get('enhanced_query') != None):
        enhanced_query = res['enhanced_query']
        print("enhanced query : ", enhanced_query)

        res = clean_response(query_classifier(enhanced_query))

        if(res.get('search_type') != None):

            search_type = res['search_type']
            print("search type : ", search_type)
            print("Query :",query)

            # direct SQL
            if(search_type == "sql"):
                res = clean_response(sql_generator(enhanced_query, 'theory'))
                if(res.get('sql') != None):
                    sql = res['sql']
                    print("SQL : ", sql, end="\n\n")

                    pg_data = retrieve_data_from_postgres(sql)
                    pg_data = pg_data.to_json(orient="records")

                    sources_to_cite=None
                    if(res.get('sources_to_cite')):
                        sources_to_cite = res['sources_to_cite']
                        print("Sources to cite : ", sources_to_cite, end="\n\n")

                    final_ans_text = get_ans_with_relevant_data(enhanced_query, pg_data, [], sources_to_cite, language)
                    print("FInal ans : ", final_ans_text)

                    return {
                        "text": final_ans_text,
                    }
                
            elif(search_type == "vector"):

                res = clean_response(generate_filters(enhanced_query))
                print("Retrieved vector data : ", res)

                if(res.get('where') != None):
                    where_filters = res['where']
                    res = query_documents(enhanced_query, where_filters)
                    vector_ids = res['ids'][0]

                    print(vector_ids)


                    res = clean_response(sql_generator(enhanced_query, 'theory', vector_ids))
                    print(res)
                    if(res.get('sql') != None):
                        sql = res['sql']
                        print("SQL : ", sql)

                        pg_data = retrieve_data_from_postgres(sql)
                        pg_data = pg_data.to_json(orient="records")

                        sources_to_cite=None
                        if(res.get('sources_to_cite')):
                            sources_to_cite = res['sources_to_cite']
                            print("Sources to cite : ", sources_to_cite, end="\n\n")


                        final_ans_text = get_ans_with_relevant_data(enhanced_query, pg_data, [], sources_to_cite, language)
                        print("FInal ans : ", final_ans_text)

                        return {
                            "text": final_ans_text,
                        }



def table_answer(query, language="english"):
    res = clean_response(query_enhancer(query, language, []))
    
    # reply
    if(res.get('reply') != None):
        return {
            "text": res['reply'],
            "csv_url": None
        }

    if(res.get('enhanced_query') != None):
        enhanced_query = res['enhanced_query']
        print("enhanced query : ", enhanced_query)

        res = clean_response(query_classifier(enhanced_query))

        if(res.get('search_type') != None):

            search_type = res['search_type']
            print("search type : ", search_type)

            # direct SQL
            if(search_type == "sql"):
                res = clean_response(sql_generator(enhanced_query, 'table'))
                if(res.get('sql') != None):
                    sql = res['sql']
                    print("SQL : ", sql)

                    pg_data = retrieve_data_from_postgres(sql)
                    if(res.get('sources_to_cite')):
                        sources_to_cite = res['sources_to_cite']
                        print("Sources to cite : ", sources_to_cite, end="\n\n")

                    asyncio.run(save_pg_data_async(pg_data, 'static/tables/userId_chatId_uniqueId.csv'))

                    return {
                        "text": f"Query returned {len(pg_data)} row(s). Showing first {min(len(pg_data), 100)} rows.",
                        "csv_url": "static/tables/userId_chatId_uniqueId.csv"
                    }
                
            elif(search_type == "vector"):

                res = clean_response(generate_filters(enhanced_query))
                print("Retrieved vector data : ", res)

                if(res.get('where') != None):
                    where_filters = res['where']
                    res = query_documents(enhanced_query, where_filters)
                    vector_ids = res['ids'][0]

                    print(vector_ids)


                    res = clean_response(sql_generator(enhanced_query, 'table', vector_ids))
                    print(res)
                    if(res.get('sql') != None):
                        sql = res['sql']
                        print("SQL : ", sql)

                        pg_data = retrieve_data_from_postgres(sql)
                        if(res.get('sources_to_cite')):
                            sources_to_cite = res['sources_to_cite']
                            print("Sources to cite : ", sources_to_cite, end="\n\n")

                        asyncio.run(save_pg_data_async(pg_data, 'static/tables/userId_chatId_uniqueId.csv'))

                        return {
                            "text": f"Query returned {len(pg_data)} row(s). Showing first {min(len(pg_data), 10)} rows.",
                            "csv_url": "static/tables/userId_chatId_uniqueId.csv"
                        }


def plot_answer(query, language="english"):
    res = clean_response(query_enhancer(query, language, []))
    
    # reply
    if(res.get('reply') != None):
        return {
            "text": res['reply'],
            "csv_url": None
        }

    if(res.get('enhanced_query') != None):
        enhanced_query = res['enhanced_query']
        print("enhanced query : ", enhanced_query)

        res = clean_response(query_classifier(enhanced_query))

        if(res.get('search_type') != None):

            search_type = res['search_type']
            print("search type : ", search_type)

            # direct SQL
            if(search_type == "sql"):
                res = clean_response(sql_generator(enhanced_query, 'plot'))
                if(res.get('sql') != None):
                    sql = res['sql']
                    print("SQL : ", sql)

                    pg_data = retrieve_data_from_postgres(sql)
                    if(res.get('sources_to_cite')):
                        sources_to_cite = res['sources_to_cite']
                        print("Sources to cite : ", sources_to_cite, end="\n\n")

                    asyncio.run(save_pg_data_async(pg_data, 'static/plots/userId_chatId_uniqueId.csv'))

                    return {
                        "text": f"Query returned {len(pg_data)} row(s). Data prepared for plotting visualization.",
                        "csv_url": "static/plots/userId_chatId_uniqueId.csv"
                    }
                
            elif(search_type == "vector"):

                res = clean_response(generate_filters(enhanced_query))
                print("Retrieved vector data : ", res)

                if(res.get('where') != None):
                    where_filters = res['where']
                    res = query_documents(enhanced_query, where_filters)
                    vector_ids = res['ids'][0]

                    print(vector_ids)


                    res = clean_response(sql_generator(enhanced_query, 'plot', vector_ids))
                    print(res)
                    if(res.get('sql') != None):
                        sql = res['sql']
                        print("SQL : ", sql)

                        pg_data = retrieve_data_from_postgres(sql)
                        if(res.get('sources_to_cite')):
                            sources_to_cite = res['sources_to_cite']
                            print("Sources to cite : ", sources_to_cite, end="\n\n")

                        asyncio.run(save_pg_data_async(pg_data, 'static/plots/userId_chatId_uniqueId.csv'))

                        return {
                            "text": f"Query returned {len(pg_data)} row(s). Data prepared for plotting visualization.",
                            "csv_url": "static/plots/userId_chatId_uniqueId.csv"
                        }





@app.get("/")
def main():
    return { "message" : "Welcome to Float chat, what do you want to know today... ?" }
static_path = Path(__file__).parent / "static"
print(static_path)  # Optional: check the resolved path

app.mount("/static", StaticFiles(directory=static_path), name="static")
@app.post("/query")
def get_answer(req: QueryRequest):
    global history

    try:
        # Validate and choose tab
        if not req.tab or req.tab.lower() not in ["table", "plot", "theory"]:
            tab_chosen = "theory"
        else:
            tab_chosen = req.tab.lower()

        # Validate query
        if not req.query or req.query.strip() == "":
            raise HTTPException(status_code=400, detail="Query can't be empty")

        user_query = req.query.strip()

        # Handle "table" tab
        if tab_chosen == "table":
            answer = table_answer(user_query)

            if not answer or 'text' not in answer or 'csv_url' not in answer:
                raise HTTPException(status_code=500, detail="Invalid response from table_answer")

            text = answer['text']
            url = answer['csv_url']

            df = pd.read_csv(url)

            return TableResponse(
                type=tab_chosen,
                message=text,
                raw_data=df.head(10).to_dict(orient="records"),
                columns=df.columns.to_list(),
                csv_url=url
            )

        # Handle "plot" tab
        elif tab_chosen == "plot":
            answer = plot_answer(user_query)

            if not answer or 'text' not in answer or 'csv_url' not in answer:
                raise HTTPException(status_code=500, detail="Invalid response from plot_answer")

            text = answer['text']
            url = answer['csv_url']

            return PlotResponse(
                type=tab_chosen,
                message=text,
                csv_url=url
            )

        # Handle "theory" or default tab
        else:
            answer = text_answer(user_query, req.language)

            if not answer or 'text' not in answer:
                raise HTTPException(status_code=500, detail="Invalid response from text_answer")

            text = answer['text']

            return TextResponse(
                type=tab_chosen,
                message=text
            )

    except HTTPException as http_exc:
        # Let FastAPI handle HTTP errors
        raise http_exc

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.post("/speech-to-text")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """
    Convert speech audio file to text using speech recognition.
    Supports WAV, FLAC, and other audio formats.
    """
    try:
        # Validate file type
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Create a temporary file to store the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Initialize the recognizer
            recognizer = sr.Recognizer()
            
            # Load the audio file
            with sr.AudioFile(temp_file_path) as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source)
                # Record the audio
                audio_data = recognizer.record(source)
            
            # Perform speech recognition
            try:
                # Use Google's speech recognition service
                text = recognizer.recognize_google(audio_data)
                confidence = 0.9  # Google API doesn't return confidence, so we estimate
                
                return SpeechToTextResponse(text=text, confidence=confidence)
                
            except sr.UnknownValueError:
                raise HTTPException(status_code=400, detail="Could not understand the audio")
            except sr.RequestError as e:
                raise HTTPException(status_code=500, detail=f"Speech recognition service error: {str(e)}")
                
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    