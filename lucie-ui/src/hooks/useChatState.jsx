import { useState, useEffect, useCallback } from "react";
import chatService from "../services/chatService";

/**
 * Hook personnalisé pour gérer l'état du chat
 * Fournit des fonctions pour interagir avec le service de chat
 *
 * @returns {Object} Fonctions et état du chat
 */
const useChatState = () => {
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [suggestions, setSuggestions] = useState([]);

  // Charger l'état initial
  useEffect(() => {
    const initChat = async () => {
      try {
        // Vérifier s'il y a une conversation en cours
        const currentConversation = chatService.getCurrentConversation();

        if (currentConversation) {
          setConversationId(currentConversation.id);
          setMessages(currentConversation.messages);
        } else {
          // Créer une nouvelle conversation
          const newConversationId = await chatService.startNewConversation();
          setConversationId(newConversationId);
        }

        // Charger les suggestions initiales
        await loadSuggestions();
      } catch (error) {
        console.error("Erreur lors de l'initialisation du chat:", error);
        setError("Impossible d'initialiser le chat. Veuillez réessayer.");
      }
    };

    initChat();

    // S'abonner aux changements du service de chat
    const unsubscribe = chatService.addListener(({ currentConversation }) => {
      if (currentConversation) {
        setConversationId(currentConversation.id);
        setMessages(currentConversation.messages);
      }
    });

    return () => {
      // Se désabonner lors du démontage
      unsubscribe();
    };
  }, []);

  /**
   * Charge les suggestions proactives
   */
  const loadSuggestions = useCallback(async () => {
    try {
      const newSuggestions = await chatService.getProactiveSuggestions();
      setSuggestions(newSuggestions);
    } catch (error) {
      console.error("Erreur lors du chargement des suggestions:", error);
      // Suggestions par défaut en cas d'erreur
      setSuggestions([
        "Qu'est-ce que tu peux faire?",
        "Comment fonctionnes-tu?",
        "Aide-moi à comprendre comment utiliser Lucie",
      ]);
    }
  }, []);

  /**
   * Envoie un message à Lucie
   * @param {string} messageText - Texte du message
   * @param {Object} options - Options supplémentaires
   * @returns {Promise<Object>} Message de réponse
   */
  const sendMessage = useCallback(
    async (messageText, options = {}) => {
      try {
        setIsLoading(true);
        setError(null);

        // Envoyer le message via le service
        const response = await chatService.sendMessage(messageText, options);

        // Recharger les suggestions après un délai
        setTimeout(() => {
          loadSuggestions();
        }, 500);

        return response;
      } catch (error) {
        console.error("Erreur lors de l'envoi du message:", error);
        setError("Erreur lors de l'envoi du message. Veuillez réessayer.");
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [loadSuggestions]
  );

  /**
   * Envoie un message en mode streaming
   * @param {string} messageText - Texte du message
   * @param {Function} onChunk - Callback pour chaque morceau de réponse
   * @param {Object} options - Options supplémentaires
   * @returns {Promise<Object>} Résumé de la conversation
   */
  const sendMessageStream = useCallback(
    async (messageText, onChunk, options = {}) => {
      try {
        setIsLoading(true);
        setError(null);

        // Envoyer le message via le service en mode streaming
        const response = await chatService.sendMessageStream(
          messageText,
          onChunk,
          options
        );

        // Recharger les suggestions après un délai
        setTimeout(() => {
          loadSuggestions();
        }, 500);

        return response;
      } catch (error) {
        console.error("Erreur lors de l'envoi du message en streaming:", error);
        setError("Erreur lors de l'envoi du message. Veuillez réessayer.");
        return null;
      } finally {
        setIsLoading(false);
      }
    },
    [loadSuggestions]
  );

  /**
   * Crée une nouvelle conversation
   * @returns {Promise<string>} ID de la nouvelle conversation
   */
  const startNewConversation = useCallback(async () => {
    try {
      setIsLoading(true);

      // Créer une nouvelle conversation
      const newConversationId = await chatService.startNewConversation();
      setConversationId(newConversationId);
      setMessages([]);

      // Recharger les suggestions
      await loadSuggestions();

      return newConversationId;
    } catch (error) {
      console.error(
        "Erreur lors de la création d'une nouvelle conversation:",
        error
      );
      setError(
        "Impossible de créer une nouvelle conversation. Veuillez réessayer."
      );
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [loadSuggestions]);

  /**
   * Supprime une conversation
   * @param {string} convId - ID de la conversation à supprimer
   * @returns {boolean} Succès de la suppression
   */
  const deleteConversation = useCallback(
    (convId) => {
      try {
        const success = chatService.deleteConversation(
          convId || conversationId
        );

        // Si on a supprimé la conversation courante, en créer une nouvelle
        if (success && convId === conversationId) {
          startNewConversation();
        }

        return success;
      } catch (error) {
        console.error(
          "Erreur lors de la suppression de la conversation:",
          error
        );
        setError(
          "Impossible de supprimer la conversation. Veuillez réessayer."
        );
        return false;
      }
    },
    [conversationId, startNewConversation]
  );

  /**
   * Charge l'historique des conversations
   * @param {number} limit - Nombre maximum de conversations
   * @returns {Promise<Array>} Liste des conversations
   */
  const loadConversationHistory = useCallback(async (limit = 10) => {
    try {
      setIsLoading(true);
      const history = await chatService.loadConversationHistory(limit);
      return history;
    } catch (error) {
      console.error("Erreur lors du chargement de l'historique:", error);
      setError("Impossible de charger l'historique. Veuillez réessayer.");
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Envoie un feedback sur un message
   * @param {string} messageId - ID du message
   * @param {string} feedbackType - Type de feedback ('positive', 'negative', 'neutral')
   * @param {string} comment - Commentaire optionnel
   * @returns {Promise<Object>} Résultat de l'opération
   */
  const sendFeedback = useCallback(
    async (messageId, feedbackType, comment = "") => {
      try {
        // Trouver le message concerné
        const message = messages.find((msg) => msg.id === messageId);

        if (!message) {
          throw new Error(`Message ${messageId} introuvable`);
        }

        // Envoyer le feedback au service
        const feedback = {
          messageId,
          conversationId,
          feedbackType,
          comment,
          original: {
            content: message.content,
            timestamp: message.timestamp,
          },
        };

        return await chatService.sendFeedback(feedback);
      } catch (error) {
        console.error("Erreur lors de l'envoi du feedback:", error);
        setError("Impossible d'envoyer le feedback. Veuillez réessayer.");
        return { success: false, error: error.message };
      }
    },
    [messages, conversationId]
  );

  return {
    // État
    messages,
    conversationId,
    isLoading,
    error,
    suggestions,

    // Actions
    sendMessage,
    sendMessageStream,
    startNewConversation,
    deleteConversation,
    loadConversationHistory,
    loadSuggestions,
    sendFeedback,
  };
};

export default useChatState;
