/**
 * Interface avec la base de données vectorielle
 * Gère les embeddings et la recherche sémantique
 */

const logger = require("../utils/logger");
const config = require("../utils/config");
const axios = require("axios");

class VectorDatabase {
  constructor() {
    this.ready = false;
    this.initialized = false;
    this.stats = {
      vectors: 0,
      collections: 0,
      lastUpdated: null,
    };
    this.config = {
      url: config.vectorDb?.url || "http://weaviate:8080",
      apiKey: config.vectorDb?.apiKey || null,
      timeout: config.vectorDb?.timeout || 10000,
    };
    logger.info("VectorDatabase: Instance créée");
  }

  /**
   * Initialise la connexion à la base de données vectorielle
   * @returns {Promise<boolean>} Succès de l'initialisation
   */
  async initialize() {
    try {
      logger.info("VectorDatabase: Initialisation...");

      // Vérifier que la base de données vectorielle est accessible
      const status = await this.checkConnection();

      if (status) {
        this.ready = true;
        this.initialized = true;
        await this.updateStats();
        logger.info("VectorDatabase: Connexion établie", { stats: this.stats });
        return true;
      } else {
        logger.warn("VectorDatabase: Service non disponible");
        this.ready = false;
        return false;
      }
    } catch (error) {
      logger.error("VectorDatabase: Erreur d'initialisation", {
        error: error.message,
        stack: error.stack,
      });
      this.ready = false;
      return false;
    }
  }

  /**
   * Vérifie la connexion à la base de données vectorielle
   * @returns {Promise<boolean>} État de la connexion
   */
  async checkConnection() {
    try {
      // Pour Weaviate, on vérifie le point de terminaison /.well-known/ready
      const response = await axios.get(`${this.config.url}/.well-known/ready`, {
        timeout: this.config.timeout,
        headers: this.config.apiKey
          ? {
              Authorization: `Bearer ${this.config.apiKey}`,
            }
          : {},
      });

      return response.status === 200;
    } catch (error) {
      logger.error("VectorDatabase: Erreur de connexion", {
        error: error.message,
      });
      return false;
    }
  }

  /**
   * Met à jour les statistiques de la base de données
   * @returns {Promise<Object>} Statistiques mises à jour
   */
  async updateStats() {
    try {
      if (!this.ready) {
        return this.stats;
      }

      // Pour Weaviate, on récupère les informations via /v1
      const response = await axios.get(`${this.config.url}/v1/schema`, {
        timeout: this.config.timeout,
        headers: this.config.apiKey
          ? {
              Authorization: `Bearer ${this.config.apiKey}`,
            }
          : {},
      });

      if (response.status === 200 && response.data) {
        const collections = response.data.classes || [];
        this.stats.collections = collections.length;

        // Récupérer le nombre total de vecteurs
        // Dans une implémentation réelle, on utiliserait une requête agrégée
        let totalVectors = 0;
        for (const collection of collections) {
          try {
            const countResponse = await axios.get(
              `${this.config.url}/v1/objects?class=${collection.class}&limit=0`,
              {
                timeout: this.config.timeout,
                headers: this.config.apiKey
                  ? {
                      Authorization: `Bearer ${this.config.apiKey}`,
                    }
                  : {},
              }
            );

            totalVectors += countResponse.data?.totalResults || 0;
          } catch (error) {
            logger.warn(
              `VectorDatabase: Erreur lors du comptage des vecteurs pour ${collection.class}`,
              {
                error: error.message,
              }
            );
          }
        }

        this.stats.vectors = totalVectors;
        this.stats.lastUpdated = new Date().toISOString();
      }

      return this.stats;
    } catch (error) {
      logger.error(
        "VectorDatabase: Erreur lors de la mise à jour des statistiques",
        {
          error: error.message,
        }
      );
      return this.stats;
    }
  }

