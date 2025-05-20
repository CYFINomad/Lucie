/**
 * Service de gestion du chat
 * Encapsule la logique de conversation avec Lucie
 */

import apiClient from "./apiClient";

class ChatService {
  constructor() {
    this.conversations = [];
    this.currentConversation = null;
    this.listeners = [];
  }

  /**
   * Initialise une nouvelle conversation
   * @returns {string} ID de la conversation
   */
  async startNewConversation() {
    this.currentConversation = {
      id: `conv_${Date.now()}`,
      messages: [],
      startTime: new Date().toISOString(),
      metadata: {},
    };

    this.conversations.unshift(this.currentConversation);
    this._notifyListeners();

    return this.currentConversation.id;
  }

  /**
   * Ajoute un message à la conversation
   * @param {string} content - Contenu du message
   * @param {string} sender - Expéditeur ('user' ou 'lucie')
   * @param {Object} metadata - Métadonnées supplémentaires
   * @returns {Object} Message ajouté
   */
  addMessage(content, sender, metadata = {}) {
    if (!this.currentConversation) {
      this.startNewConversation();
    }

    const message = {
      id: `msg_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
      content,
      sender,
      timestamp: new Date().toISOString(),
      ...metadata,
    };

    this.currentConversation.messages.push(message);
    this._notifyListeners();

    return message;
  }

  /**
   * Envoie un message à Lucie et attend sa réponse
   * @param {string} message - Message à envoyer
   * @param {Object} options - Options supplémentaires
   * @returns {Promise<Object>} Message de réponse
   */
  async sendMessage(message, options = {}) {
    try {
      // Ajouter le message de l'utilisateur
      const userMessage = this.addMessage(message, "user");

      // Préparer le contexte
      const context = this._prepareContext(options.context);

      // Appeler l'API
      const response = await apiClient.sendMessage(message, context);

      // Ajouter la réponse de Lucie
      const lucieMessage = this.addMessage(response.response, "lucie", {
        messageId: response.messageId,
        intent: response.intent,
        confidence: response.confidence,
        featureStatus: response.featureStatus,
      });

      // Mettre à jour les métadonnées de la conversation
      if (response.context) {
        this.currentConversation.metadata = {
          ...this.currentConversation.metadata,
          ...response.context,
        };
      }

      return lucieMessage;
    } catch (error) {
      // En cas d'erreur, ajouter un message d'erreur
      const errorMessage = this.addMessage(
        "Je suis désolée, j'ai rencontré une erreur lors du traitement de votre message. Veuillez réessayer.",
        "lucie",
        { isError: true, errorDetails: error.message }
      );

      return errorMessage;
    }
  }

  /**
   * Version streaming pour envoyer un message
   * @param {string} message - Message à envoyer
   * @param {Function} onChunk - Callback pour chaque morceau de réponse
   * @param {Object} options - Options supplémentaires
   * @returns {Promise<Object>} Résumé de la conversation
   */
  async sendMessageStream(message, onChunk, options = {}) {
    try {
      // Ajouter le message de l'utilisateur
      const userMessage = this.addMessage(message, "user");

      // Préparer le contexte
      const context = this._prepareContext(options.context);

      // Message temporaire pour Lucie (sera mis à jour progressivement)
      const tempLucieMessage = this.addMessage("", "lucie", {
        isStreaming: true,
      });
      let fullResponse = "";

      // Appeler l'API en mode streaming
      await apiClient.sendMessageStream(
        message,
        (chunk) => {
          // Mettre à jour le message temporaire
          if (chunk.type === "token" || chunk.type === "start") {
            fullResponse += chunk.response || "";

            // Mettre à jour le message dans la conversation
            tempLucieMessage.content = fullResponse;
            this._notifyListeners();

            // Appeler le callback
            onChunk({
              type: "chunk",
              content: chunk.response || "",
              fullContent: fullResponse,
              done: false,
            });
          } else if (chunk.type === "end" || chunk.done) {
            // Finaliser le message
            tempLucieMessage.isStreaming = false;
            tempLucieMessage.messageId = chunk.messageId;

            // Mettre à jour le message dans la conversation avec toutes les métadonnées
            if (chunk.context) {
              tempLucieMessage.context = chunk.context;

              // Mettre à jour les métadonnées de la conversation
              this.currentConversation.metadata = {
                ...this.currentConversation.metadata,
                ...chunk.context,
              };
            }

            this._notifyListeners();

            // Appeler le callback avec done=true
            onChunk({
              type: "end",
              content: "",
              fullContent: fullResponse,
              done: true,
            });
          } else if (chunk.error) {
            // Signaler l'erreur
            tempLucieMessage.isError = true;
            tempLucieMessage.content =
              "Je suis désolée, j'ai rencontré une erreur lors du traitement de votre message. Veuillez réessayer.";
            tempLucieMessage.errorDetails = chunk.error;

            this._notifyListeners();

            // Appeler le callback avec l'erreur
            onChunk({
              type: "error",
              error: chunk.error,
              done: true,
            });
          }
        },
        context
      );

      return tempLucieMessage;
    } catch (error) {
      // En cas d'erreur, ajouter un message d'erreur
      const errorMessage = this.addMessage(
        "Je suis désolée, j'ai rencontré une erreur lors du traitement de votre message. Veuillez réessayer.",
        "lucie",
        { isError: true, errorDetails: error.message }
      );

      // Appeler le callback avec l'erreur
      onChunk({
        type: "error",
        error: error.message,
        done: true,
      });

      return errorMessage;
    }
  }

  /**
   * Prépare le contexte pour l'API
   * @param {Object} additionalContext - Contexte supplémentaire
   * @returns {Object} Contexte complet
   */
  _prepareContext(additionalContext = {}) {
    // Contexte de base
    const baseContext = {
      conversation: {
        id: this.currentConversation?.id,
        messages: this.currentConversation?.messages.slice(-5).map((msg) => ({
          content: msg.content,
          sender: msg.sender,
          timestamp: msg.timestamp,
        })),
      },
    };

    // Fusionner avec le contexte supplémentaire
    return {
      ...baseContext,
      ...additionalContext,
    };
  }

  /**
   * Récupère toutes les conversations
   * @returns {Array} Liste des conversations
   */
  getConversations() {
    return this.conversations;
  }

  /**
   * Récupère la conversation actuelle
   * @returns {Object} Conversation actuelle
   */
  getCurrentConversation() {
    return this.currentConversation;
  }

  /**
   * Charge l'historique des conversations depuis l'API
   * @param {number} limit - Nombre maximum de conversations
   * @returns {Promise<Array>} Liste des conversations
   */
  async loadConversationHistory(limit = 10) {
    try {
      const history = await apiClient.getConversationHistory(limit);

      // Remplacer les conversations en cache
      this.conversations = history;

      // Si on a des conversations, définir la plus récente comme courante
      if (history.length > 0) {
        this.currentConversation = history[0];
      }

      this._notifyListeners();

      return history;
    } catch (error) {
      console.error("Failed to load conversation history:", error);

      // Garder les conversations en cache
      return this.conversations;
    }
  }

  /**
   * Supprime une conversation
   * @param {string} conversationId - ID de la conversation à supprimer
   * @returns {boolean} Succès de la suppression
   */
  deleteConversation(conversationId) {
    const index = this.conversations.findIndex(
      (conv) => conv.id === conversationId
    );

    if (index !== -1) {
      this.conversations.splice(index, 1);

      // Si on a supprimé la conversation courante, définir la plus récente comme courante
      if (this.currentConversation?.id === conversationId) {
        this.currentConversation = this.conversations[0] || null;
      }

      this._notifyListeners();

      return true;
    }

    return false;
  }

  /**
   * Ajoute un écouteur pour les changements
   * @param {Function} listener - Fonction à appeler lors des changements
   * @returns {Function} Fonction pour supprimer l'écouteur
   */
  addListener(listener) {
    this.listeners.push(listener);

    // Appeler l'écouteur immédiatement avec l'état actuel
    listener({
      conversations: this.conversations,
      currentConversation: this.currentConversation,
    });

    // Renvoyer une fonction pour supprimer l'écouteur
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index !== -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  /**
   * Notifie tous les écouteurs des changements
   */
  _notifyListeners() {
    const state = {
      conversations: this.conversations,
      currentConversation: this.currentConversation,
    };

    this.listeners.forEach((listener) => {
      try {
        listener(state);
      } catch (error) {
        console.error("Error in chat service listener:", error);
      }
    });
  }

  /**
   * Récupère les suggestions proactives
   * @returns {Promise<Array>} Liste des suggestions
   */
  async getProactiveSuggestions() {
    try {
      // Contexte basé sur la conversation actuelle
      const context = {
        conversation: {
          messageCount: this.currentConversation?.messages.length || 0,
          lastUserMessage: this.currentConversation?.messages
            .filter((msg) => msg.sender === "user")
            .slice(-1)[0]?.content,
        },
      };

      const response = await apiClient.getProactiveSuggestions(context);

      return response.suggestions || [];
    } catch (error) {
      console.error("Failed to fetch suggestions:", error);

      // Suggestions par défaut en cas d'erreur
      return [
        "Qu'est-ce que tu peux faire?",
        "Comment fonctionnes-tu?",
        "Aide-moi à comprendre comment utiliser Lucie",
      ];
    }
  }
}

// Créer une instance singleton
const chatService = new ChatService();

export default chatService;
