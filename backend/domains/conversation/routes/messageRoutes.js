const express = require('express');
const router = express.Router();
const messageController = require('../controllers/messageController');

/**
 * @route POST /api/chat/message
 * @description Traite un message envoyé par l'utilisateur
 * @access Public
 */
router.post('/', messageController.processMessage);

/**
 * @route POST /api/chat/message/stream
 * @description Version streaming du traitement des messages (pour réponses en temps réel)
 * @access Public
 */
router.post('/stream', messageController.streamMessage);

module.exports = router;