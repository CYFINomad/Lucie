import React, { useState, useRef, useEffect } from "react";
import {
  Box,
  Paper,
  Typography,
  Fade,
  useTheme,
  IconButton,
  Tooltip,
  Collapse,
  Grow,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import SettingsIcon from "@mui/icons-material/Settings";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";
import ResponseDisplay from "./ResponseDisplay";
import LucieAvatarEnhanced from "../assistant/LucieAvatarEnhanced";
import ProactivePanel from "../assistant/ProactivePanel";
import useChatState from "../../hooks/useChatState";

/**
 * Interface principale de chat pour Lucie
 * Version améliorée avec avatar réactif et style Jarvis
 */
const EnhancedChatInterface = () => {
  const theme = useTheme();
  const {
    messages,
    isLoading,
    error,
    suggestions,
    sendMessage,
    loadSuggestions,
  } = useChatState();

  const [avatarState, setAvatarState] = useState("neutral");
  const [showAvatar, setShowAvatar] = useState(true);
  const [showProactive, setShowProactive] = useState(true);
  const messagesEndRef = useRef(null);

  // Faire défiler vers le bas quand de nouveaux messages sont ajoutés
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Mettre à jour les suggestions et l'affichage du panneau proactif
  useEffect(() => {
    // Si les messages sont vides, on montre le panneau proactif
    setShowProactive(messages.length === 0 && !isLoading);
  }, [messages.length, isLoading]);

  // Mettre à jour l'état de l'avatar en fonction du contexte
  useEffect(() => {
    if (isLoading) {
      setAvatarState("processing");
    } else if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.sender === "lucie") {
        if (lastMessage.isError) {
          setAvatarState("error");
          // Revenir à l'état neutre après 2 secondes
          const timer = setTimeout(() => {
            setAvatarState("neutral");
          }, 2000);
          return () => clearTimeout(timer);
        } else {
          setAvatarState("speaking");
          // Revenir à l'état neutre après 1 seconde
          const timer = setTimeout(() => {
            setAvatarState("neutral");
          }, 1000);
          return () => clearTimeout(timer);
        }
      }
    }
  }, [isLoading, messages]);

  // Traiter l'envoi d'un nouveau message
  const handleSendMessage = async (messageText) => {
    if (!messageText.trim()) return;

    // Mise à jour de l'avatar pendant le traitement
    setAvatarState("processing");

    // Masquer les suggestions proactives lors de l'envoi du message
    setShowProactive(false);

    try {
      // Envoyer le message via le hook useChatState
      await sendMessage(messageText);

      // Avatar passe en mode "speaking" après l'envoi du message
      setAvatarState("speaking");

      // Puis revient en mode neutre après un court délai
      setTimeout(() => {
        setAvatarState("neutral");
      }, 1000);
    } catch (error) {
      console.error("Erreur lors de l'envoi du message:", error);
      setAvatarState("error");

      // Revenir à l'état neutre après l'erreur
      setTimeout(() => {
        setAvatarState("neutral");
      }, 2000);
    }
  };

  // Gérer l'utilisation d'une suggestion
  const handleSuggestionClick = (suggestion) => {
    handleSendMessage(suggestion);
  };

  // Mise à jour de l'état de l'avatar par l'entrée vocale
  const updateAvatarState = (state) => {
    setAvatarState(state);
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
        p: { xs: 1, sm: 2 },
        backgroundColor: theme.palette.background.default,
        position: "relative",
      }}
    >
      {/* En-tête de l'interface */}
      <Paper
        elevation={2}
        sx={{
          p: 2,
          mb: 2,
          borderRadius: 2,
          backgroundColor: theme.palette.background.paper,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography variant="h6" color="secondary">
          Conversation avec Lucie
        </Typography>

        <Box display="flex" alignItems="center">
          <Tooltip title="Paramètres d'interaction">
            <IconButton size="small" color="secondary" sx={{ ml: 1 }}>
              <SettingsIcon />
            </IconButton>
          </Tooltip>

          <Tooltip
            title={showAvatar ? "Masquer l'avatar" : "Afficher l'avatar"}
          >
            <IconButton
              size="small"
              color="secondary"
              sx={{ ml: 1 }}
              onClick={() => setShowAvatar(!showAvatar)}
            >
              {showAvatar ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>

      {/* Zone de l'avatar (collapsible) */}
      <Collapse in={showAvatar} timeout={500}>
        <Box
          sx={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            mb: 2,
            height: { xs: 150, sm: 200, md: 250 },
            transition: "height 0.5s ease",
          }}
        >
          {/* Utiliser l'avatar amélioré */}
          <LucieAvatarEnhanced
            state={avatarState}
            size={showAvatar ? 200 : 0}
          />
        </Box>
      </Collapse>

      {/* Zone des messages (principale) */}
      <Paper
        elevation={2}
        sx={{
          flexGrow: 1,
          mb: 2,
          p: 2,
          borderRadius: 2,
          backgroundColor: theme.palette.background.paper,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          position: "relative",
        }}
      >
        {messages.length === 0 ? (
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              height: "100%",
              textAlign: "center",
              p: 3,
            }}
          >
            <Typography color="text.secondary">
              Je suis Lucie, votre assistant IA personnel.
              <br />
              Comment puis-je vous aider aujourd'hui ?
            </Typography>
          </Box>
        ) : (
          <MessageList messages={messages} />
        )}
        <div ref={messagesEndRef} />

        {/* Panneau de suggestions proactives */}
        <Grow in={showProactive && !isLoading}>
          <Box
            sx={{ position: "absolute", bottom: 20, left: 0, width: "100%" }}
          >
            <ProactivePanel
              suggestions={suggestions}
              onSuggestionClick={handleSuggestionClick}
            />
          </Box>
        </Grow>
      </Paper>

      {/* Zone de saisie */}
      <MessageInput
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        avatarState={avatarState}
        setAvatarState={updateAvatarState}
      />

      {/* Affichage de l'état de réponse en cours */}
      <Fade in={isLoading}>
        <Box>
          <ResponseDisplay />
        </Box>
      </Fade>

      {/* Message d'erreur si présent */}
      {error && (
        <Fade in={!!error}>
          <Paper
            elevation={3}
            sx={{
              p: 2,
              mt: 2,
              borderRadius: 2,
              backgroundColor: theme.palette.error.dark,
              color: theme.palette.error.contrastText,
              boxShadow: `0 0 10px ${theme.palette.error.main}`,
            }}
          >
            <Typography variant="body2">{error}</Typography>
          </Paper>
        </Fade>
      )}
    </Box>
  );
};

export default EnhancedChatInterface;
