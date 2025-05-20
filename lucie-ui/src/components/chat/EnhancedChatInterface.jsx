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
import LucieAvatar from "../assistant/LucieAvatar";
import ProactivePanel from "../assistant/ProactivePanel";
import axios from "axios";

/**
 * Interface principale de chat pour Lucie
 * Version améliorée avec avatar réactif et style Jarvis
 */
const EnhancedChatInterface = () => {
  const theme = useTheme();
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [avatarState, setAvatarState] = useState("neutral");
  const [showAvatar, setShowAvatar] = useState(true);
  const [showProactive, setShowProactive] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const messagesEndRef = useRef(null);
  const API_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

  // Faire défiler vers le bas quand de nouveaux messages sont ajoutés
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Générer quelques suggestions basiques (à terme serait basé sur l'analyse du contexte)
  useEffect(() => {
    const defaultSuggestions = [
      "Qu'est-ce que tu peux faire?",
      "Comment fonctionne ton système d'agents?",
      "Aide-moi à comprendre comment utiliser Lucie",
    ];

    setSuggestions(defaultSuggestions);

    // À terme, ce serait une API call pour récupérer des suggestions contextuelles
    // Si les messages sont vides, on montre le panneau proactif
    setShowProactive(messages.length === 0);
  }, [messages.length]);

  // Déterminer l'état de l'avatar en fonction du contexte
  const updateAvatarState = (state) => {
    setAvatarState(state);
  };

  // Traiter l'envoi d'un nouveau message
  const handleSendMessage = async (messageText) => {
    if (!messageText.trim()) return;

    // Mise à jour de l'état de l'avatar
    updateAvatarState("processing");

    // Masquer les suggestions proactives lors de l'envoi du message
    setShowProactive(false);

    // Ajouter le message utilisateur à la conversation
    const userMessage = {
      id: Date.now().toString(),
      content: messageText,
      sender: "user",
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Appel à l'API pour traiter le message
      const response = await axios.post(`${API_URL}/api/chat/message`, {
        message: messageText,
        context: {
          // Contexte pertinent, comme l'historique récent
          recentMessages: messages.slice(-5).map((m) => ({
            content: m.content,
            sender: m.sender,
          })),
        },
      });

      // Créer le message de réponse de Lucie
      const lucieMessage = {
        id: response.data.messageId || Date.now().toString() + 1,
        content: response.data.response,
        sender: "lucie",
        timestamp: response.data.timestamp || new Date().toISOString(),
        featureStatus: response.data.featureStatus || null,
        intent: response.data.intent || "unknown",
        confidence: response.data.confidence || 1.0,
      };

      // Mise à jour de l'avatar pendant la "réponse"
      updateAvatarState("speaking");

      // Ajouter la réponse avec un court délai pour l'effet visuel
      setTimeout(() => {
        setMessages((prev) => [...prev, lucieMessage]);
        setIsLoading(false);

        // Revenir à l'état neutre après la réponse
        setTimeout(() => {
          updateAvatarState("neutral");
        }, 1000);
      }, 500);
    } catch (error) {
      console.error("Erreur lors de l'envoi du message:", error);

      // Message d'erreur en cas d'échec
      const errorMessage = {
        id: Date.now().toString() + 1,
        content:
          "Je suis désolée, j'ai rencontré une erreur lors du traitement de votre message. Veuillez réessayer.",
        sender: "lucie",
        timestamp: new Date().toISOString(),
        isError: true,
      };

      setMessages((prev) => [...prev, errorMessage]);
      setIsLoading(false);
      updateAvatarState("error");

      // Revenir à l'état neutre après l'erreur
      setTimeout(() => {
        updateAvatarState("neutral");
      }, 2000);
    }
  };

  // Gérer l'utilisation d'une suggestion
  const handleSuggestionClick = (suggestion) => {
    handleSendMessage(suggestion);
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
          <LucieAvatar state={avatarState} size={showAvatar ? 200 : 0} />
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
    </Box>
  );
};

export default EnhancedChatInterface;
