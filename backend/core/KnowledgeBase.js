/**
 * Interface avec la base de connaissances Python
 * Gère l'accès et les requêtes à la base de connaissances
 */

const logger = require("../utils/logger");
const config = require("../utils/config");

class KnowledgeBase {
  /**
   * Crée une instance de l'interface avec la base de connaissances
   * @param {Object} pythonBridge - Interface avec le service Python
   */
  constructor(pythonBridge) {
    this.pythonBridge = pythonBridge;
    this.ready = false;
    this.initialized = false;
    this.graphStats = {
      nodes: 0,
      relationships: 0,
      lastUpdated: null,
    };
    logger.info("KnowledgeBase: Instance créée");
  }

  /**
   * Initialise la connexion à la base de connaissances
   * @returns {Promise<boolean>} Succès de l'initialisation
   */
  async initialize() {
    try {
      if (!this.pythonBridge) {
        throw new Error("Python bridge non disponible pour KnowledgeBase");
      }

      logger.info("KnowledgeBase: Initialisation...");

      // Vérifier la connexion au backend Python
      const status = await this.pythonBridge.checkStatus("knowledge");

      if (status && status.available) {
        this.ready = true;
        this.graphStats = status.stats || this.graphStats;
        this.initialized = true;
        logger.info("KnowledgeBase: Connexion établie", {
          stats: this.graphStats,
        });
        return true;
      } else {
        logger.warn("KnowledgeBase: Service non disponible", { status });
        this.ready = false;
        return false;
      }
    } catch (error) {
      logger.error("KnowledgeBase: Erreur d'initialisation", {
        error: error.message,
        stack: error.stack,
      });
      this.ready = false;
      return false;
    }
  }

  /**
   * Recherche des informations dans la base de connaissances
   * @param {string} query - Requête de recherche
   * @param {Object} options - Options de recherche
   * @returns {Promise<Array>} Résultats de la recherche
   */
  async query(query, options = {}) {
    if (!this.ready) {
      await this.initialize();
      if (!this.ready) {
        throw new Error("KnowledgeBase non disponible");
      }
    }

    try {
      logger.debug("KnowledgeBase: Requête", { query, options });

      // Appeler le backend Python pour la requête
      const response = await this.pythonBridge.invokeMethod(
        "knowledge",
        "query",
        {
          query,
          options: {
            limit: options.limit || 10,
            threshold: options.threshold || 0.7,
            includeMetadata: options.includeMetadata || true,
            ...options,
          },
        }
      );

      logger.debug("KnowledgeBase: Résultats obtenus", {
        count: response?.results?.length || 0,
      });

      return response?.results || [];
    } catch (error) {
      logger.error("KnowledgeBase: Erreur de requête", {
        error: error.message,
        query,
      });
      throw new Error(`Erreur lors de la requête: ${error.message}`);
    }
  }

  /**
   * Ajoute une nouvelle connaissance au graphe
   * @param {Object} data - Données à ajouter
   * @returns {Promise<Object>} Résultat de l'opération
   */
  async addKnowledge(data) {
    if (!this.ready) {
      await this.initialize();
      if (!this.ready) {
        throw new Error("KnowledgeBase non disponible");
      }
    }

    try {
      logger.debug("KnowledgeBase: Ajout de connaissance", {
        type: data.type,
        hasContent: !!data.content,
      });

      // Appeler le backend Python pour ajouter la connaissance
      const response = await this.pythonBridge.invokeMethod(
        "knowledge",
        "addKnowledge",
        {
          data,
        }
      );

      // Mise à jour des statistiques
      if (response.success && response.stats) {
        this.graphStats = response.stats;
      }

      logger.info("KnowledgeBase: Connaissance ajoutée", {
        id: response.id,
        success: response.success,
      });

      return response;
    } catch (error) {
      logger.error("KnowledgeBase: Erreur d'ajout", {
        error: error.message,
        dataType: data.type,
      });
      throw new Error(
        `Erreur lors de l'ajout de connaissances: ${error.message}`
      );
    }
  }

  /**
   * Récupère des informations sur le graphe de connaissances
   * @returns {Promise<Object>} Statistiques du graphe
   */
  async getGraphStats() {
    if (!this.ready) {
      await this.initialize();
      if (!this.ready) {
        return this.graphStats;
      }
    }

    try {
      // Appeler le backend Python pour obtenir les statistiques à jour
      const response = await this.pythonBridge.invokeMethod(
        "knowledge",
        "getGraphStats",
        {}
      );

      if (response && response.stats) {
        this.graphStats = response.stats;
      }

      return this.graphStats;
    } catch (error) {
      logger.error(
        "KnowledgeBase: Erreur lors de la récupération des statistiques",
        {
          error: error.message,
        }
      );
      return this.graphStats;
    }
  }
}

module.exports = KnowledgeBase;
