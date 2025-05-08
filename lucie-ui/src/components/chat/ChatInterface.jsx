import React, { useState, useRef, useEffect } from 'react';
import { Box, Paper, Typography, useTheme } from '@mui/material';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import ResponseDisplay from './ResponseDisplay';
import axios from 'axios';

/**
 * Interface principale de chat pour Lucie
 * Gère l'affichage et l'envoi des messages
 */
const ChatInterface = () => {
  const theme = useTheme();
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

  // Faire défiler vers le bas quand de nouveaux messages sont ajoutés
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Traiter l'envoi d'un nouveau message
  const handleSendMessage = async (messageText) => {
    if (!messageText.trim()) return;

    // Ajouter le message utilisateur à la conversation
    const userMessage = {
      id: Date.now().toString(),
      content: messageText,
      sender: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Appel à l'API pour traiter le message
      const response = await axios.post(`${API_URL}/api/chat/message`, {
        message: messageText,
        context: {
          // Contexte pertinent, comme l'historique récent
          recentMessages: messages.slice(-5).map(m => ({ 
            content: m.content, 
            sender: m.sender 
          }))
        }
      });

      // Créer le message de réponse de Lucie
      const lucieMessage = {
        id: response.data.messageId || Date.now().toString() + 1,
        content: response.data.response,
        sender: 'lucie',
        timestamp: response.data.timestamp || new Date().toISOString(),
        featureStatus: response.data.featureStatus || null
      };

      setMessages(prev => [...prev, lucieMessage]);
    } catch (error) {
      console.error('Erreur lors de l\'envoi du message:', error);
      
      // Message d'erreur en cas d'échec
      const errorMessage = {
        id: Date.now().toString() + 1,
        content: "Je suis désolée, j'ai rencontré une erreur lors du traitement de votre message. Veuillez réessayer.",
        sender: 'lucie',
        timestamp: new Date().toISOString(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        width: '100%',
        p: { xs: 1, sm: 2 },
        backgroundColor: theme.palette.background.default
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
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <Typography variant="h6" color="secondary">
          Conversation avec Lucie
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {messages.length > 0 ? `${messages.length} messages` : 'Nouvelle conversation'}
        </Typography>
      </Paper>

      {/* Zone des messages */}
      <Paper
        elevation={2}
        sx={{
          flexGrow: 1,
          mb: 2,
          p: 2,
          borderRadius: 2,
          backgroundColor: theme.palette.background.paper,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {messages.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              textAlign: 'center',
              p: 3
            }}
          >
            <Typography color="text.secondary">
              Je suis Lucie, votre assistant IA personnel.<br />
              Comment puis-je vous aider aujourd'hui ?
            </Typography>
          </Box>
        ) : (
          <MessageList messages={messages} />
        )}
        <div ref={messagesEndRef} />
      </Paper>

      {/* Zone de saisie */}
      <MessageInput 
        onSendMessage={handleSendMessage} 
        isLoading={isLoading} 
      />

      {/* Affichage de l'état de réponse en cours */}
      {isLoading && <ResponseDisplay />}
    </Box>
  );
};

export default ChatInterface;