#!/usr/bin/env python3
"""
Minimal FastAPI server focused only on voice recognition
This avoids dependency issues with the main application
"""

import os
import tempfile
import base64
from typing import Optional
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Google Speech-to-Text only - no Whisper needed
import requests
print("✅ Using Google Speech-to-Text API only")

# Load environment variables
load_dotenv()

# Global Google Speech client
google_speech_ready = False

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
    print("🚀 Starting Voice Recognition Server...")
    print("🎤 Using Google Speech-to-Text API only")
    
    # Setup Google Speech-to-Text
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
app = FastAPI(title="Voice Recognition Server", version="1.0.0", lifespan=lifespan)

# CORS middleware
origins = [
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        "message": "Voice Recognition Server - Google Speech-to-Text API Only",
        "method": "google-speech-api-only",
        "google_speech_ready": google_speech_ready,
        "api_key_configured": bool(os.getenv('GOOGLE_API_KEY_TRANSLATE'))
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "method": "google-speech-api-only",
        "google_speech_ready": google_speech_ready,
        "api_key_configured": bool(os.getenv('GOOGLE_API_KEY_TRANSLATE')),
        "supported_languages": len(LANGUAGE_CONFIGS)
    }


@app.get("/model-info")
def get_model_info():
    """Get information about Google Speech-to-Text API"""
    return {
        "message": "Google Speech-to-Text API information",
        "method": "google-speech-api",
        "api_ready": google_speech_ready,
        "api_key_configured": bool(os.getenv('GOOGLE_API_KEY_TRANSLATE')),
        "features": {
            "real_time": True,
            "native_scripts": True,
            "multilingual": True,
            "cloud_processing": True,
            "high_accuracy": True
        },
        "advantages": {
            "speed": "1-3 seconds processing",
            "accuracy": "95-98% for supported languages",
            "scripts": "Native script output (Hindi gets Devanagari)",
            "reliability": "Google's enterprise infrastructure"
        },
        "supported_languages": len(LANGUAGE_CONFIGS)
    }

@app.get("/languages")
def get_supported_languages():
    """Get list of supported languages with their configurations"""
    return {
        "message": "Supported languages for Google Speech-to-Text",
        "total_languages": len(LANGUAGE_CONFIGS),
        "languages": {
            code: {
                "name": config["name"],
                "native_name": config.get("native_name", config["name"]),
                "google_code": config.get("google_code", f"{code}-US"),
                "script": config.get("script", "Latin"),
                "speakers": config.get("speakers", "Unknown"),
                "flag": config.get("flag", "🌍"),
                "region": config.get("region", "Global")
            }
            for code, config in LANGUAGE_CONFIGS.items()
        },
        "indian_languages": [
            code for code, config in LANGUAGE_CONFIGS.items() 
            if config.get("flag") == "🇮🇳"
        ],
        "total_indian_languages": len([
            code for code, config in LANGUAGE_CONFIGS.items() 
            if config.get("flag") == "🇮🇳"
        ])
    }


@app.get("/test-text")
def test_text():
    """Test endpoint to verify text encoding for multiple languages"""
    test_texts = {
        "english": "Hello, this is a test",
        "spanish": "Hola, esto es una prueba",
        "french": "Bonjour, ceci est un test",
        "german": "Hallo, das ist ein Test",
        "hindi": "नमस्ते, यह एक परीक्षण है",
        "urdu": "السلام علیکم، یہ ایک ٹیسٹ ہے",
        "arabic": "مرحبا، هذا اختبار",
        "chinese": "你好，这是一个测试",
        "japanese": "こんにちは、これはテストです",
        "korean": "안녕하세요, 이것은 테스트입니다",
        "russian": "Привет, это тест",
        "mixed": "Hello नमस्ते السلام 你好",
    }

    return {
        "message": "Multi-language text encoding test",
        "total_languages": len(test_texts),
        "texts": test_texts,
        "encoding_info": {
            lang: {
                "text": text,
                "length": len(text),
                "bytes": text.encode("utf-8").hex(),
                "utf8_valid": True,
            }
            for lang, text in test_texts.items()
        },
    }


