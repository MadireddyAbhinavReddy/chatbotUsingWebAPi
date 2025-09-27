#!/usr/bin/env python3
"""
Install Google Speech-to-Text dependencies
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required packages"""
    packages = [
        "google-cloud-speech==2.21.0",
        "requests==2.31.0"
    ]
    
    print("📦 Installing Google Speech-to-Text dependencies...")
    
    for package in packages:
        print(f"🔄 Installing {package}...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {package}: {e}")
            return False
    
    return True

def check_api_key():
    """Check if Google API key is configured"""
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('GOOGLE_API_KEY_TRANSLATE')
    if api_key:
        print(f"✅ Google API key found: {api_key[:10]}...")
        return True
    else:
        print("❌ GOOGLE_API_KEY_TRANSLATE not found in .env")
        return False

def main():
    print("🎤 Google Speech-to-Text Setup")
    print("=" * 40)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return False
    
    # Check API key
    if not check_api_key():
        print("\n💡 Please add your Google API key to .env:")
        print("GOOGLE_API_KEY_TRANSLATE=your_api_key_here")
        return False
    
    print("\n🎉 Google Speech-to-Text setup complete!")
    print("\n🚀 Next steps:")
    print("1. Start the voice server: python voice_server.py")
    print("2. Google Speech-to-Text will be used as primary method")
    print("3. Whisper will be available as fallback")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)