const express = require('express');
const router = express.Router();

// Import des routes spécifiques aux domaines
const conversationRoutes = require('../../domains/conversation/routes/messageRoutes');

// Routes pour le chat - point d'entrée pour les sous-routes
router.use('/message', conversationRoutes);

// Historique des conversations
router.get('/history', (req, res) => {
  // TODO: Implémenter la récupération de l'historique des conversations
  res.json({ 
    message: 'Historique des conversations',
    info: 'Cette fonctionnalité sera implémentée dans une version future'
  });
});

// Statut du système de chat
router.get('/status', (req, res) => {
  res.json({
    status: 'online',
    latency: '25ms',
    availableFeatures: ['basic-conversation'],
    timestamp: new Date().toISOString()
  });
});

module.exports = router;