  /**
   * Effectue une recherche vectorielle
   * @param {string} query - Requête de recherche
   * @param {Object} options - Options de recherche
   * @returns {Promise<Array>} Résultats de la recherche
   */
  async search(query, options = {}) {
    if (!this.ready) {
      await this.initialize();
      if (!this.ready) {
        throw new Error("VectorDatabase non disponible");
      }
    }

    try {
      logger.debug("VectorDatabase: Recherche", {
        query,
        collection: options.collection,
      });

      // Dans une implémentation réelle, nous utiliserions le client Weaviate officiel
      // ou d'autres APIs spécifiques à la base de données vectorielle choisie
      // Ceci est une simplification pour l'exemple

      const requestOptions = {
        className: options.collection || "Knowledge",
        properties: options.properties || [
          "content",
          "title",
          "url",
          "metadata",
        ],
        limit: options.limit || 10,
        nearText: {
          concepts: [query],
        },
      };

      if (options.filters) {
        requestOptions.where = options.filters;
      }

      // Exemple d'utilisation de l'API REST Weaviate
      const response = await axios.post(
        `${this.config.url}/v1/graphql`,
        {
          query: `
          {
            Get {
              ${requestOptions.className} (
                limit: ${requestOptions.limit}
                nearText: {
                  concepts: ["${query}"]
                }
                ${
                  options.filters
                    ? "where: " + JSON.stringify(options.filters)
                    : ""
                }
              ) {
                ${requestOptions.properties.join("\n")}
                _additional {
                  distance
                  id
                }
              }
            }
          }
        `,
        },
        {
          timeout: this.config.timeout,
          headers: {
            "Content-Type": "application/json",
            ...(this.config.apiKey
              ? {
                  Authorization: `Bearer ${this.config.apiKey}`,
                }
              : {}),
          },
        }
      );

      // Traiter les résultats
      const results =
        response.data?.data?.Get?.[requestOptions.className] || [];

      logger.debug("VectorDatabase: Résultats obtenus", {
        count: results.length,
      });

      return results.map((result) => ({
        id: result._additional.id,
        distance: result._additional.distance,
        score: 1 - result._additional.distance, // Convertir distance en score (1 = parfait)
        ...result,
      }));
    } catch (error) {
      logger.error("VectorDatabase: Erreur de recherche", {
        error: error.message,
        query,
      });
      throw new Error(
        `Erreur lors de la recherche vectorielle: ${error.message}`
      );
    }
  }

  /**
   * Ajoute un vecteur à la base de données
   * @param {Object} data - Données à vectoriser et stocker
   * @param {Object} options - Options d'ajout
   * @returns {Promise<Object>} Résultat de l'opération
   */
  async addVector(data, options = {}) {
    if (!this.ready) {
      await this.initialize();
      if (!this.ready) {
        throw new Error("VectorDatabase non disponible");
      }
    }

    try {
      logger.debug("VectorDatabase: Ajout de vecteur", {
        collection: options.collection,
        hasContent: !!data.content,
      });

      // Préparation des données
      const requestData = {
        class: options.collection || "Knowledge",
        properties: {
          ...(data.content && { content: data.content }),
          ...(data.title && { title: data.title }),
          ...(data.url && { url: data.url }),
          ...(data.metadata && { metadata: JSON.stringify(data.metadata) }),
          ...data.additionalProperties,
        },
      };

      // Vectorisation et ajout (dans une implémentation réelle, cela pourrait passer par le backend Python)
      const response = await axios.post(
        `${this.config.url}/v1/objects`,
        requestData,
        {
          timeout: this.config.timeout,
          headers: {
            "Content-Type": "application/json",
            ...(this.config.apiKey
              ? {
                  Authorization: `Bearer ${this.config.apiKey}`,
                }
              : {}),
          },
        }
      );

      // Mise à jour des statistiques locales
      this.stats.vectors++;
      this.stats.lastUpdated = new Date().toISOString();

      logger.info("VectorDatabase: Vecteur ajouté", {
        id: response.data?.id,
        collection: options.collection || "Knowledge",
      });

      return {
        success: true,
        id: response.data?.id,
        status: response.status,
        stats: this.stats,
      };
    } catch (error) {
      logger.error("VectorDatabase: Erreur d'ajout de vecteur", {
        error: error.message,
        collection: options.collection,
      });
      throw new Error(`Erreur lors de l'ajout de vecteur: ${error.message}`);
    }
  }

