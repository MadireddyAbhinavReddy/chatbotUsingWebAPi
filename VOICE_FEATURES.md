# Voice-to-Text Features

## Overview
The application now includes voice-to-text functionality with a microphone icon that allows users to speak their queries instead of typing them.

## Features

### 🎤 Voice Input Component
- **Microphone Icon**: Click the mic button next to the image upload button
- **Visual Feedback**: The mic button shows recording state with animation and color changes
- **Multi-language Support**: Automatically adapts to the selected language in the interface
- **Browser Integration**: Uses Web Speech API for real-time speech recognition

### 🌐 Language Support
The voice input automatically detects and uses the language selected in the interface:
- English (en-US)
- Spanish (es-ES)
- French (fr-FR)
- German (de-DE)
- Italian (it-IT)
- Portuguese (pt-PT)
- Russian (ru-RU)
- Japanese (ja-JP)
- Korean (ko-KR)
- Chinese (zh-CN)
- Arabic (ar-SA)
- Hindi (hi-IN)

### 🔧 Technical Implementation

#### Frontend Components
- **VoiceInput Component** (`src/components/ui/VoiceInput.tsx`): Main voice input interface
- **useVoiceRecognition Hook** (`src/hooks/useVoiceRecognition.ts`): Custom hook for speech recognition
- **Speech Types** (`src/types/speech.d.ts`): TypeScript declarations for Web Speech API

#### Backend Support (Optional)
- **FastAPI Endpoint**: `/speech-to-text` for server-side speech processing
- **Dependencies**: SpeechRecognition library for advanced audio processing
- **File Support**: Handles WAV, FLAC, and other audio formats

## Usage

### Basic Usage
1. Click the microphone icon next to the image upload button
2. Start speaking your query
3. The text will appear in the input field in real-time
4. Click the mic again to stop recording

### Browser Compatibility
- **Chrome**: Full support with Web Speech API
- **Edge**: Full support with Web Speech API
- **Safari**: Full support with Web Speech API
- **Firefox**: Limited support (may require backend processing)

### Permissions
- The browser will request microphone permissions on first use
- Grant permission to enable voice input functionality

## Installation & Setup

### Frontend Only (Web Speech API)
No additional setup required - works out of the box in supported browsers.

### Backend Speech Processing (Optional)
If you want to use server-side speech recognition:

1. Install Python dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Start the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```

3. The voice input will automatically use backend processing when available.

## Troubleshooting

### Common Issues
1. **Microphone not working**: Check browser permissions
2. **No speech detected**: Ensure microphone is not muted
3. **Language not recognized**: Verify the selected language matches your speech
4. **Backend errors**: Ensure FastAPI server is running on port 8000

### Error Messages
- "Speech recognition is not supported in this browser" - Try Chrome, Edge, or Safari
- "Could not access microphone" - Check browser permissions
- "Failed to process speech" - Try speaking more clearly or check internet connection

## Future Enhancements
- Voice commands for specific actions
- Custom wake words
- Offline speech recognition
- Voice response synthesis
- Advanced noise cancellation