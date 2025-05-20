"""
Module de gestion du dialogue
Coordonne les composants de conversation pour générer des réponses pertinentes
"""

import logging
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple

# Importation des sous-composants
from .intent_classifier import IntentClassifier
from .response_generator import ResponseGenerator
from .context_handler import ContextHandler

# Configuration des logs
logger = logging.getLogger("lucie.conversation.dialog_manager")


class DialogManager:
    """
    Gestionnaire de dialogue principal.
    Coordonne les différents composants pour traiter les messages et générer des réponses.
    """

    def __init__(self):
        """Initialise le gestionnaire de dialogue"""
        self.intent_classifier = IntentClassifier()
        self.response_generator = ResponseGenerator()
        self.context_handler = ContextHandler()
        self.stats = {
            "messages_processed": 0,
            "intents_recognized": 0,
            "fallback_count": 0,
            "avg_response_time": 0,
            "last_updated": datetime.now().isoformat(),
        }
        logger.info("DialogManager initialized")

    async def process_message(
        self, message: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Traite un message utilisateur et génère une réponse appropriée.

        Args:
            message (str): Le message à traiter
            context (Dict[str, Any], optional): Le contexte de la conversation

        Returns:
            Dict[str, Any]: La réponse et le contexte mis à jour
        """
        start_time = time.time()

        # Initialiser le contexte si nécessaire
        context = context or {}

        # Mettre à jour le contexte avec le message de l'utilisateur
        updated_context = self.context_handler.update_context(message, context)

        try:
            # Classification d'intention
            intent_result = await self.intent_classifier.classify(
                message, updated_context
            )
            intent = intent_result.get("intent", "unknown")
            intent_score = intent_result.get("confidence", 0.0)
            entities = intent_result.get("entities", [])

            # Mettre à jour le contexte avec l'intention et les entités
            updated_context = self.context_handler.add_intent_to_context(
                intent, intent_score, entities, updated_context
            )

            # Vérifier si l'intention est reconnue avec un score suffisant
            if (
                intent_score < 0.5
                and intent != "conversation.greeting"
                and intent != "conversation.help"
            ):
                logger.warning(f"Low confidence intent: {intent} ({intent_score:.2f})")

                # Décider s'il faut utiliser l'intention ou passer en mode secours
                if intent_score < 0.3:
                    logger.info("Falling back to general conversation")
                    intent = "fallback.general"
                    self.stats["fallback_count"] += 1
            else:
                self.stats["intents_recognized"] += 1

            # Générer une réponse basée sur l'intention
            response_result = await self.response_generator.generate_response(
                message, intent, entities, updated_context
            )

            # Mettre à jour le contexte avec la réponse
            final_context = self.context_handler.add_response_to_context(
                response_result.get("response", ""), updated_context
            )

            # Mettre à jour les statistiques
            self.stats["messages_processed"] += 1

            # Calculer le temps de réponse moyen
            response_time = time.time() - start_time
            avg_time = self.stats["avg_response_time"]
            self.stats["avg_response_time"] = (
                avg_time * (self.stats["messages_processed"] - 1) + response_time
            ) / self.stats["messages_processed"]
            self.stats["last_updated"] = datetime.now().isoformat()

            logger.info(
                f"Message processed in {response_time:.2f}s: Intent={intent} ({intent_score:.2f})"
            )

            # Préparer le résultat
            return {
                "response": response_result.get("response", ""),
                "intent": intent,
                "confidence": intent_score,
                "entities": entities,
                "context": final_context,
                "processing_time": response_time,
            }

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

            # En cas d'erreur, générer une réponse de secours
            error_response = "Je suis désolée, j'ai rencontré une erreur lors du traitement de votre message. L'équipe technique en a été informée."

            return {
                "response": error_response,
                "intent": "error.processing",
                "confidence": 1.0,
                "entities": [],
                "context": updated_context,
                "error": str(e),
            }

    def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques du gestionnaire de dialogue.

        Returns:
            Dict[str, Any]: Les statistiques du gestionnaire de dialogue
        """
        return self.stats

    async def train(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Entraîne les composants du gestionnaire de dialogue.

        Args:
            training_data (Dict[str, Any]): Les données d'entraînement

        Returns:
            Dict[str, Any]: Les résultats de l'entraînement
        """
        results = {"intent_classifier": None, "response_generator": None}

        # Entraîner le classificateur d'intention
        if "intents" in training_data:
            intent_result = await self.intent_classifier.train(training_data["intents"])
            results["intent_classifier"] = intent_result

        # Entraîner le générateur de réponse
        if "responses" in training_data:
            response_result = await self.response_generator.train(
                training_data["responses"]
            )
            results["response_generator"] = response_result

        return results


# Créer une instance du gestionnaire de dialogue
dialog_manager = DialogManager()


# Fonctions d'aide pour l'API
async def process_message(
    message: str, context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Fonction d'aide pour traiter un message.

    Args:
        message (str): Le message à traiter
        context (Dict[str, Any], optional): Le contexte de la conversation

    Returns:
        Dict[str, Any]: La réponse et le contexte mis à jour
    """
    return await dialog_manager.process_message(message, context)


def get_stats() -> Dict[str, Any]:
    """
    Fonction d'aide pour récupérer les statistiques.

    Returns:
        Dict[str, Any]: Les statistiques du gestionnaire de dialogue
    """
    return dialog_manager.get_stats()
