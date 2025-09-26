#!/usr/bin/env python3
"""
Minimal FastAPI server focused only on voice recognition
This avoids dependency issues with the main application
"""

import os
import tempfile
from typing import Optional
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import speech_recognition as sr

# Try to import Whisper, fallback gracefully if not available
try:
    import whisper
    import torch

    WHISPER_AVAILABLE = True
    print("✅ Local Whisper available")
except ImportError as e:
    WHISPER_AVAILABLE = False
    print(f"⚠️  Local Whisper not available: {e}")

# Try to import OpenAI for cloud Whisper
try:
    from openai import OpenAI

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI not available for cloud Whisper")

# Load environment variables
load_dotenv()

# Global Whisper model - loaded once at startup
whisper_model = None


def load_whisper_model():
    """Load Whisper model at startup"""
    global whisper_model
    if not WHISPER_AVAILABLE:
        print("❌ Whisper not available, skipping model load")
        return

    try:
        model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
        print(f"🔄 Loading Whisper model: {model_size}")
        whisper_model = whisper.load_model(model_size)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"✅ Whisper model loaded successfully on {device}")
    except Exception as e:
        print(f"❌ Failed to load Whisper model: {e}")
        whisper_model = None


# Lifespan events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Voice Recognition Server...")
    load_whisper_model()
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
        "message": "Voice Recognition Server",
        "whisper_available": WHISPER_AVAILABLE,
        "openai_available": OPENAI_AVAILABLE,
        "model_loaded": whisper_model is not None,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "whisper_local": whisper_model is not None,
        "whisper_cloud": OPENAI_AVAILABLE and bool(os.getenv("OPENAI_API_KEY")),
        "google_speech": True,  # Always available via SpeechRecognition
    }


@app.get("/test-text")
def test_text():
    """Test endpoint to verify text encoding"""
    test_texts = {
        "english": "Hello, this is a test",
        "hindi": "नमस्ते, यह एक परीक्षण है",
        "urdu": "السلام علیکم، یہ ایک ٹیسٹ ہے",
        "mixed": "Hello नमस्ते السلام",
    }

    return {
        "message": "Text encoding test",
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


async def transcribe_with_local_whisper(
    audio_path: str, language: Optional[str] = None
):
    """Transcribe using local Whisper model"""
    global whisper_model

    if not WHISPER_AVAILABLE or whisper_model is None:
        raise Exception("Local Whisper not available")

    try:
        print(f"🎤 Transcribing with local Whisper...")

        # For Hindi, we need to be more specific to avoid Urdu script
        transcribe_options = {
            "language": language,
            "task": "transcribe",
            "verbose": False,
        }

        # Special handling for Hindi to avoid Urdu script
        if language == "hi":
            print(
                "🇮🇳 Hindi language specified - using English transcription to avoid script issues"
            )
            # Use English transcription which gives transliterated Hindi (Roman script)
            # This avoids the Urdu script issue completely
            transcribe_options["language"] = "en"
            print("   Using English language setting to get transliterated Hindi")

        result = whisper_model.transcribe(audio_path, **transcribe_options)

        # Calculate confidence from segments
        confidence = 0.95
        if "segments" in result and result["segments"]:
            confidences = [seg.get("avg_logprob", 0) for seg in result["segments"]]
            if confidences:
                avg_logprob = sum(confidences) / len(confidences)
                confidence = min(0.99, max(0.7, (avg_logprob + 1) * 0.5 + 0.5))

        detected_language = result.get("language", language)
        transcribed_text = result["text"].strip()

        # For Hindi requests, we used English transcription to avoid script issues
        if language == "hi" and transcribe_options.get("language") == "en":
            print(
                "✅ Hindi transcribed using English to get Roman script (avoids Urdu script issue)"
            )
            corrected_text = f"{transcribed_text}"
            detected_language = "hi"  # Override to show it was Hindi request
        else:
            # Check for script mismatch and correct if needed
            corrected_text = correct_script_mismatch(
                transcribed_text, detected_language, language
            )

        # If we have a script mismatch for Hindi, try re-transcribing with different approach
        if language == "hi" and detect_script(transcribed_text) == "arabic":
            print("🔄 Attempting re-transcription with Hindi optimization...")
            try:
                # Try without specifying language to let Whisper auto-detect
                result_retry = whisper_model.transcribe(
                    audio_path,
                    task="transcribe",
                    verbose=False,
                    # Let Whisper decide the language naturally
                )

                retry_text = result_retry["text"].strip()
                retry_script = detect_script(retry_text)

                print(f"🔄 Retry result:")
                print(f"   Retry Text: '{retry_text}'")
                print(f"   Retry Script: {retry_script}")
                print(f"   Retry Language: {result_retry.get('language', 'unknown')}")

                # If retry gives us Devanagari script, use it
                if retry_script == "devanagari":
                    print("✅ Retry successful - got Devanagari script!")
                    corrected_text = retry_text
                    detected_language = result_retry.get("language", detected_language)

            except Exception as retry_error:
                print(f"⚠️  Retry failed: {retry_error}")
                # Keep original result

        print(f"✅ Transcription complete:")
        print(f"   Original Text: '{result['text']}'")
        print(f"   Stripped Text: '{transcribed_text}'")
        print(f"   Corrected Text: '{corrected_text}'")
        print(f"   Text Length: {len(corrected_text)}")
        print(f"   Detected Language: {detected_language}")
        print(f"   Confidence: {confidence:.2f}")
        print(f"   Text Encoding: {corrected_text.encode('utf-8')}")

        return SpeechToTextResponse(
            text=corrected_text,
            confidence=confidence,
            language=detected_language,
            method="whisper-local",
        )

    except Exception as e:
        raise Exception(f"Local Whisper transcription failed: {e}")


async def transcribe_with_cloud_whisper(
    audio_path: str, language: Optional[str] = None
):
    """Transcribe using OpenAI Whisper API"""
    if not OPENAI_AVAILABLE:
        raise Exception("OpenAI not available")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OpenAI API key not found")

    try:
        client = OpenAI(api_key=api_key)

        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="verbose_json",
            )

        return SpeechToTextResponse(
            text=transcript.text,
            confidence=0.95,
            language=getattr(transcript, "language", language),
            method="whisper-cloud",
        )

    except Exception as e:
        raise Exception(f"Cloud Whisper transcription failed: {e}")


