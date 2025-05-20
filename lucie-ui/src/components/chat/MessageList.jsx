import React from "react";
import {
  Box,
  Paper,
  Typography,
  Chip,
  Avatar,
  useTheme,
  Tooltip,
  Fade,
} from "@mui/material";
import { formatDistanceToNow } from "date-fns";
import { fr } from "date-fns/locale";
import PersonOutlineIcon from "@mui/icons-material/PersonOutline";
import SmartToyOutlinedIcon from "@mui/icons-material/SmartToyOutlined";
import MarkdownRenderer from "../common/MarkdownRenderer";

/**
 * Liste des messages de la conversation avec style amélioré
 * Supporte le markdown et les métadonnées enrichies
 * @param {Object} props - Propriétés du composant
 * @param {Array} props.messages - Liste des messages à afficher
 */
const MessageList = ({ messages }) => {
  const theme = useTheme();

  // Formater la date relative
  const formatMessageTime = (timestamp) => {
    try {
      const date = new Date(timestamp);
      return formatDistanceToNow(date, { addSuffix: true, locale: fr });
    } catch (e) {
      return "";
    }
  };

  // Vérifier si un message contient du code
  const containsCode = (content) => {
    return content.includes("```") || content.includes("`");
  };

  return (
    <Box sx={{ width: "100%" }}>
      {messages.map((message, index) => {
        const isUser = message.sender === "user";
        const isError = message.isError;
        const hasCode = !isUser && containsCode(message.content);

        return (
          <Fade
            key={message.id || index}
            in={true}
            timeout={500}
            style={{ transitionDelay: `${(index % 5) * 50}ms` }}
          >
            <Box
              sx={{
                display: "flex",
                justifyContent: isUser ? "flex-end" : "flex-start",
                mb: 3,
                maxWidth: "100%",
              }}
            >
              {/* Avatar pour les messages de Lucie */}
              {!isUser && (
                <Avatar
                  sx={{
                    bgcolor: isError
                      ? theme.palette.error.main
                      : theme.palette.secondary.main,
                    width: 36,
                    height: 36,
                    mr: 1.5,
                    mt: 0.5,
                    boxShadow: `0 0 10px ${
                      isError
                        ? theme.palette.error.main
                        : theme.palette.secondary.main
                    }50`,
                  }}
                >
                  <SmartToyOutlinedIcon />
                </Avatar>
              )}

              <Box
                sx={{
                  maxWidth: { xs: "80%", sm: "75%", md: "65%" },
                  display: "flex",
                  flexDirection: "column",
                  alignItems: isUser ? "flex-end" : "flex-start",
                }}
              >
                {/* En-tête du message avec le nom et l'heure */}
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    mb: 0.5,
                    ml: isUser ? 0 : 0.5,
                    mr: isUser ? 0.5 : 0,
                  }}
                >
                  {/* Avatar pour les messages utilisateur (seulement dans l'en-tête) */}
                  {isUser && (
                    <Avatar
                      sx={{
                        bgcolor: theme.palette.primary.main,
                        width: 24,
                        height: 24,
                        mr: 1,
                        boxShadow: `0 0 10px ${theme.palette.primary.main}50`,
                      }}
                    >
                      <PersonOutlineIcon sx={{ fontSize: 16 }} />
                    </Avatar>
                  )}

                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ fontWeight: 500 }}
                  >
                    {isUser ? "Vous" : "Lucie"}
                  </Typography>

                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ mx: 0.5, opacity: 0.7 }}
                  >
                    •
                  </Typography>

                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ opacity: 0.7 }}
                  >
                    {formatMessageTime(message.timestamp)}
                  </Typography>
                </Box>

                {/* Contenu du message */}
                <Paper
                  elevation={2}
                  sx={{
                    p: hasCode ? 1.5 : 2,
                    borderRadius: 2,
                    backgroundColor: isUser
                      ? theme.palette.primary.dark
                      : isError
                      ? theme.palette.error.dark
                      : theme.palette.secondary.dark,
                    color: isUser
                      ? theme.palette.primary.contrastText
                      : isError
                      ? theme.palette.error.contrastText
                      : theme.palette.secondary.contrastText,
                    wordBreak: "break-word",
                    width: "auto",
                    maxWidth: "100%",
                    boxShadow: `0 3px 10px ${
                      isUser
                        ? theme.palette.primary.dark
                        : isError
                        ? theme.palette.error.dark
                        : theme.palette.secondary.dark
                    }40`,
                    border: isUser
                      ? `1px solid ${theme.palette.primary.main}50`
                      : isError
                      ? `1px solid ${theme.palette.error.main}50`
                      : `1px solid ${theme.palette.secondary.main}50`,
                    position: "relative",
                    "&::before": {
                      content: '""',
                      position: "absolute",
                      top: 15,
                      [isUser ? "right" : "left"]: -8,
                      width: 15,
                      height: 15,
                      backgroundColor: isUser
                        ? theme.palette.primary.dark
                        : isError
                        ? theme.palette.error.dark
                        : theme.palette.secondary.dark,
                      transform: "rotate(45deg)",
                      zIndex: -1,
                      borderTop: isUser
                        ? `1px solid ${theme.palette.primary.main}50`
                        : isError
                        ? `1px solid ${theme.palette.error.main}50`
                        : `1px solid ${theme.palette.secondary.main}50`,
                      borderLeft: isUser
                        ? "none"
                        : `1px solid ${
                            isError
                              ? theme.palette.error.main
                              : theme.palette.secondary.main
                          }50`,
                      borderRight: isUser
                        ? `1px solid ${theme.palette.primary.main}50`
                        : "none",
                      display:
                        isUser &&
                        index > 0 &&
                        messages[index - 1].sender === "user"
                          ? "none"
                          : "block",
                    },
                  }}
                >
                  {/* Rendu du contenu avec support du markdown */}
                  {!isUser && hasCode ? (
                    <MarkdownRenderer content={message.content} />
                  ) : (
                    <Typography variant="body1">{message.content}</Typography>
                  )}
                </Paper>

                {/* Fonctionnalités/statut supplémentaires */}
                {message.featureStatus && (
                  <Box sx={{ mt: 1, ml: 1 }}>
                    <Chip
                      label={`Fonctionnalité: ${message.featureStatus.requested} (non implémentée)`}
                      size="small"
                      color="info"
                      variant="outlined"
                      sx={{
                        borderRadius: 1.5,
                        "& .MuiChip-label": {
                          px: 1,
                        },
                      }}
                    />
                  </Box>
                )}

                {/* Affichage de l'intention détectée (si disponible) */}
                {!isUser &&
                  message.intent &&
                  message.confidence &&
                  message.confidence > 0.7 && (
                    <Tooltip title="Intention détectée par Lucie">
                      <Chip
                        label={`${message.intent} (${Math.round(
                          message.confidence * 100
                        )}%)`}
                        size="small"
                        color="secondary"
                        variant="outlined"
                        sx={{
                          mt: 1,
                          ml: 1,
                          fontSize: "0.7rem",
                          height: 20,
                          opacity: 0.7,
                          borderRadius: 1,
                          "& .MuiChip-label": {
                            px: 1,
                          },
                        }}
                      />
                    </Tooltip>
                  )}
              </Box>

              {/* Avatar pour les messages utilisateur (à droite) */}
              {isUser && (
                <Avatar
                  sx={{
                    bgcolor: theme.palette.primary.main,
                    width: 36,
                    height: 36,
                    ml: 1.5,
                    mt: 0.5,
                    boxShadow: `0 0 10px ${theme.palette.primary.main}50`,
                  }}
                >
                  <PersonOutlineIcon />
                </Avatar>
              )}
            </Box>
          </Fade>
        );
      })}
    </Box>
  );
};

export default MessageList;
