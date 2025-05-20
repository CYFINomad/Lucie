/**
 * Service API Client
 * Gère les communications avec le backend Node.js
 * Centralise les requêtes API et la gestion des erreurs
 */

import axios from "axios";

class ApiClient {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || "http://localhost:5000";
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000, // 30 seconds
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Intercepteur pour les requêtes
    this.client.interceptors.request.use(
      (config) => {
        // On pourrait ajouter un token JWT ici si nécessaire
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Intercepteur pour les réponses
    this.client.interceptors.response.use(
      (response) => {
        return response;
      },
      (error) => {
        // Traitement centralisé des erreurs
        console.error("API Error:", error.response || error.message);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Vérifie l'état de santé du backend
   * @returns {Promise<Object>} État de santé
   */
  async checkHealth() {
    try {
      const response = await this.client.get("/health");
      return response.data;
    } catch (error) {
      console.error("Health check failed:", error);
      throw error;
    }
  }

  /**
   * Envoie un message à Lucie
   * @param {string} message - Message à envoyer
   * @param {Object} context - Contexte de la conversation
   * @returns {Promise<Object>} Réponse de Lucie
   */
  async sendMessage(message, context = {}) {
    try {
      const response = await this.client.post("/api/chat/message", {
        message,
        context,
      });
      return response.data;
    } catch (error) {
      console.error("Message sending failed:", error);
      throw error;
    }
  }

  /**
   * Version streaming pour envoyer un message à Lucie
   * @param {string} message - Message à envoyer
   * @param {Function} onChunk - Callback pour chaque morceau de réponse
   * @param {Object} context - Contexte de la conversation
   * @returns {Promise<Object>} Résumé de la réponse
   */
  async sendMessageStream(message, onChunk, context = {}) {
    try {
      const response = await this.client.post(
        "/api/chat/message/stream",
        {
          message,
          context,
        },
        {
          responseType: "text",
          onDownloadProgress: (progressEvent) => {
            // Traiter les événements SSE (Server-Sent Events)
            const text = progressEvent.currentTarget.response;
            const lines = text.split("\n\n");

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                try {
                  const data = JSON.parse(line.substring(6));
                  onChunk(data);
                } catch (e) {
                  console.error("Error parsing SSE data:", e);
                }
              }
            }
          },
        }
      );

      return {
        success: true,
        message: "Streaming completed",
      };
    } catch (error) {
      console.error("Message streaming failed:", error);
      onChunk({
        error: true,
        done: true,
        message: error.message || "Streaming error",
      });
      throw error;
    }
  }

  /**
   * Récupère l'historique des conversations
   * @param {number} limit - Nombre maximum de conversations
   * @returns {Promise<Array>} Liste des conversations
   */
  async getConversationHistory(limit = 10) {
    try {
      const response = await this.client.get("/api/chat/history", {
        params: { limit },
      });
      return response.data;
    } catch (error) {
      console.error("Failed to fetch conversation history:", error);
      throw error;
    }
  }

  /**
   * Récupère l'état des fonctionnalités disponibles
   * @returns {Promise<Object>} État des fonctionnalités
   */
  async getFeatureStatus() {
    try {
      const response = await this.client.get("/api/config/features");
      return response.data;
    } catch (error) {
      console.error("Failed to fetch feature status:", error);
      throw error;
    }
  }

  /**
   * Soumet une URL pour apprentissage
   * @param {string} url - URL à analyser
   * @param {Object} options - Options d'apprentissage
   * @returns {Promise<Object>} Résultat de l'apprentissage
   */
  async learnFromUrl(url, options = {}) {
    try {
      const response = await this.client.post("/api/learning/url", {
        url,
        options,
      });
      return response.data;
    } catch (error) {
      console.error("Learning from URL failed:", error);
      throw error;
    }
  }

  /**
   * Récupère les suggestions proactives
   * @param {Object} context - Contexte de l'utilisateur
   * @returns {Promise<Array>} Liste des suggestions
   */
  async getProactiveSuggestions(context = {}) {
    try {
      const response = await this.client.post("/api/assistance/suggestions", {
        context,
      });
      return response.data;
    } catch (error) {
      console.error("Failed to fetch suggestions:", error);
      // Renvoyer des suggestions par défaut en cas d'erreur
      return {
        suggestions: [
          "Qu'est-ce que tu peux faire?",
          "Comment fonctionnes-tu?",
          "Aide-moi à comprendre comment utiliser Lucie",
        ],
      };
    }
  }

  /**
   * Envoie un feedback utilisateur
   * @param {Object} feedback - Données de feedback
   * @returns {Promise<Object>} Confirmation
   */
  async sendFeedback(feedback) {
    try {
      const response = await this.client.post("/api/feedback", feedback);
      return response.data;
    } catch (error) {
      console.error("Failed to send feedback:", error);
      throw error;
    }
  }
}

// Créer une instance singleton
const apiClient = new ApiClient();

export default apiClient;
