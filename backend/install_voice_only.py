#!/usr/bin/env python3
"""
Install only voice recognition dependencies
This avoids conflicts with the main application dependencies
"""

import subprocess
import sys
import platform
import shutil

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        return False

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    if shutil.which('ffmpeg'):
        print("✅ FFmpeg is already installed")
        return True
    
    print("❌ FFmpeg not found. Please install it:")
    system = platform.system().lower()
    
    if system == "windows":
        print("  Windows: choco install ffmpeg")
    elif system == "darwin":  # macOS
        print("  macOS: brew install ffmpeg")
    elif system == "linux":
        print("  Ubuntu/Debian: sudo apt install ffmpeg")
    
    return False

def install_voice_dependencies():
    """Install minimal voice recognition dependencies"""
    
    # Core dependencies for voice server
    dependencies = [
        "fastapi==0.104.1",
        "uvicorn==0.24.0", 
        "python-multipart==0.0.6",
        "python-dotenv==1.0.0",
        "SpeechRecognition==3.10.0",
        "pydub==0.25.1",
        "requests==2.31.0"
    ]
    
    # Optional: Whisper dependencies
    whisper_deps = [
        "openai-whisper==20231117",
        "torch>=1.10.0",
        "torchaudio>=0.10.0"
    ]
    
    # Optional: OpenAI API
    openai_deps = [
        "openai==1.3.0"
    ]
    
    print("📦 Installing core voice dependencies...")
    for dep in dependencies:
        if not run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}"):
            return False
    
    print("\n🎤 Installing Whisper (local speech recognition)...")
    for dep in whisper_deps:
        if not run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}"):
            print(f"⚠️  Failed to install {dep} - Whisper may not work")
    
    print("\n☁️  Installing OpenAI (cloud speech recognition)...")
    for dep in openai_deps:
        if not run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}"):
            print(f"⚠️  Failed to install {dep} - Cloud Whisper may not work")
    
    return True

def test_installation():
    """Test if voice recognition works"""
    try:
        print("\n🧪 Testing installation...")
        
        # Test FastAPI
        import fastapi
        print("✅ FastAPI available")
        
        # Test SpeechRecognition
        import speech_recognition
        print("✅ SpeechRecognition available")
        
        # Test Whisper (optional)
        try:
            import whisper
            print("✅ Local Whisper available")
        except ImportError:
            print("⚠️  Local Whisper not available (optional)")
        
        # Test OpenAI (optional)
        try:
            import openai
            print("✅ OpenAI available")
        except ImportError:
            print("⚠️  OpenAI not available (optional)")
        
        print("\n🎉 Voice recognition installation successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Installation test failed: {e}")
        return False

def main():
    """Main installation process"""
    print("🎤 Voice Recognition Installation")
    print("=" * 40)
    
    # Check FFmpeg
    if not check_ffmpeg():
        print("\n⚠️  Please install FFmpeg first")
        return False
    
    # Install dependencies
    if not install_voice_dependencies():
        return False
    
    # Test installation
    if not test_installation():
        return False
    
    print("\n🚀 Next steps:")
    print("1. Start voice server: python voice_server.py")
    print("2. Or use the start script: python start_voice_server.py")
    print("3. Server will be available at: http://localhost:8000")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)