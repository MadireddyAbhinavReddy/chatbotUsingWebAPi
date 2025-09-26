import React, { useEffect, useRef, useState } from 'react';
import { Button } from './button';
import { Mic, MicOff, Volume2, Square } from 'lucide-react';
import { useVoiceRecognition } from '@/hooks/useVoiceRecognition';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from './tooltip';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  onStart?: () => void;
  onStop?: () => void;
  className?: string;
  disabled?: boolean;
  language?: string;
  useBackend?: boolean; // Option to use backend speech recognition
}

export const VoiceInput: React.FC<VoiceInputProps> = ({
  onTranscript,
  onStart,
  onStop,
  className,
  disabled = false,
  language = 'en-US',
  useBackend = false
}) => {
  const { toast } = useToast();
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  
  const {
    transcript,
    isListening,
    isSupported,
    startListening,
    stopListening,
    resetTranscript,
    error
  } = useVoiceRecognition({
    continuous: true, // Enable continuous mode with manual control
    interimResults: true,
    language
  });

  // Handle transcript changes with debouncing
  useEffect(() => {
    if (transcript && transcript.trim()) {
      const timeoutId = setTimeout(() => {
        onTranscript(transcript);
      }, 100); // Small delay to avoid multiple rapid updates
      
      return () => clearTimeout(timeoutId);
    }
  }, [transcript, onTranscript]);

  // Handle errors
  useEffect(() => {
    if (error) {
      toast({
        title: "Voice Recognition Error",
        description: error,
        variant: "destructive",
      });
    }
  }, [error, toast]);

  // Handle listening state changes - only call callbacks on user action, not automatic stops
  const [wasListening, setWasListening] = useState(false);
  
  useEffect(() => {
    if ((isListening || isRecording) && !wasListening && onStart) {
      setWasListening(true);
      onStart();
    } else if (!isListening && !isRecording && wasListening && onStop) {
      setWasListening(false);
      onStop();
    }
  }, [isListening, isRecording, wasListening, onStart, onStop]);

  // Backend speech recognition using MediaRecorder
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await sendAudioToBackend(audioBlob);
        
        // Stop all tracks to release microphone
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      toast({
        title: "Recording Error",
        description: "Could not access microphone. Please check permissions.",
        variant: "destructive",
      });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendAudioToBackend = async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.wav');

      const response = await fetch('http://localhost:8000/speech-to-text', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      onTranscript(result.text);
      
      toast({
        title: "Speech Recognized",
        description: `Confidence: ${(result.confidence * 100).toFixed(1)}%`,
      });
    } catch (error) {
      console.error('Error sending audio to backend:', error);
      toast({
        title: "Recognition Error",
        description: "Failed to process speech. Please try again.",
        variant: "destructive",
      });
    }
  };

  const handleToggleListening = () => {
    if (useBackend) {
      // Use backend speech recognition
      if (isRecording) {
        stopRecording();
      } else {
        startRecording();
      }
    } else {
      // Use browser speech recognition
      if (!isSupported) {
        toast({
          title: "Not Supported",
          description: "Speech recognition is not supported in this browser. Please try Chrome, Edge, or Safari.",
          variant: "destructive",
        });
        return;
      }

      if (isListening) {
        stopListening();
      } else {
        resetTranscript();
        startListening();
      }
    }
  };

  if (!useBackend && !isSupported) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              disabled
              className={cn("size-10 text-gray-400", className)}
            >
              <MicOff className="size-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            Voice input not supported in this browser
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  const isActive = useBackend ? isRecording : isListening;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleToggleListening}
            disabled={disabled}
            className={cn(
              "size-10 transition-all duration-200",
              isActive 
                ? "text-red-500 hover:text-red-600 bg-red-50 hover:bg-red-100 dark:bg-red-950 dark:hover:bg-red-900 animate-pulse" 
                : "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200",
              className
            )}
          >
            {isActive ? (
              <div className="relative">
                {useBackend ? <Square className="size-4" /> : <Mic className="size-4" />}
                <div className="absolute -top-1 -right-1 size-2 bg-red-500 rounded-full animate-ping" />
              </div>
            ) : (
              <Mic className="size-4" />
            )}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          {isActive ? "Stop voice input" : "Start voice input"}
          {useBackend && <div className="text-xs text-gray-400 mt-1">Using server processing</div>}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};