  /**
   * Supprime un vecteur de la base de données
   * @param {string} id - Identifiant du vecteur
   * @param {Object} options - Options de suppression
   * @returns {Promise<Object>} Résultat de l'opération
   */
  async deleteVector(id, options = {}) {
    if (!this.ready) {
      await this.initialize();
      if (!this.ready) {
        throw new Error("VectorDatabase non disponible");
      }
    }

    try {
      logger.debug("VectorDatabase: Suppression de vecteur", { id });

      // Suppression via l'API Weaviate
      const response = await axios.delete(
        `${this.config.url}/v1/objects/${id}`,
        {
          timeout: this.config.timeout,
          headers: this.config.apiKey
            ? {
                Authorization: `Bearer ${this.config.apiKey}`,
              }
            : {},
        }
      );

      // Mise à jour des statistiques locales
      if (response.status === 204) {
        this.stats.vectors = Math.max(0, this.stats.vectors - 1);
        this.stats.lastUpdated = new Date().toISOString();
      }

      logger.info("VectorDatabase: Vecteur supprimé", { id });

      return {
        success: response.status === 204,
        status: response.status,
        stats: this.stats,
      };
    } catch (error) {
      logger.error("VectorDatabase: Erreur de suppression de vecteur", {
        error: error.message,
        id,
      });
      throw new Error(
        `Erreur lors de la suppression de vecteur: ${error.message}`
      );
    }
  }

  /**
   * Crée une nouvelle collection (classe)
   * @param {string} name - Nom de la collection
   * @param {Object} schema - Schéma de la collection
   * @returns {Promise<Object>} Résultat de l'opération
   */
  async createCollection(name, schema = {}) {
    if (!this.ready) {
      await this.initialize();
      if (!this.ready) {
        throw new Error("VectorDatabase non disponible");
      }
    }

    try {
      logger.info("VectorDatabase: Création de collection", { name });

      // Configuration par défaut pour une collection Knowledge
      const defaultSchema = {
        class: name,
        description: schema.description || `Collection ${name}`,
        vectorizer: schema.vectorizer || "text2vec-transformers",
        properties: schema.properties || [
          {
            name: "content",
            dataType: ["text"],
            description: "Contenu textuel",
          },
          {
            name: "title",
            dataType: ["string"],
            description: "Titre du document",
          },
          {
            name: "url",
            dataType: ["string"],
            description: "URL source",
          },
          {
            name: "metadata",
            dataType: ["string"],
            description: "Métadonnées (JSON)",
          },
        ],
      };

      // Création via l'API Weaviate
      const response = await axios.post(
        `${this.config.url}/v1/schema`,
        defaultSchema,
        {
          timeout: this.config.timeout,
          headers: {
            "Content-Type": "application/json",
            ...(this.config.apiKey
              ? {
                  Authorization: `Bearer ${this.config.apiKey}`,
                }
              : {}),
          },
        }
      );

      // Mise à jour des statistiques
      if (response.status === 200) {
        this.stats.collections++;
        this.stats.lastUpdated = new Date().toISOString();
      }

      logger.info("VectorDatabase: Collection créée", { name });

      return {
        success: response.status === 200,
        collection: name,
        status: response.status,
        stats: this.stats,
      };
    } catch (error) {
      logger.error("VectorDatabase: Erreur de création de collection", {
        error: error.message,
        name,
      });
      throw new Error(
        `Erreur lors de la création de collection: ${error.message}`
      );
    }
  }
}

module.exports = VectorDatabase;
