import { useState, useEffect, useRef, useCallback } from 'react';

interface VoiceRecognitionOptions {
  continuous?: boolean;
  interimResults?: boolean;
  language?: string;
}

interface VoiceRecognitionResult {
  transcript: string;
  confidence: number;
  isFinal: boolean;
}

interface UseVoiceRecognitionReturn {
  transcript: string;
  isListening: boolean;
  isSupported: boolean;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;
  error: string | null;
}

export const useVoiceRecognition = (
  options: VoiceRecognitionOptions = {}
): UseVoiceRecognitionReturn => {
  const {
    continuous = true, // Set to true for continuous listening
    interimResults = true,
    language = 'en-US'
  } = options;

  const [transcript, setTranscript] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const finalTranscriptRef = useRef<string>('');
  const shouldStopRef = useRef<boolean>(false); // Track if user wants to stop

  // Check if speech recognition is supported
  const isSupported = typeof window !== 'undefined' && 
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    finalTranscriptRef.current = '';
    setError(null);
  }, []);

  const startListening = useCallback(() => {
    if (!isSupported) {
      setError('Speech recognition is not supported in this browser');
      return;
    }

    if (isListening) return;

    shouldStopRef.current = false; // Reset stop flag

    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();

      recognition.continuous = continuous;
      recognition.interimResults = interimResults;
      recognition.lang = language;

      recognition.onstart = () => {
        setIsListening(true);
        setError(null);
      };

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let finalTranscript = finalTranscriptRef.current;
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            finalTranscript += result[0].transcript;
            finalTranscriptRef.current = finalTranscript;
          } else {
            interimTranscript += result[0].transcript;
          }
        }

        setTranscript(finalTranscript + interimTranscript);
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        // Only show error for serious issues, not for normal stops
        if (event.error !== 'aborted' && event.error !== 'no-speech') {
          setError(`Speech recognition error: ${event.error}`);
        }
        if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
          setIsListening(false);
          shouldStopRef.current = true;
        }
      };

      recognition.onend = () => {
        // Only stop if the user explicitly requested it
        if (shouldStopRef.current) {
          setIsListening(false);
          shouldStopRef.current = false;
        } else {
          // Auto-restart if it stopped unexpectedly and we're still supposed to be listening
          if (recognitionRef.current && isListening) {
            try {
              setTimeout(() => {
                if (recognitionRef.current && !shouldStopRef.current) {
                  recognitionRef.current.start();
                }
              }, 100);
            } catch (err) {
              console.log('Recognition restart failed:', err);
              setIsListening(false);
            }
          }
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      setError('Failed to start speech recognition');
      setIsListening(false);
    }
  }, [isSupported, isListening, continuous, interimResults, language]);

  const stopListening = useCallback(() => {
    shouldStopRef.current = true; // Set flag to indicate user wants to stop
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setIsListening(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      shouldStopRef.current = true;
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  return {
    transcript,
    isListening,
    isSupported,
    startListening,
    stopListening,
    resetTranscript,
    error
  };
};