# Comprehensive Indian Languages Configuration for Google Speech-to-Text
LANGUAGE_CONFIGS = {
    # === INDIAN LANGUAGES (Primary Focus) ===
    "hi": {  # Hindi - Most spoken Indian language
        "name": "Hindi",
        "native_name": "हिन्दी",
        "google_code": "hi-IN",
        "script": "Devanagari",
        "speakers": "600M+",
        "flag": "🇮🇳",
        "region": "North India"
    },
    "bn": {  # Bengali - Second most spoken
        "name": "Bengali", 
        "native_name": "বাংলা",
        "google_code": "bn-IN",
        "script": "Bengali",
        "speakers": "300M+",
        "flag": "🇮🇳",
        "region": "West Bengal, Bangladesh"
    },
    "te": {  # Telugu - Third most spoken
        "name": "Telugu",
        "native_name": "తెలుగు", 
        "google_code": "te-IN",
        "script": "Telugu",
        "speakers": "95M+",
        "flag": "🇮🇳",
        "region": "Andhra Pradesh, Telangana"
    },
    "mr": {  # Marathi
        "name": "Marathi",
        "native_name": "मराठी",
        "google_code": "mr-IN", 
        "script": "Devanagari",
        "speakers": "83M+",
        "flag": "🇮🇳",
        "region": "Maharashtra"
    },
    "ta": {  # Tamil
        "name": "Tamil",
        "native_name": "தமிழ்",
        "google_code": "ta-IN",
        "script": "Tamil",
        "speakers": "78M+", 
        "flag": "🇮🇳",
        "region": "Tamil Nadu"
    },
    "ur": {  # Urdu
        "name": "Urdu",
        "native_name": "اردو",
        "google_code": "ur-IN",
        "script": "Arabic/Urdu",
        "speakers": "70M+",
        "flag": "🇮🇳",
        "region": "North India, Pakistan"
    },
    "gu": {  # Gujarati
        "name": "Gujarati", 
        "native_name": "ગુજરાતી",
        "google_code": "gu-IN",
        "script": "Gujarati",
        "speakers": "56M+",
        "flag": "🇮🇳",
        "region": "Gujarat"
    },
    "kn": {  # Kannada
        "name": "Kannada",
        "native_name": "ಕನ್ನಡ",
        "google_code": "kn-IN",
        "script": "Kannada", 
        "speakers": "44M+",
        "flag": "🇮🇳",
        "region": "Karnataka"
    },
    "ml": {  # Malayalam
        "name": "Malayalam",
        "native_name": "മലയാളം",
        "google_code": "ml-IN",
        "script": "Malayalam",
        "speakers": "38M+",
        "flag": "🇮🇳", 
        "region": "Kerala"
    },
    "or": {  # Odia
        "name": "Odia",
        "native_name": "ଓଡ଼ିଆ",
        "google_code": "or-IN",
        "script": "Odia",
        "speakers": "38M+",
        "flag": "🇮🇳",
        "region": "Odisha"
    },
    "pa": {  # Punjabi
        "name": "Punjabi",
        "native_name": "ਪੰਜਾਬੀ", 
        "google_code": "pa-IN",
        "script": "Gurmukhi",
        "speakers": "33M+",
        "flag": "🇮🇳",
        "region": "Punjab"
    },
    "as": {  # Assamese
        "name": "Assamese",
        "native_name": "অসমীয়া",
        "google_code": "as-IN",
        "script": "Bengali/Assamese",
        "speakers": "15M+",
        "flag": "🇮🇳",
        "region": "Assam"
    },
    "bho": {  # Bhojpuri
        "name": "Bhojpuri", 
        "native_name": "भोजपुरी",
        "google_code": "bho-IN",
        "script": "Devanagari",
        "speakers": "52M+",
        "flag": "🇮🇳",
        "region": "Bihar, UP"
    },
    "mai": {  # Maithili
        "name": "Maithili",
        "native_name": "मैथिली",
        "google_code": "mai-IN", 
        "script": "Devanagari",
        "speakers": "13M+",
        "flag": "🇮🇳",
        "region": "Bihar, Nepal"
    },
    "ne": {  # Nepali
        "name": "Nepali",
        "native_name": "नेपाली",
        "google_code": "ne-NP",
        "script": "Devanagari",
        "speakers": "16M+",
        "flag": "🇳🇵",
        "region": "Nepal, India"
    },
    
    # === INTERNATIONAL LANGUAGES ===
    "en": {  # English
        "name": "English",
        "native_name": "English", 
        "google_code": "en-US",
        "script": "Latin",
        "speakers": "1.5B+",
        "flag": "🇺🇸",
        "region": "Global"
    },
    "es": {  # Spanish
        "name": "Spanish",
        "native_name": "Español",
        "google_code": "es-ES",
        "script": "Latin",
        "speakers": "500M+",
        "flag": "🇪🇸", 
        "region": "Spain, Latin America"
    },
    "fr": {  # French
        "name": "French",
        "native_name": "Français",
        "google_code": "fr-FR",
        "script": "Latin",
        "speakers": "280M+",
        "flag": "🇫🇷",
        "region": "France, Africa"
    },
    "ar": {  # Arabic
        "name": "Arabic",
        "native_name": "العربية",
        "google_code": "ar-SA",
        "script": "Arabic", 
        "speakers": "400M+",
        "flag": "🇸🇦",
        "region": "Middle East, North Africa"
    },
    "zh": {  # Chinese
        "name": "Chinese",
        "native_name": "中文",
        "google_code": "zh-CN",
        "script": "Chinese",
        "speakers": "1.1B+",
        "flag": "🇨🇳",
        "region": "China, Taiwan"
    },
    "ja": {  # Japanese
        "name": "Japanese", 
        "native_name": "日本語",
        "google_code": "ja-JP",
        "script": "Japanese",
        "speakers": "125M+",
        "flag": "🇯🇵",
        "region": "Japan"
    },
    "ko": {  # Korean
        "name": "Korean",
        "native_name": "한국어",
        "google_code": "ko-KR",
        "script": "Korean",
        "speakers": "77M+",
        "flag": "🇰🇷",
        "region": "Korea"
    },
    "ru": {  # Russian
        "name": "Russian",
        "native_name": "Русский",
        "google_code": "ru-RU", 
        "script": "Cyrillic",
        "speakers": "258M+",
        "flag": "🇷🇺",
        "region": "Russia, Eastern Europe"
    },
    "de": {  # German
        "name": "German",
        "native_name": "Deutsch",
        "google_code": "de-DE",
        "script": "Latin",
        "speakers": "100M+",
        "flag": "🇩🇪",
        "region": "Germany, Austria"
    },
    "it": {  # Italian
        "name": "Italian",
        "native_name": "Italiano", 
        "google_code": "it-IT",
        "script": "Latin",
        "speakers": "65M+",
        "flag": "🇮🇹",
        "region": "Italy"
    },
    "pt": {  # Portuguese
        "name": "Portuguese",
        "native_name": "Português",
        "google_code": "pt-PT",
        "script": "Latin",
        "speakers": "260M+",
        "flag": "🇵🇹",
        "region": "Portugal, Brazil"
    }
}


