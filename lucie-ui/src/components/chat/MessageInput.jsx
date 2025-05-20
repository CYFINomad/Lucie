import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  TextField,
  Button,
  IconButton,
  CircularProgress,
  Paper,
  Tooltip,
  useTheme,
  Fade,
  Chip,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import MicIcon from "@mui/icons-material/Mic";
import MicNoneIcon from "@mui/icons-material/MicNone";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import GraphicEqIcon from "@mui/icons-material/GraphicEq";

/**
 * Composant de saisie des messages avec reconnaissance vocale
 * Interface stylisée inspirée de Jarvis
 * @param {Object} props - Propriétés du composant
 * @param {Function} props.onSendMessage - Fonction à appeler lors de l'envoi d'un message
 * @param {boolean} props.isLoading - Indique si une réponse est en cours de chargement
 * @param {string} props.avatarState - État actuel de l'avatar
 * @param {Function} props.setAvatarState - Fonction pour mettre à jour l'état de l'avatar
 */
const MessageInput = ({
  onSendMessage,
  isLoading,
  avatarState,
  setAvatarState,
}) => {
  const theme = useTheme();
  const [message, setMessage] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isVoiceAvailable, setIsVoiceAvailable] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [recognitionEnabled, setRecognitionEnabled] = useState(false);
  const recognitionRef = useRef(null);
  const recordingTimerRef = useRef(null);
  const inputRef = useRef(null);

  // Vérifier si la reconnaissance vocale est disponible dans le navigateur
  useEffect(() => {
    const checkVoiceSupport = () => {
      if (
        "webkitSpeechRecognition" in window ||
        "SpeechRecognition" in window
      ) {
        setIsVoiceAvailable(true);

        // Simuler une fonctionnalité disponible pour la démo
        // Dans une implémentation réelle, on vérifierait les permissions et disponibilité API
        setRecognitionEnabled(true);

        // Initialiser la reconnaissance vocale
        const SpeechRecognition =
          window.SpeechRecognition || window.webkitSpeechRecognition;
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = true;
        recognitionRef.current.interimResults = true;
        recognitionRef.current.lang = "fr-FR"; // Langue par défaut

        recognitionRef.current.onresult = (event) => {
          const transcript = Array.from(event.results)
            .map((result) => result[0])
            .map((result) => result.transcript)
            .join("");

          setMessage(transcript);
        };

        recognitionRef.current.onerror = (event) => {
          console.error("Erreur de reconnaissance vocale:", event.error);
          stopRecording();
        };

        recognitionRef.current.onend = () => {
          stopRecording();
        };
      }
    };

    checkVoiceSupport();

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    };
  }, []);

  // Gérer l'envoi du message
  const handleSend = () => {
    if (message.trim() && !isLoading) {
      onSendMessage(message);
      setMessage("");

      // Focus sur l'input après envoi
      setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
    }
  };

  // Gérer la touche Entrée
  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Démarrer l'enregistrement vocal
  const startRecording = () => {
    if (!recognitionRef.current || !recognitionEnabled) return;

    try {
      // Réinitialiser le texte du message
      setMessage("");

      // Démarrer la reconnaissance vocale
      recognitionRef.current.start();
      setIsRecording(true);

      // Mettre à jour l'état de l'avatar
      if (setAvatarState) {
        setAvatarState("listening");
      }

      // Démarrer le timer
      setRecordingDuration(0);
      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 1);
      }, 1000);
    } catch (error) {
      console.error(
        "Erreur lors du démarrage de la reconnaissance vocale:",
        error
      );
    }
  };

  // Arrêter l'enregistrement vocal
  const stopRecording = () => {
    if (!recognitionRef.current) return;

    try {
      recognitionRef.current.stop();
    } catch (error) {
      console.error(
        "Erreur lors de l'arrêt de la reconnaissance vocale:",
        error
      );
    }

    setIsRecording(false);

    // Arrêter le timer
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }

    // Réinitialiser l'état de l'avatar
    if (setAvatarState && avatarState === "listening") {
      setAvatarState("neutral");
    }
  };

  // Formater la durée d'enregistrement (mm:ss)
  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs
      .toString()
      .padStart(2, "0")}`;
  };

  return (
    <Paper
      elevation={3}
      sx={{
        p: 2,
        borderRadius: 3,
        backgroundColor: theme.palette.background.paper,
        border: isRecording ? `1px solid ${theme.palette.info.main}` : "none",
        boxShadow: isRecording
          ? `0 0 15px ${theme.palette.info.main}40`
          : `0 4px 20px rgba(0, 0, 0, 0.5)`,
        transition: "all 0.3s ease",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "flex-end" }}>
        {/* Entrée de texte */}
        <TextField
          fullWidth
          inputRef={inputRef}
          variant="outlined"
          placeholder="Envoyez un message à Lucie..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading || isRecording}
          multiline
          maxRows={4}
          sx={{
            mr: 1,
            "& .MuiOutlinedInput-root": {
              borderRadius: 2,
              backgroundColor: isRecording
                ? "rgba(106, 53, 224, 0.05)"
                : "transparent",
              transition: "all 0.3s ease",
            },
            "& .MuiOutlinedInput-input": {
              color: isRecording ? theme.palette.info.main : "inherit",
            },
          }}
          InputProps={{
            endAdornment: isRecording && (
              <Box display="flex" alignItems="center" mr={1}>
                <GraphicEqIcon
                  color="info"
                  fontSize="small"
                  sx={{
                    animation: "pulse 1s infinite",
                    "@keyframes pulse": {
                      "0%": { opacity: 0.5 },
                      "50%": { opacity: 1 },
                      "100%": { opacity: 0.5 },
                    },
                  }}
                />
                <Fade in={true}>
                  <Chip
                    label={formatDuration(recordingDuration)}
                    size="small"
                    color="info"
                    variant="outlined"
                    sx={{ ml: 1 }}
                  />
                </Fade>
              </Box>
            ),
          }}
        />

        {/* Bouton de reconnaissance vocale */}
        {isVoiceAvailable && (
          <Tooltip
            title={
              isRecording ? "Arrêter l'enregistrement" : "Reconnaissance vocale"
            }
          >
            <IconButton
              color={isRecording ? "info" : "primary"}
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isLoading || !recognitionEnabled}
              sx={{
                mr: 1,
                backgroundColor: isRecording
                  ? "rgba(106, 53, 224, 0.1)"
                  : "transparent",
                boxShadow: isRecording
                  ? `0 0 10px ${theme.palette.info.main}40`
                  : "none",
                transition: "all 0.3s ease",
                animation: isRecording ? "pulse-record 1.5s infinite" : "none",
                "@keyframes pulse-record": {
                  "0%": { transform: "scale(1)" },
                  "50%": { transform: "scale(1.1)" },
                  "100%": { transform: "scale(1)" },
                },
              }}
            >
              {isRecording ? <MicIcon /> : <MicNoneIcon />}
            </IconButton>
          </Tooltip>
        )}

        {/* Bouton pour effacer le texte */}
        {message.length > 0 && !isLoading && !isRecording && (
          <Tooltip title="Effacer le message">
            <IconButton
              onClick={() => setMessage("")}
              color="primary"
              sx={{ mr: 1 }}
            >
              <DeleteOutlineIcon />
            </IconButton>
          </Tooltip>
        )}

        {/* Bouton d'envoi */}
        <Button
          variant="contained"
          color="secondary"
          endIcon={
            isLoading ? (
              <CircularProgress size={24} color="inherit" />
            ) : (
              <SendIcon />
            )
          }
          onClick={handleSend}
          disabled={isLoading || !message.trim() || isRecording}
          sx={{
            borderRadius: 3,
            px: 3,
            py: 1.3,
            height: 48,
            textTransform: "none",
            fontWeight: 500,
            boxShadow: "0 4px 10px rgba(140, 94, 255, 0.3)",
            "&:hover": {
              boxShadow: "0 6px 15px rgba(140, 94, 255, 0.4)",
            },
          }}
        >
          Envoyer
        </Button>
      </Box>

      {/* Infos sur les capacités */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-start",
          mt: 1.5,
        }}
      >
        <InfoOutlinedIcon
          fontSize="small"
          color="action"
          sx={{ mr: 0.5, opacity: 0.7 }}
        />
        <Tooltip title="Lucie est en phase alpha et ses capacités sont limitées">
          <Box
            component="span"
            sx={{
              fontSize: "0.75rem",
              color: theme.palette.text.secondary,
              opacity: 0.7,
            }}
          >
            Lucie est en phase alpha (v0.1.0)
          </Box>
        </Tooltip>
      </Box>
    </Paper>
  );
};

export default MessageInput;