async def transcribe_with_google(audio_path: str, language: Optional[str] = None):
    """Transcribe using Google Speech Recognition (free)"""
    try:
        recognizer = sr.Recognizer()

        with sr.AudioFile(audio_path) as source:
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.record(source)

        # Map language codes for Google
        google_language = "en-US"
        if language:
            language_map = {
                "en": "en-US",
                "es": "es-ES",
                "fr": "fr-FR",
                "de": "de-DE",
                "it": "it-IT",
                "pt": "pt-PT",
                "ru": "ru-RU",
                "ja": "ja-JP",
                "ko": "ko-KR",
                "zh": "zh-CN",
                "ar": "ar-SA",
                "hi": "hi-IN",
            }
            google_language = language_map.get(language, f"{language}-US")

        text = recognizer.recognize_google(audio_data, language=google_language)

        return SpeechToTextResponse(
            text=text, confidence=0.85, language=language, method="google-speech"
        )

    except sr.UnknownValueError:
        raise Exception("Could not understand the audio")
    except sr.RequestError as e:
        raise Exception(f"Google Speech Recognition error: {e}")


@app.post("/speech-to-text")
async def speech_to_text(
    audio_file: UploadFile = File(...),
    method: str = "whisper",
    language: Optional[str] = None,
):
    """
    Convert speech to text using various methods
    Methods: whisper (local), whisper-cloud, google
    """
    try:
        # Validate file type
        if not audio_file.content_type or not audio_file.content_type.startswith(
            "audio/"
        ):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Try methods in order of preference
            if method == "whisper" or method == "whisper-local":
                try:
                    return await transcribe_with_local_whisper(temp_file_path, language)
                except Exception as e:
                    print(f"Local Whisper failed: {e}")
                    if method == "whisper-local":
                        raise HTTPException(status_code=500, detail=str(e))
                    # Fall through to try other methods

            if method == "whisper-cloud" or (method == "whisper" and not whisper_model):
                try:
                    return await transcribe_with_cloud_whisper(temp_file_path, language)
                except Exception as e:
                    print(f"Cloud Whisper failed: {e}")
                    if method == "whisper-cloud":
                        raise HTTPException(status_code=500, detail=str(e))
                    # Fall through to Google

            # Fallback to Google Speech Recognition
            return await transcribe_with_google(temp_file_path, language)

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