def get_language_config(language_code: str) -> dict:
    """Get configuration for a specific language"""
    return LANGUAGE_CONFIGS.get(
        language_code,
        {
            "name": language_code.upper(),
            "script_issue": False,
            "workaround": None,
            "flag": "🌍",
        },
    )


def detect_script(text: str) -> str:
    """Detect the script/writing system of the text"""
    if not text.strip():
        return "unknown"

    # Count characters from different scripts
    devanagari_count = sum(
        1 for char in text if "\u0900" <= char <= "\u097f"
    )  # Devanagari (Hindi)
    arabic_count = sum(
        1 for char in text if "\u0600" <= char <= "\u06ff"
    )  # Arabic/Urdu
    latin_count = sum(1 for char in text if "A" <= char <= "Z" or "a" <= char <= "z")

    total_chars = len([c for c in text if c.isalpha()])

    if total_chars == 0:
        return "unknown"

    # Determine dominant script
    if devanagari_count / total_chars > 0.5:
        return "devanagari"
    elif arabic_count / total_chars > 0.5:
        return "arabic"
    elif latin_count / total_chars > 0.5:
        return "latin"
    else:
        return "mixed"


def correct_script_mismatch(text: str, detected_lang: str, requested_lang: str) -> str:
    """Correct script mismatches for similar languages"""
    if not text.strip():
        return text

    detected_script = detect_script(text)

    print(f"🔍 Script Analysis:")
    print(f"   Detected Script: {detected_script}")
    print(f"   Detected Language: {detected_lang}")
    print(f"   Requested Language: {requested_lang}")

    # If user requested Hindi but got Arabic/Urdu script, suggest re-transcription
    if requested_lang == "hi" and detected_script == "arabic":
        print("⚠️  Script mismatch: Requested Hindi but got Arabic/Urdu script")
        print(
            "💡 Suggestion: Try speaking more distinctly Hindi words or use longer phrases"
        )
        # For now, return the text as-is but with a warning
        return f"[Script Mismatch - Got Urdu script for Hindi] {text}"

    # If detected Hindi but got Arabic script (common Whisper issue)
    if detected_lang == "hi" and detected_script == "arabic":
        print("⚠️  Whisper detected Hindi but transcribed in Urdu script")
        return f"[Hindi detected but Urdu script] {text}"

    return text


