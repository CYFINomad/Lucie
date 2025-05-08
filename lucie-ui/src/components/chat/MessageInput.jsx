import React, { useState } from 'react';
import { 
  Box, 
  TextField, 
  Button, 
  IconButton, 
  CircularProgress, 
  Paper,
  Tooltip,
  useTheme
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import MicIcon from '@mui/icons-material/Mic';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';

/**
 * Composant de saisie des messages
 * @param {Object} props - Propriétés du composant
 * @param {Function} props.onSendMessage - Fonction à appeler lors de l'envoi d'un message
 * @param {boolean} props.isLoading - Indique si une réponse est en cours de chargement
 */
const MessageInput = ({ onSendMessage, isLoading }) => {
  const theme = useTheme();
  const [message, setMessage] = useState('');
  const [isVoiceAvailable, setIsVoiceAvailable] = useState(false);

  // Vérifier si la reconnaissance vocale est disponible dans le navigateur
  React.useEffect(() => {
    const checkVoiceSupport = () => {
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        setIsVoiceAvailable(true);
      }
    };
    
    checkVoiceSupport();
  }, []);

  // Gérer l'envoi du message
  const handleSend = () => {
    if (message.trim() && !isLoading) {
      onSendMessage(message);
      setMessage('');
    }
  };

  // Gérer la touche Entrée
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Gérer le clic sur le bouton de saisie vocale
  const handleVoiceClick = () => {
    if (!isVoiceAvailable) {
      alert('La reconnaissance vocale n\'est pas prise en charge par votre navigateur.');
      return;
    }
    
    // Afficher une notification pour la fonctionnalité non implémentée
    const placeholderMessage = "La fonctionnalité de reconnaissance vocale sera disponible dans une prochaine version.";
    onSendMessage("Activer la reconnaissance vocale");
  };

  return (
    <Paper
      elevation={2}
      sx={{
        p: 2,
        borderRadius: 2,
        backgroundColor: theme.palette.background.paper
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-end' }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Envoyez un message à Lucie..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isLoading}
          multiline
          maxRows={4}
          sx={{ 
            mr: 1,
            '& .MuiOutlinedInput-root': {
              borderRadius: 2
            }
          }}
        />
        
        {/* Bouton de reconnaissance vocale */}
        <Tooltip title="Reconnaissance vocale (bientôt disponible)">
          <IconButton 
            color="primary"
            onClick={handleVoiceClick}
            disabled={isLoading}
            sx={{ 
              mr: 1,
              color: theme.palette.primary.main
            }}
          >
            <MicIcon />
          </IconButton>
        </Tooltip>
        
        {/* Bouton d'envoi */}
        <Button
          variant="contained"
          color="secondary"
          endIcon={isLoading ? <CircularProgress size={24} color="inherit" /> : <SendIcon />}
          onClick={handleSend}
          disabled={isLoading || !message.trim()}
          sx={{ 
            borderRadius: 2,
            px: 3,
            py: 1,
            height: 40
          }}
        >
          Envoyer
        </Button>
      </Box>
      
      {/* Infos sur les capacités */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start', mt: 1 }}>
        <InfoOutlinedIcon fontSize="small" color="action" sx={{ mr: 0.5 }} />
        <Tooltip title="Lucie est en phase alpha et ses capacités sont limitées">
          <Box component="span" sx={{ fontSize: '0.75rem', color: theme.palette.text.secondary }}>
            Lucie est en phase alpha (v0.1.0)
          </Box>
        </Tooltip>
      </Box>
    </Paper>
  );
};

export default MessageInput;