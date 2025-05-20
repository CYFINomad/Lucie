/**
 * Proxy pour l'accès aux modèles d'IA externes
 * Fournit une interface unifiée pour interagir avec différents fournisseurs d'IA
 */

const logger = require("../utils/logger");
const config = require("../utils/config");
const axios = require("axios");

class ModelProxy {
  constructor(pythonBridge) {
    this.pythonBridge = pythonBridge;
    this.availableProviders = new Map();
    this.defaultProvider = null;
    this.initialized = false;

    logger.info("ModelProxy: Instance créée");
  }

  /**
   * Initialise le proxy et vérifie les fournisseurs disponibles
   * @returns {Promise<boolean>} Succès de l'initialisation
   */
  async initialize() {
    try {
      logger.info("ModelProxy: Initialisation...");

      if (!this.pythonBridge) {
        throw new Error("Python bridge est requis pour le ModelProxy");
      }

      // Vérifier que le service multi_ai est disponible
      const status = await this.pythonBridge.checkStatus("multi_ai");

      if (!status || !status.available) {
        logger.warn("ModelProxy: Service multi_ai non disponible", { status });
        return false;
      }

      // Récupérer les fournisseurs disponibles
      const providersResponse = await this.pythonBridge.invokeMethod(
        "multi_ai",
        "listProviders",
        {}
      );

      if (providersResponse && providersResponse.providers) {
        const providers = providersResponse.providers || [];

        for (const provider of providers) {
          this.availableProviders.set(provider.id, {
            id: provider.id,
            name: provider.name,
            models: provider.models || [],
            status: provider.status || "available",
            capabilities: provider.capabilities || [],
            defaultModel: provider.defaultModel,
            metadata: provider.metadata || {},
          });
        }

        if (providersResponse.defaultProvider) {
          this.defaultProvider = providersResponse.defaultProvider;
        } else if (this.availableProviders.size > 0) {
          this.defaultProvider = Array.from(this.availableProviders.keys())[0];
        }

        logger.info("ModelProxy: Fournisseurs disponibles", {
          count: this.availableProviders.size,
          providers: Array.from(this.availableProviders.keys()),
          defaultProvider: this.defaultProvider,
        });

        this.initialized = true;
        return true;
      } else {
        logger.warn("ModelProxy: Aucun fournisseur disponible");
        return false;
      }
    } catch (error) {
      logger.error("ModelProxy: Erreur d'initialisation", {
        error: error.message,
        stack: error.stack,
      });
      return false;
    }
  }

  /**
   * S'assure que le proxy est initialisé
   * @returns {Promise<boolean>} État de l'initialisation
   */
  async ensureInitialized() {
    if (this.initialized) {
      return true;
    }

    return this.initialize();
  }

  /**
   * Récupère les fournisseurs disponibles
   * @returns {Promise<Array>} Liste des fournisseurs
   */
  async getProviders() {
    await this.ensureInitialized();
    return Array.from(this.availableProviders.values());
  }

  /**
   * Récupère les modèles disponibles pour un fournisseur
   * @param {string} providerId - Identifiant du fournisseur
   * @returns {Promise<Array>} Liste des modèles
   */
  async getModels(providerId) {
    await this.ensureInitialized();

    const provider = this.availableProviders.get(
      providerId || this.defaultProvider
    );

    if (!provider) {
      throw new Error(`Fournisseur "${providerId}" non disponible`);
    }

    return provider.models;
  }

  /**
   * Génère une réponse en utilisant un modèle spécifié
   * @param {string} prompt - Requête à envoyer au modèle
   * @param {Object} options - Options de génération
   * @returns {Promise<Object>} Réponse générée
   */
  async generateResponse(prompt, options = {}) {
    await this.ensureInitialized();

    const providerId = options.provider || this.defaultProvider;
    const provider = this.availableProviders.get(providerId);

    if (!provider) {
      throw new Error(`Fournisseur "${providerId}" non disponible`);
    }

    const modelId = options.model || provider.defaultModel;

    // Vérifier que le modèle existe
    const modelExists = provider.models.some((m) => m.id === modelId);

    if (!modelExists) {
      throw new Error(
        `Modèle "${modelId}" non disponible pour le fournisseur "${providerId}"`
      );
    }

    logger.debug("ModelProxy: Génération de réponse", {
      provider: providerId,
      model: modelId,
      promptLength: prompt.length,
    });

    try {
      // Appeler le backend Python pour la génération
      const response = await this.pythonBridge.invokeMethod(
        "multi_ai",
        "generateResponse",
        {
          provider: providerId,
          model: modelId,
          prompt,
          options: {
            temperature: options.temperature || 0.7,
            maxTokens: options.maxTokens || 1000,
            topP: options.topP || 1.0,
            stream: options.stream || false,
            ...options,
          },
        }
      );

      if (response.error) {
        throw new Error(response.error);
      }

      logger.debug("ModelProxy: Réponse générée", {
        provider: providerId,
        model: modelId,
        responseLength: response.text?.length || 0,
      });

      return {
        text: response.text,
        finishReason: response.finishReason,
        usage: response.usage || {},
        provider: providerId,
        model: modelId,
        timestamp: response.timestamp || new Date().toISOString(),
      };
    } catch (error) {
      logger.error("ModelProxy: Erreur de génération", {
        provider: providerId,
        model: modelId,
        error: error.message,
      });

      throw new Error(
        `Erreur de génération avec ${providerId}/${modelId}: ${error.message}`
      );
    }
  }