# Removed Whisper - using Google Speech-to-Text only

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
        
        # Handle language codes for Google Speech-to-Text
        google_language = 'en-US'  # Default
        if language:
            # If already in Google format (contains hyphen), use as-is
            if '-' in language:
                google_language = language
            else:
                # Check if language exists in our comprehensive config
                if language in LANGUAGE_CONFIGS:
                    google_language = LANGUAGE_CONFIGS[language]["google_code"]
                else:
                    # Fallback mapping for any missing languages
                    fallback_map = {
                        'en': 'en-US', 'es': 'es-ES', 'fr': 'fr-FR', 'de': 'de-DE',
                        'it': 'it-IT', 'pt': 'pt-PT', 'ru': 'ru-RU', 'ja': 'ja-JP',
                        'ko': 'ko-KR', 'zh': 'zh-CN', 'ar': 'ar-SA'
                    }
                    google_language = fallback_map.get(language, 'en-US')
        
        # Prepare request for Google Speech-to-Text REST API
        url = f"https://speech.googleapis.com/v1/speech:recognize?key={api_key}"
        
        payload = {
            "config": {
                "encoding": "WEBM_OPUS",
                "languageCode": google_language,
                "enableAutomaticPunctuation": True,
                "model": "latest_long"  # Use latest model for better accuracy
            },
            "audio": {
                "content": audio_base64
            }
        }
        
        print(f"🎤 Transcribing with Google Speech-to-Text...")
        print(f"   Input language: {language}")
        print(f"   Google language: {google_language}")
        
        # Make API request
        import requests
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
    language: Optional[str] = None,
):
    """
    Convert speech to text using Google Speech-to-Text API only
    """
    try:
        # Validate file type
        if not audio_file.content_type or not audio_file.content_type.startswith(
            "audio/"
        ):
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

    print("🎤 Starting Voice Recognition Server...")
    uvicorn.run("voice_server:app", host="0.0.0.0", port=8000, reload=True)
