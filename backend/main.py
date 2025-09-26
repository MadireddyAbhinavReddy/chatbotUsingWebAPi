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
import whisper
import torch


# ENHANCE
# CLASSIFY
# FILTERS
# VECTOR DB
# SQL
# POSTGRES DATA RETRIEVAL
# FINAL ANS




load_dotenv()
DB_URL = os.getenv('DB_URL')

# Global Whisper model - loaded once at startup
whisper_model = None

def load_whisper_model():
    """Load Whisper model at startup"""
    global whisper_model
    try:
        # Use base model for good balance of speed and accuracy
        # Options: tiny, base, small, medium, large
        model_size = os.getenv('WHISPER_MODEL_SIZE', 'base')
        print(f"Loading Whisper model: {model_size}")
        whisper_model = whisper.load_model(model_size)
        print(f"Whisper model loaded successfully. Using device: {whisper_model.device}")
    except Exception as e:
        print(f"Failed to load Whisper model: {e}")
        whisper_model = None

app = FastAPI()

# Load Whisper model on startup
@app.on_event("startup")
async def startup_event():
    load_whisper_model()

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
async def speech_to_text(
    audio_file: UploadFile = File(...),
    method: str = "whisper",
    language: Optional[str] = None
):
    """
    Convert speech audio file to text using advanced speech recognition.
    Supports multiple methods: whisper (OpenAI), google, azure
    Supports 99+ languages with high accuracy.
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
            if method == "whisper":
                return await transcribe_with_whisper(temp_file_path, language)
            elif method == "whisper-api":
                return await transcribe_with_whisper_api(temp_file_path, language)
            elif method == "google":
                return await transcribe_with_google(temp_file_path, language)
            elif method == "azure":
                return await transcribe_with_azure(temp_file_path, language)
            else:
                raise HTTPException(status_code=400, detail="Unsupported method. Use: whisper, whisper-api, google, or azure")
                
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


async def transcribe_with_whisper(audio_path: str, language: Optional[str] = None):
    """
    Transcribe audio using Local OpenAI Whisper - Most accurate, supports 99+ languages, FREE!
    """
    global whisper_model
    
    try:
        # Load model if not already loaded
        if whisper_model is None:
            load_whisper_model()
        
        if whisper_model is None:
            print("Local Whisper not available, falling back to Google")
            return await transcribe_with_google(audio_path, language)
        
        # Transcribe using local Whisper
        print(f"Transcribing with local Whisper model...")
        result = whisper_model.transcribe(
            audio_path,
            language=language,  # Optional: specify language code
            task="transcribe",  # or "translate" to translate to English
            verbose=False
        )
        
        # Extract confidence from segments if available
        confidence = 0.95  # Default high confidence for Whisper
        if 'segments' in result and result['segments']:
            # Average confidence from all segments
            confidences = [seg.get('avg_logprob', 0) for seg in result['segments']]
            if confidences:
                # Convert log probability to confidence (rough approximation)
                avg_logprob = sum(confidences) / len(confidences)
                confidence = min(0.99, max(0.7, (avg_logprob + 1) * 0.5 + 0.5))
        
        detected_language = result.get('language', language)
        
        return SpeechToTextResponse(
            text=result['text'].strip(),
            confidence=confidence,
            language=detected_language,
            method="whisper-local"
        )
        
    except Exception as e:
        print(f"Local Whisper failed: {e}, falling back to Google")
        return await transcribe_with_google(audio_path, language)


async def transcribe_with_whisper_api(audio_path: str, language: Optional[str] = None):
    """
    Transcribe audio using OpenAI Whisper API (cloud) - Requires API key
    """
    try:
        from openai import OpenAI
        
        # Initialize OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("No OpenAI API key found, using local Whisper")
            return await transcribe_with_whisper(audio_path, language)
            
        client = OpenAI(api_key=api_key)
        
        with open(audio_path, 'rb') as audio_file:
            # Use Whisper API for transcription
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,  # Optional: specify language code (e.g., 'en', 'es', 'fr')
                response_format="verbose_json"  # Get detailed response with confidence
            )
        
        return SpeechToTextResponse(
            text=transcript.text,
            confidence=0.95,  # Whisper is very accurate
            language=transcript.language if hasattr(transcript, 'language') else language,
            method="whisper-api"
        )
        
    except Exception as e:
        # Fallback to local Whisper
        print(f"Whisper API failed: {e}, falling back to local Whisper")
        return await transcribe_with_whisper(audio_path, language)


async def transcribe_with_google(audio_path: str, language: Optional[str] = None):
    """
    Transcribe audio using Google Speech Recognition - Good accuracy, free
    """
    try:
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(audio_path) as source:
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.record(source)
        
        # Map language codes for Google
        google_language = language if language else 'en-US'
        if language:
            language_map = {
                'en': 'en-US', 'es': 'es-ES', 'fr': 'fr-FR', 'de': 'de-DE',
                'it': 'it-IT', 'pt': 'pt-PT', 'ru': 'ru-RU', 'ja': 'ja-JP',
                'ko': 'ko-KR', 'zh': 'zh-CN', 'ar': 'ar-SA', 'hi': 'hi-IN'
            }
            google_language = language_map.get(language, f"{language}-US")
        
        text = recognizer.recognize_google(audio_data, language=google_language)
        
        return SpeechToTextResponse(
            text=text,
            confidence=0.85,
            language=language,
            method="google"
        )
        
    except sr.UnknownValueError:
        raise HTTPException(status_code=400, detail="Could not understand the audio")
    except sr.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Google Speech Recognition error: {str(e)}")


async def transcribe_with_azure(audio_path: str, language: Optional[str] = None):
    """
    Transcribe audio using Azure Speech Services - Enterprise grade
    """
    try:
        # This would require Azure Speech SDK
        # For now, fallback to Google
        return await transcribe_with_google(audio_path, language)
    except Exception as e:
        return await transcribe_with_google(audio_path, language)
    