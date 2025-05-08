import React from 'react';
import { Box, Paper, Typography, Chip, useTheme } from '@mui/material';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';

/**
 * Liste des messages de la conversation
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
      return '';
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      {messages.map((message, index) => (
        <Box
          key={message.id || index}
          sx={{
            display: 'flex',
            justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
            mb: 2,
            maxWidth: '100%'
          }}
        >
          <Box
            sx={{
              maxWidth: { xs: '90%', sm: '75%', md: '60%' },
              display: 'flex',
              flexDirection: 'column',
              alignItems: message.sender === 'user' ? 'flex-end' : 'flex-start'
            }}
          >
            {/* En-tête du message avec le nom et l'heure */}
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ mb: 0.5, ml: message.sender === 'user' ? 0 : 1, mr: message.sender !== 'user' ? 0 : 1 }}
            >
              {message.sender === 'user' ? 'Vous' : 'Lucie'} • {formatMessageTime(message.timestamp)}
            </Typography>

            {/* Contenu du message */}
            <Paper
              elevation={1}
              sx={{
                p: 2,
                borderRadius: 2,
                backgroundColor: message.sender === 'user'
                  ? theme.palette.primary.dark
                  : message.isError
                    ? theme.palette.error.dark
                    : theme.palette.secondary.dark,
                color: message.sender === 'user'
                  ? theme.palette.primary.contrastText
                  : message.isError
                    ? theme.palette.error.contrastText
                    : theme.palette.secondary.contrastText,
                wordBreak: 'break-word'
              }}
            >
              <Typography variant="body1">
                {message.content}
              </Typography>
            </Paper>

            {/* Affichage d'une fonctionnalité non implémentée si détectée */}
            {message.featureStatus && (
              <Box sx={{ mt: 1, ml: 1 }}>
                <Chip
                  label={`Fonctionnalité: ${message.featureStatus.requested} (non implémentée)`}
                  size="small"
                  color="info"
                  variant="outlined"
                />
              </Box>
            )}
          </Box>
        </Box>
      ))}
    </Box>
  );
};

export default MessageList;