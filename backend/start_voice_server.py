#!/usr/bin/env python3
"""
Start the voice-only server
This avoids dependency conflicts with the main application
"""

import os
import sys
import subprocess
from pathlib import Path

def check_voice_installation():
    """Check if voice dependencies are installed"""
    try:
        import fastapi
        import speech_recognition
        print("✅ Core voice dependencies available")
        
        # Check optional dependencies
        try:
            import whisper
            print("✅ Local Whisper available")
        except ImportError:
            print("⚠️  Local Whisper not available (install with: pip install openai-whisper torch)")
        
        try:
            import openai
            print("✅ OpenAI available")
        except ImportError:
            print("⚠️  OpenAI not available (install with: pip install openai)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Voice dependencies missing: {e}")
        print("Run: python install_voice_only.py")
        return False

def setup_env():
    """Setup environment file if needed"""
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("📝 Creating basic .env file...")
        with open(env_file, 'w') as f:
            f.write("# Voice Recognition Configuration\n")
            f.write("WHISPER_MODEL_SIZE=base\n")
            f.write("# OPENAI_API_KEY=your_key_here\n")
        print("✅ Created .env file")

def start_voice_server():
    """Start the voice recognition server"""
    print("🎤 Starting Voice Recognition Server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("🔍 Health check: http://localhost:8000/health")
    print("\n💡 Features available:")
    print("  - Local Whisper (if installed)")
    print("  - Cloud Whisper (if API key provided)")
    print("  - Google Speech Recognition (always available)")
    print("\n" + "="*50)
    
    try:
        # Start the voice server
        voice_server_path = Path(__file__).parent / "voice_server.py"
        subprocess.run([
            sys.executable, str(voice_server_path)
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Voice server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        return False
    except FileNotFoundError:
        print("❌ voice_server.py not found")
        return False
    
    return True

def main():
    """Main function"""
    print("🎤 Voice Recognition Server Starter")
    print("=" * 40)
    
    # Check installation
    if not check_voice_installation():
        return False
    
    # Setup environment
    setup_env()
    
    # Start server
    return start_voice_server()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)