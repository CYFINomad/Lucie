/**
 * Moteur d'apprentissage de Lucie
 * Gère l'apprentissage continu et l'adaptation aux préférences utilisateur
 */

const logger = require("../utils/logger");
const config = require("../utils/config");

class LearningEngine {
  /**
   * Crée une instance du moteur d'apprentissage
   * @param {Object} pythonBridge - Interface avec le service Python
   */
  constructor(pythonBridge) {
    this.pythonBridge = pythonBridge;
    this.ready = false;
    this.initialized = false;
    this.stats = {
      feedbackCount: 0,
      learningEvents: 0,
      lastLearningEvent: null,
      performance: {},
    };
    logger.info("LearningEngine: Instance créée");
  }

  /**
   * Initialise le moteur d'apprentissage
   * @returns {Promise<boolean>} Succès de l'initialisation
   */
  async initialize() {
    try {
      if (!this.pythonBridge) {
        throw new Error("Python bridge non disponible pour LearningEngine");
      }

      logger.info("LearningEngine: Initialisation...");

      // Vérifier la connexion au backend Python
      const status = await this.pythonBridge.checkStatus("learning");

      if (status && status.available) {
        this.ready = true;
        this.stats = status.stats || this.stats;
        this.initialized = true;
        logger.info("LearningEngine: Connexion établie", { stats: this.stats });
        return true;
      } else {
        logger.warn("LearningEngine: Service non disponible", { status });
        this.ready = false;
        return false;
      }
    } catch (error) {
      logger.error("LearningEngine: Erreur d'initialisation", {
        error: error.message,
        stack: error.stack,
      });
      this.ready = false;
      return false;
    }
  }

  /**
   * Enregistre un feedback utilisateur pour améliorer les réponses futures
   * @param {Object} feedback - Données de feedback
   * @returns {Promise<Object>} Résultat du traitement du feedback
   */
  async processFeedback(feedback) {
    if (!this.ready) {
      await this.initialize();
      if (!this.ready) {
        throw new Error("LearningEngine non disponible");
      }
    }

    try {
      logger.debug("LearningEngine: Traitement de feedback", {
        type: feedback.type,
        rating: feedback.rating,
      });

      // Appeler le backend Python pour le traitement du feedback
      const response = await this.pythonBridge.invokeMethod(
        "learning",
        "processFeedback",
        {
          feedback: {
            type: feedback.type,
            rating: feedback.rating,
            message: feedback.message,
            response: feedback.response,
            context: feedback.context || {},
            timestamp: feedback.timestamp || new Date().toISOString(),
            metadata: feedback.metadata || {},
          },
        }
      );

      // Mise à jour des statistiques
      if (response.success) {
        this.stats.feedbackCount++;
        this.stats.lastFeedbackEvent = new Date().toISOString();
      }

      logger.info("LearningEngine: Feedback traité", {
        success: response.success,
        improvements: response.improvements ? response.improvements.length : 0,
      });

      return response;
    } catch (error) {
      logger.error("LearningEngine: Erreur de traitement de feedback", {
        error: error.message,
        feedbackType: feedback.type,
      });
      throw new Error(
        `Erreur lors du traitement du feedback: ${error.message}`
      );
    }
  }

  /**
   * Apprend à partir d'une URL ou d'un document
   * @param {string} url - URL ou chemin du document
   * @param {Object} options - Options d'apprentissage
   * @returns {Promise<Object>} Résultat de l'apprentissage
   */
  async learnFromUrl(url, options = {}) {
    if (!this.ready) {
      await this.initialize();
      if (!this.ready) {
        throw new Error("LearningEngine non disponible");
      }
    }

    try {
      logger.info("LearningEngine: Apprentissage depuis URL", { url });

      // Appeler le backend Python pour l'apprentissage depuis URL
      const response = await this.pythonBridge.invokeMethod(
        "learning",
        "learnFromUrl",
        {
          url,
          options: {
            depth: options.depth || 1,
            maxPages: options.maxPages || 5,
            extractImages: options.extractImages || false,
            timeout: options.timeout || 30000,
            ...options,
          },
        }
      );

      // Mise à jour des statistiques
      if (response.success) {
        this.stats.learningEvents++;
        this.stats.lastLearningEvent = new Date().toISOString();
      }

      logger.info("LearningEngine: Apprentissage depuis URL terminé", {
        success: response.success,
        extractedFacts: response.facts ? response.facts.length : 0,
        processingTime: response.processingTime,
      });

      return response;
    } catch (error) {
      logger.error("LearningEngine: Erreur d'apprentissage depuis URL", {
        error: error.message,
        url,
      });
      throw new Error(
        `Erreur lors de l'apprentissage depuis l'URL: ${error.message}`
      );
    }
  }

  /**
   * Identifie les lacunes de connaissances
   * @param {Object} options - Options pour l'identification
   * @returns {Promise<Array>} Liste des lacunes identifiées
   */
  async identifyKnowledgeGaps(options = {}) {
    if (!this.ready) {
      await this.initialize();
      if (!this.ready) {
        throw new Error("LearningEngine non disponible");
      }
    }

    try {
      logger.debug("LearningEngine: Identification des lacunes", { options });

      // Appeler le backend Python pour identifier les lacunes
      const response = await this.pythonBridge.invokeMethod(
        "learning",
        "identifyKnowledgeGaps",
        {
          options: {
            limit: options.limit || 10,
            minConfidence: options.minConfidence || 0.6,
            categories: options.categories || [],
            includeMetadata: options.includeMetadata || true,
            ...options,
          },
        }
      );

      logger.info("LearningEngine: Lacunes identifiées", {
        count: response.gaps ? response.gaps.length : 0,
      });

      return response.gaps || [];
    } catch (error) {
      logger.error(
        "LearningEngine: Erreur lors de l'identification des lacunes",
        {
          error: error.message,
        }
      );
      return [];
    }
  }

  /**
   * Récupère les statistiques actuelles du moteur d'apprentissage
   * @returns {Promise<Object>} Statistiques d'apprentissage
   */
  async getStats() {
    if (!this.ready) {
      await this.initialize();
      if (!this.ready) {
        return this.stats;
      }
    }

    try {
      // Appeler le backend Python pour obtenir les statistiques à jour
      const response = await this.pythonBridge.invokeMethod(
        "learning",
        "getStats",
        {}
      );

      if (response && response.stats) {
        this.stats = response.stats;
      }

      return this.stats;
    } catch (error) {
      logger.error(
        "LearningEngine: Erreur lors de la récupération des statistiques",
        {
          error: error.message,
        }
      );
      return this.stats;
    }
  }
}

module.exports = LearningEngine;
