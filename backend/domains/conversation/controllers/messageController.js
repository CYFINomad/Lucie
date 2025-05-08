const axios = require('axios');
const config = require('../../../utils/config');
const logger = require('../../../utils/logger');
const featureService = require('../services/featureService');

/**
 * Traite un message envoyé par l'utilisateur
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
async function processMessage(req, res) {
  try {
    const { message, context = {} } = req.body;
    
    if (!message || typeof message !== 'string') {
      return res.status(400).json({
        error: 'Message invalide',
        details: 'Le message doit être une chaîne de caractères non vide'
      });
    }
    
    logger.info('Traitement d\'un message', { messageLength: message.length });
    
    // Analyse du message pour détecter les demandes de fonctionnalités
    const featureRequest = featureService.analyzeForFeatureRequest(message);
    
    if (featureRequest) {
      const notImplementedMessage = featureService.generateNotImplementedMessage(featureRequest.feature);
      
      if (notImplementedMessage) {
        // La fonctionnalité n'est pas implémentée
        logger.info('Fonctionnalité non implémentée détectée', { feature: featureRequest.feature });
        featureService.logFeatureRequest(featureRequest.feature, message);
        
        return res.json({
          response: notImplementedMessage,
          timestamp: new Date().toISOString(),
          featureStatus: {
            requested: featureRequest.feature,
            implemented: false
          }
        });
      }
    }
    
    // Pour les fonctionnalités implémentées ou les messages généraux,
    // on transmet au backend Python
    logger.debug('Transfert du message au backend Python');
    try {
      const pythonResponse = await axios.post(`${config.pythonApi.url}/process-message`, {
        message,
        context
      }, {
        timeout: config.pythonApi.timeout
      });
      
      // Relayer la réponse
      res.json({
        response: pythonResponse.data.response,
        timestamp: pythonResponse.data.timestamp,
        messageId: pythonResponse.data.messageId || Date.now().toString(),
        context: pythonResponse.data.context || {}
      });
    } catch (pythonError) {
      logger.error('Erreur lors de la communication avec le backend Python', {
        error: pythonError.message,
        code: pythonError.code
      });
      
      // Fallback - réponse basique en cas d'erreur avec le backend Python
      res.json({
        response: "Je suis désolée, je rencontre des difficultés techniques pour traiter votre message. Nos équipes travaillent à résoudre ce problème.",
        timestamp: new Date().toISOString(),
        error: true
      });
    }
  } catch (error) {
    logger.error('Erreur lors du traitement du message', { error: error.message });
    
    res.status(500).json({
      response: "Je suis désolée, une erreur est survenue lors du traitement de votre message.",
      timestamp: new Date().toISOString(),
      error: true
    });
  }
}

/**
 * Version streaming du traitement des messages
 * Pour réponses progressives en temps réel
 * @param {Object} req - Requête Express
 * @param {Object} res - Réponse Express
 */
async function streamMessage(req, res) {
  try {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    
    const { message, context = {} } = req.body;
    
    if (!message || typeof message !== 'string') {
      res.write(`data: ${JSON.stringify({
        error: 'Message invalide',
        details: 'Le message doit être une chaîne de caractères non vide',
        done: true
      })}\n\n`);
      return res.end();
    }
    
    // Vérifier les fonctionnalités non implémentées
    const featureRequest = featureService.analyzeForFeatureRequest(message);
    
    if (featureRequest) {
      const notImplementedMessage = featureService.generateNotImplementedMessage(featureRequest.feature);
      
      if (notImplementedMessage) {
        featureService.logFeatureRequest(featureRequest.feature, message);
        
        res.write(`data: ${JSON.stringify({
          response: notImplementedMessage,
          timestamp: new Date().toISOString(),
          featureStatus: {
            requested: featureRequest.feature,
            implemented: false
          },
          done: true
        })}\n\n`);
        
        return res.end();
      }
    }
    
    // Pour le moment, en mode streaming, nous simulons une réponse progressive
    // Dans une implémentation réelle, nous utiliserions un serveur SSE Python ou WebSockets
    
    // Envoi d'un accusé de réception
    res.write(`data: ${JSON.stringify({
      type: 'ack',
      timestamp: new Date().toISOString()
    })}\n\n`);
    
    // Simulation d'une réponse progressive
    setTimeout(() => {
      res.write(`data: ${JSON.stringify({
        type: 'token',
        response: "Je suis en train ",
        timestamp: new Date().toISOString()
      })}\n\n`);
    }, 300);
    
    setTimeout(() => {
      res.write(`data: ${JSON.stringify({
        type: 'token',
        response: "de traiter votre message. ",
        timestamp: new Date().toISOString()
      })}\n\n`);
    }, 600);
    
    setTimeout(() => {
      res.write(`data: ${JSON.stringify({
        type: 'token',
        response: "Cette fonctionnalité de streaming sera améliorée dans les prochaines versions.",
        timestamp: new Date().toISOString()
      })}\n\n`);
    }, 900);
    
    // Message final
    setTimeout(() => {
      res.write(`data: ${JSON.stringify({
        type: 'end',
        messageId: Date.now().toString(),
        done: true
      })}\n\n`);
      
      res.end();
    }, 1200);
  } catch (error) {
    logger.error('Erreur lors du streaming du message', { error: error.message });
    
    res.write(`data: ${JSON.stringify({
      error: true,
      response: "Je suis désolée, une erreur est survenue lors du traitement de votre message.",
      timestamp: new Date().toISOString(),
      done: true
    })}\n\n`);
    
    res.end();
  }
}

module.exports = {
  processMessage,
  streamMessage
};