import React, { useState, useCallback } from 'react';
import { useTheme } from '../../hooks/useTheme';
import { IconButton, Tooltip } from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import { useVoiceRecognition } from '../../hooks/useVoiceRecognition';

const VoiceInput = ({ onVoiceInput }) => {
  const [isRecording, setIsRecording] = useState(false);
  const { theme } = useTheme();
  const { startRecording, stopRecording, isSupported } = useVoiceRecognition({
    onResult: (text) => {
      onVoiceInput(text);
      setIsRecording(false);
    },
    onError: (error) => {
      console.error('Voice recognition error:', error);
      setIsRecording(false);
    }
  });

  const handleToggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
    setIsRecording(!isRecording);
  }, [isRecording, startRecording, stopRecording]);

  if (!isSupported) {
    return null;
  }

  return (
    <Tooltip title={isRecording ? "Stop recording" : "Start voice input"}>
      <IconButton
        onClick={handleToggleRecording}
        sx={{
          color: isRecording ? theme.palette.error.main : theme.palette.primary.main,
          '&:hover': {
            backgroundColor: theme.palette.action.hover,
          },
        }}
      >
        {isRecording ? <MicOffIcon /> : <MicIcon />}
      </IconButton>
    </Tooltip>
  );
};

export default VoiceInput;