  /**
   * Génère une réponse en streaming
   * @param {string} prompt - Requête à envoyer au modèle
   * @param {function} callback - Fonction appelée pour chaque fragment de réponse
   * @param {Object} options - Options de génération
   * @returns {Promise<Object>} Récapitulatif de la génération
   */
  async streamResponse(prompt, callback, options = {}) {
    await this.ensureInitialized();

    const providerId = options.provider || this.defaultProvider;
    const provider = this.availableProviders.get(providerId);

    if (!provider) {
      throw new Error(`Fournisseur "${providerId}" non disponible`);
    }

    const modelId = options.model || provider.defaultModel;

    // Vérifier que le modèle existe
    const modelExists = provider.models.some((m) => m.id === modelId);

    if (!modelExists) {
      throw new Error(
        `Modèle "${modelId}" non disponible pour le fournisseur "${providerId}"`
      );
    }

    // Vérifier que le modèle supporte le streaming
    const modelDetails = provider.models.find((m) => m.id === modelId);
    if (!modelDetails.capabilities.includes("streaming")) {
      throw new Error(
        `Le streaming n'est pas pris en charge par le modèle "${modelId}"`
      );
    }

    logger.debug("ModelProxy: Démarrage du streaming", {
      provider: providerId,
      model: modelId,
      promptLength: prompt.length,
    });

    try {
      // Appeler le backend Python pour le streaming
      const response = await this.pythonBridge.invokeMethod(
        "multi_ai",
        "streamResponse",
        {
          provider: providerId,
          model: modelId,
          prompt,
          options: {
            temperature: options.temperature || 0.7,
            maxTokens: options.maxTokens || 1000,
            topP: options.topP || 1.0,
            ...options,
          },
        }
      );

      // Simuler un streaming puisque l'appel gRPC/REST ne supporte pas le vrai streaming
      // Dans une implémentation réelle, on utiliserait WebSockets ou Server-Sent Events
      let fullText = "";

      if (response.chunks && response.chunks.length > 0) {
        for (const chunk of response.chunks) {
          fullText += chunk.text;

          callback({
            text: chunk.text,
            done: false,
            timestamp: chunk.timestamp || new Date().toISOString(),
          });

          // Petite pause pour simuler un vrai streaming
          await new Promise((resolve) => setTimeout(resolve, 50));
        }
      } else if (response.text) {
        // Pas de chunks disponibles, fallback à la découpe manuelle
        const textChunks = response.text.match(/.{1,10}/g) || [];

        for (const chunk of textChunks) {
          fullText += chunk;

          callback({
            text: chunk,
            done: false,
            timestamp: new Date().toISOString(),
          });

          await new Promise((resolve) => setTimeout(resolve, 50));
        }
      }

      // Signal de fin
      callback({
        text: "",
        done: true,
        finishReason: response.finishReason,
        timestamp: new Date().toISOString(),
      });

      logger.debug("ModelProxy: Streaming terminé", {
        provider: providerId,
        model: modelId,
        responseLength: fullText.length,
      });

      return {
        provider: providerId,
        model: modelId,
        finishReason: response.finishReason,
        usage: response.usage || {},
        totalLength: fullText.length,
      };
    } catch (error) {
      logger.error("ModelProxy: Erreur de streaming", {
        provider: providerId,
        model: modelId,
        error: error.message,
      });

      // Signaler l'erreur au callback
      callback({
        text: "",
        done: true,
        error: error.message,
        timestamp: new Date().toISOString(),
      });

      throw new Error(
        `Erreur de streaming avec ${providerId}/${modelId}: ${error.message}`
      );
    }
  }

  /**
   * Évalue plusieurs réponses pour déterminer la meilleure
   * @param {string} query - Requête originale
   * @param {Array} responses - Réponses à évaluer
   * @param {Object} options - Options d'évaluation
   * @returns {Promise<Object>} Résultat de l'évaluation
   */
  async evaluateResponses(query, responses, options = {}) {
    await this.ensureInitialized();

    logger.debug("ModelProxy: Évaluation de réponses", {
      responsesCount: responses.length,
    });

    try {
      const evaluationResponse = await this.pythonBridge.invokeMethod(
        "multi_ai",
        "evaluateResponses",
        {
          query,
          responses,
          options: {
            criteria: options.criteria || ["relevance", "accuracy", "clarity"],
            weights: options.weights || {},
            evaluator: options.evaluator || this.defaultProvider,
            ...options,
          },
        }
      );

      logger.debug("ModelProxy: Évaluation terminée", {
        bestIndex: evaluationResponse.bestIndex,
        scores: evaluationResponse.scores,
      });

      return evaluationResponse;
    } catch (error) {
      logger.error("ModelProxy: Erreur d'évaluation", {
        error: error.message,
      });

      // En cas d'erreur, renvoyer la première réponse comme meilleure par défaut
      return {
        bestIndex: 0,
        bestResponse: responses[0],
        error: error.message,
        scores: responses.map((_, i) => ({
          index: i,
          score: i === 0 ? 1.0 : 0.5,
        })),
      };
    }
  }
}

module.exports = ModelProxy;
