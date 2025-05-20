/**
 * Classe principale du noyau de Lucie
 * Gère l'orchestration des différents composants et services
 */

const logger = require("../utils/logger");
const config = require("../utils/config");
const {
  extendLucieCoreWithAgents,
} = require("../agents/lucie-core-agents-integration");

class LucieCore {
  constructor() {
    this.components = new Map();
    this.initialized = false;
    this.services = {};
    this.startTime = new Date();
    logger.info("Instance LucieCore créée");

    // Étendre avec le système d'agents
    extendLucieCoreWithAgents(this);
  }

  /**
   * Initialise le noyau de Lucie et tous ses composants
   * @returns {Promise<boolean>} Succès de l'initialisation
   */
  async initialize() {
    try {
      logger.info("Initialisation du noyau Lucie...");

      // Initialiser la communication avec Python
      const PythonBridge = require("../python-bridge/grpcClient");
      // Utiliser le bridge amélioré à la place
      // const PythonBridge = require("../python-bridge/enhancedPythonBridge");
      this.registerComponent("pythonBridge", new PythonBridge());

      // Initialiser la base de connaissances
      const KnowledgeBase = require("./KnowledgeBase");
      this.registerComponent(
        "knowledgeBase",
        new KnowledgeBase(this.getComponent("pythonBridge"))
      );

      // Initialiser le moteur d'apprentissage
      const LearningEngine = require("./LearningEngine");
      this.registerComponent(
        "learningEngine",
        new LearningEngine(this.getComponent("pythonBridge"))
      );

      // Initialiser la base de données vectorielle
      const VectorDatabase = require("./VectorDatabase");
      this.registerComponent("vectorDatabase", new VectorDatabase());

      // Enregistrer les services de base
      this.services = {
        state: {
          conversationState: {},
          userPreferences: {},
          activeAgents: [],
          recentTopics: [],
        },
        version: config.version || "0.1.0",
        startTime: this.startTime,
        features: config.features,
        environment: config.environment,
      };

      this.initialized = true;
      logger.info("Noyau Lucie initialisé avec succès", {
        componentsCount: this.components.size,
        enabledFeatures: Object.keys(config.features).filter(
          (key) => config.features[key]
        ),
      });
      return true;
    } catch (error) {
      logger.error("Erreur lors de l'initialisation du noyau Lucie:", {
        error: error.message,
        stack: error.stack,
      });
      throw error;
    }
  }

  /**
   * Enregistre un composant dans le noyau
   * @param {string} name - Nom du composant
   * @param {Object} component - Instance du composant
   */
  registerComponent(name, component) {
    this.components.set(name, component);
    logger.debug(`Composant "${name}" enregistré`);
    return component;
  }

  /**
   * Récupère un composant enregistré
   * @param {string} name - Nom du composant
   * @returns {Object} Instance du composant
   */
  getComponent(name) {
    if (!this.components.has(name)) {
      logger.warn(`Tentative d'accès à un composant non enregistré: "${name}"`);
      return null;
    }
    return this.components.get(name);
  }

  /**
   * Vérifie si un composant est enregistré
   * @param {string} name - Nom du composant
   * @returns {boolean} Vrai si le composant existe
   */
  hasComponent(name) {
    return this.components.has(name);
  }

  /**
   * Récupère l'état actuel du noyau Lucie
   * @returns {Object} État détaillé du noyau
   */
  getStatus() {
    return {
      initialized: this.initialized,
      componentsCount: this.components.size,
      componentsList: Array.from(this.components.keys()),
      uptime: Date.now() - this.startTime,
      version: this.services.version,
      environment: this.services.environment,
      enabledFeatures: Object.keys(this.services.features).filter(
        (key) => this.services.features[key]
      ),
    };
  }

  /**
   * Traite un message utilisateur
   * @param {string} message - Message de l'utilisateur
   * @param {Object} context - Contexte de la conversation
   * @returns {Promise<Object>} Réponse traitée
   */
  async processMessage(message, context = {}) {
    if (!this.initialized) {
      throw new Error("Le noyau Lucie n'est pas initialisé.");
    }

    try {
      logger.debug("Traitement du message", { messageLength: message.length });

      // Enrichir le contexte avec les informations système
      const enrichedContext = {
        ...context,
        systemState: {
          timestamp: new Date().toISOString(),
          version: this.services.version,
        },
      };

      // Utiliser le bridge Python pour le traitement du message
      const pythonBridge = this.getComponent("pythonBridge");
      if (!pythonBridge) {
        throw new Error("Bridge Python non disponible");
      }

      const response = await pythonBridge.processMessage(
        message,
        enrichedContext
      );

      // Mise à jour de l'état de la conversation
      this.services.state.conversationState = {
        ...(this.services.state.conversationState || {}),
        lastMessage: message,
        lastResponse: response.response,
        timestamp: new Date().toISOString(),
      };

      return response;
    } catch (error) {
      logger.error("Erreur lors du traitement du message", {
        error: error.message,
        stack: error.stack,
      });

      // Réponse de fallback en cas d'erreur
      return {
        response:
          "Je suis désolée, j'ai rencontré une erreur lors du traitement de votre message. Nos équipes techniques ont été informées de ce problème.",
        timestamp: new Date().toISOString(),
        error: true,
        errorType: error.name,
        errorMessage: error.message,
      };
    }
  }
}

// Export d'une instance singleton
const lucieCore = new LucieCore();

module.exports = lucieCore;
