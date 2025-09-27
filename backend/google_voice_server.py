#!/usr/bin/env python3
"""
Google Speech-to-Text Voice Server
Simple, fast, accurate speech recognition using Google's API
"""

import os
import tempfile
import base64
import requests
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global Google Speech client status
google_speech_ready = False

# Language mapping for Google Speech-to-Text
GOOGLE_LANGUAGE_MAP = {
    'en': 'en-US', 'es': 'es-ES', 'fr': 'fr-FR', 'de': 'de-DE',
    'it': 'it-IT', 'pt': 'pt-PT', 'ru': 'ru-RU', 'ja': 'ja-JP',
    'ko': 'ko-KR', 'zh': 'zh-CN', 'ar': 'ar-SA', 'hi': 'hi-IN',
    'ur': 'ur-PK', 'bn': 'bn-BD', 'te': 'te-IN', 'ta': 'ta-IN',
    'mr': 'mr-IN', 'gu': 'gu-IN', 'kn': 'kn-IN', 'ml': 'ml-IN',
    'pa': 'pa-IN', 'th': 'th-TH', 'vi': 'vi-VN', 'id': 'id-ID',
    'ms': 'ms-MY', 'tr': 'tr-TR', 'fa': 'fa-IR', 'he': 'he-IL',
    'nl': 'nl-NL', 'sv': 'sv-SE', 'da': 'da-DK', 'no': 'no-NO',
    'fi': 'fi-FI', 'pl': 'pl-PL', 'cs': 'cs-CZ', 'sk': 'sk-SK',
    'hu': 'hu-HU', 'ro': 'ro-RO', 'bg': 'bg-BG', 'hr': 'hr-HR',
    'sr': 'sr-RS', 'sl': 'sl-SI', 'et': 'et-EE', 'lv': 'lv-LV',
    'lt': 'lt-LT', 'uk': 'uk-UA'
}

def setup_google_speech():
    """Setup Google Speech-to-Text client"""
    global google_speech_ready
    
    try:
        api_key = os.getenv('GOOGLE_API_KEY_TRANSLATE')
        if not api_key:
            print("❌ GOOGLE_API_KEY_TRANSLATE not found in .env")
            return False
        
        print("🔄 Setting up Google Speech-to-Text with API key...")
        print(f"✅ Google Speech-to-Text configured successfully")
        google_speech_ready = True
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup Google Speech-to-Text: {e}")
        return False

# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Google Speech-to-Text Server...")
    
    google_setup = setup_google_speech()
    
    if not google_setup:
        print("❌ Google Speech-to-Text setup failed!")
        print("💡 Check your GOOGLE_API_KEY_TRANSLATE in .env file")
    else:
        print("✅ Google Speech-to-Text ready!")
    
    print("🎤 Voice server ready!")
    yield
    # Shutdown
    print("👋 Voice server shutting down...")

# Create FastAPI app
app = FastAPI(title="Google Speech-to-Text Server", version="1.0.0", lifespan=lifespan)

# CORS middleware
origins = [
    "http://localhost:5173",
    "http://localhost:8080", 
    "http://127.0.0.1:5173",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Pydantic models
class SpeechToTextResponse(BaseModel):
    text: str
    confidence: float
    language: Optional[str] = None
    method: str

@app.get("/")
def root():
    return {
        "message": "Google Speech-to-Text Voice Server",
        "method": "google-speech-api-only",
        "google_speech_ready": google_speech_ready,
        "api_key_configured": bool(os.getenv('GOOGLE_API_KEY_TRANSLATE')),
        "supported_languages": len(GOOGLE_LANGUAGE_MAP)
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "method": "google-speech-api-only",
        "google_speech_ready": google_speech_ready,
        "api_key_configured": bool(os.getenv('GOOGLE_API_KEY_TRANSLATE')),
        "supported_languages": len(GOOGLE_LANGUAGE_MAP)
    }

@app.get("/languages")
def get_supported_languages():
    """Get list of supported languages"""
    return {
        "message": "Supported languages for Google Speech-to-Text",
        "total_languages": len(GOOGLE_LANGUAGE_MAP),
        "languages": {
            code: {
                "name": code.upper(),
                "google_code": google_code,
                "native_script": True
            }
            for code, google_code in GOOGLE_LANGUAGE_MAP.items()
        }
    }

async def transcribe_with_google_speech(audio_path: str, language: Optional[str] = None):
    """Transcribe using Google Speech-to-Text API"""
    try:
        api_key = os.getenv('GOOGLE_API_KEY_TRANSLATE')
        if not api_key:
            raise Exception("Google API key not found")
        
        # Read audio file
        with open(audio_path, 'rb') as audio_file:
            audio_content = audio_file.read()
        
        # Convert to base64 for API
        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
        
        # Get Google language code
        google_language = GOOGLE_LANGUAGE_MAP.get(language, 'en-US')
        
        # Prepare request for Google Speech-to-Text REST API
        url = f"https://speech.googleapis.com/v1/speech:recognize?key={api_key}"
        
        payload = {
            "config": {
                "encoding": "WEBM_OPUS",
                "sampleRateHertz": 16000,
                "languageCode": google_language,
                "enableAutomaticPunctuation": True,
                "model": "latest_long",
                "useEnhanced": True
            },
            "audio": {
                "content": audio_base64
            }
        }
        
        print(f"🎤 Transcribing with Google Speech-to-Text...")
        print(f"   Language: {google_language}")
        
        # Make API request
        response = requests.post(url, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Google Speech API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        # Extract transcription
        if 'results' not in result or not result['results']:
            raise Exception("No transcription results from Google Speech API")
        
        transcript = ""
        confidence = 0.0
        
        for res in result['results']:
            if 'alternatives' in res and res['alternatives']:
                alt = res['alternatives'][0]
                transcript += alt.get('transcript', '')
                confidence = max(confidence, alt.get('confidence', 0.0))
        
        if not transcript.strip():
            raise Exception("Empty transcription from Google Speech API")
        
        print(f"✅ Google Speech transcription complete:")
        print(f"   Text: '{transcript.strip()}'")
        print(f"   Language: {google_language}")
        print(f"   Confidence: {confidence:.2f}")
        
        return SpeechToTextResponse(
            text=transcript.strip(),
            confidence=confidence,
            language=language,
            method="google-speech-api"
        )
        
    except Exception as e:
        print(f"❌ Google Speech transcription failed: {e}")
        raise Exception(f"Google Speech transcription failed: {e}")

@app.post("/speech-to-text")
async def speech_to_text(
    audio_file: UploadFile = File(...),
    method: str = "google",
    language: Optional[str] = None
):
    """
    Convert speech to text using Google Speech-to-Text API only
    """
    try:
        # Validate file type
        if not audio_file.content_type or not audio_file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Check if Google Speech is ready
        if not google_speech_ready:
            raise HTTPException(status_code=503, detail="Google Speech-to-Text not configured")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Use Google Speech-to-Text only
            return await transcribe_with_google_speech(temp_file_path, language)

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🎤 Starting Google Speech-to-Text Server...")
    uvicorn.run("google_voice_server:app", host="0.0.0.0", port=8000, reload=True)