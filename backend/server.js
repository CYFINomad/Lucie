require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const lucieCore = require('./core/LucieCore');
const logger = require('./utils/logger');

// Routes API
const chatRoutes = require('./api/routes/chatRoutes');

// Initialisation de l'application Express
const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(helmet());
app.use(morgan('dev'));
app.use(express.json());

// Initialisation du noyau Lucie
(async () => {
  try {
    await lucieCore.initialize();
    logger.info('Noyau Lucie initialisé avec succès');
  } catch (error) {
    logger.error('Erreur lors de l\'initialisation du noyau Lucie', { error: error.message });
    process.exit(1);
  }
})();

// Routes de base
app.get('/', (req, res) => {
  res.json({ message: 'API Lucie - Backend Node.js fonctionnel', version: '0.1.0' });
});

// Route de santé
app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    initialized: lucieCore.initialized,
    version: '0.1.0'
  });
});

// Routes API
app.use('/api/chat', chatRoutes);

// Gestionnaire d'erreurs global
app.use((err, req, res, next) => {
  logger.error('Erreur non gérée', { 
    error: err.message,
    stack: err.stack,
    path: req.path 
  });
  res.status(500).json({ error: 'Une erreur est survenue sur le serveur' });
});

// Démarrage du serveur
app.listen(PORT, () => {
  logger.info(`Serveur Lucie démarré sur le port ${PORT}`);
  console.log(`Serveur Lucie démarré sur le port ${PORT}`);
});