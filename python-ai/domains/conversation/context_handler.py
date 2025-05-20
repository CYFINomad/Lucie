"""
Gestionnaire de contexte pour les conversations
Maintient et met à jour le contexte lors des échanges avec l'utilisateur
"""

import logging
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# Configuration des logs
logger = logging.getLogger("lucie.conversation.context_handler")


class ContextHandler:
    """
    Gestionnaire de contexte pour les conversations.
    Maintient et met à jour le contexte de la conversation pour assurer la cohérence des échanges.
    """

    def __init__(self):
        """Initialise le gestionnaire de contexte"""
        logger.info("ContextHandler initialized")

    def update_context(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour le contexte avec un nouveau message utilisateur.

        Args:
            message (str): Le message de l'utilisateur
            context (Dict[str, Any]): Le contexte actuel

        Returns:
            Dict[str, Any]: Le contexte mis à jour
        """
        # Créer une copie du contexte pour ne pas modifier l'original
        updated_context = context.copy() if context else {}

        # Initialiser la section conversation si elle n'existe pas
        if "conversation" not in updated_context:
            updated_context["conversation"] = {
                "messages": [],
                "start_time": datetime.now().isoformat(),
                "message_count": 0,
            }

        # Ajouter le message à l'historique
        conversation = updated_context["conversation"]

        # Limiter la taille de l'historique pour des raisons de performances
        max_history = 10
        message_history = conversation.get("messages", [])[-max_history:]

        # Ajouter le nouveau message
        message_history.append(
            {
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Mettre à jour le contexte
        conversation["messages"] = message_history
        conversation["message_count"] = conversation.get("message_count", 0) + 1
        conversation["last_user_message"] = message
        conversation["last_user_message_time"] = datetime.now().isoformat()

        # Déterminer si le message est une question
        is_question = "?" in message
        conversation["last_message_is_question"] = is_question

        # Si c'est une question, on attend une réponse
        if is_question:
            conversation["waiting_for_response"] = True

        # Mettre à jour la section utilisateur
        if "user" not in updated_context:
            updated_context["user"] = {
                "total_messages": 0,
                "first_interaction": datetime.now().isoformat(),
            }

        updated_context["user"]["total_messages"] = (
            updated_context["user"].get("total_messages", 0) + 1
        )
        updated_context["user"]["last_activity"] = datetime.now().isoformat()

        return updated_context

    def add_intent_to_context(
        self,
        intent: str,
        confidence: float,
        entities: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Ajoute l'intention reconnue au contexte.

        Args:
            intent (str): L'intention reconnue
            confidence (float): Le niveau de confiance
            entities (List[Dict[str, Any]]): Les entités reconnues
            context (Dict[str, Any]): Le contexte actuel

        Returns:
            Dict[str, Any]: Le contexte mis à jour
        """
        # Créer une copie du contexte
        updated_context = context.copy() if context else {}

        # Accéder à la section conversation
        conversation = updated_context.get("conversation", {})

        # Ajouter l'intention au contexte
        conversation["last_intent"] = intent
        conversation["last_intent_confidence"] = confidence
        conversation["last_intent_time"] = datetime.now().isoformat()

        # Stocker l'historique des intentions
        intent_history = conversation.get("intent_history", [])
        intent_history.append(
            {
                "intent": intent,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Limiter la taille de l'historique
        max_intent_history = 5
        conversation["intent_history"] = intent_history[-max_intent_history:]

        # Ajouter les entités au contexte
        if entities:
            # Stocker les entités actuelles
            conversation["current_entities"] = entities

            # Mettre à jour le dictionnaire des entités par type
            entities_by_type = conversation.get("entities_by_type", {})

            for entity in entities:
                entity_type = entity["type"]
                entity_value = entity["value"]

                if entity_type not in entities_by_type:
                    entities_by_type[entity_type] = []

                # Ajouter l'entité (éviter les doublons)
                entities_by_type[entity_type].append(entity_value)
                entities_by_type[entity_type] = list(set(entities_by_type[entity_type]))

            conversation["entities_by_type"] = entities_by_type

        # Déterminer la prochaine action en fonction de l'intention
        if intent.startswith("question."):
            # Si c'est une question, on s'attend à une réponse
            conversation["expected_intent"] = f"answer.{intent.split('.')[1]}"
            conversation["waiting_for_response"] = True
        elif intent.startswith("request."):
            # Si c'est une demande, on s'attend à une confirmation
            conversation["expected_intent"] = "confirmation"
            conversation["waiting_for_response"] = True
        else:
            # Réinitialiser l'attente si ce n'est pas une question ou une demande
            conversation["expected_intent"] = None
            conversation["waiting_for_response"] = False

        # Mettre à jour le contexte
        updated_context["conversation"] = conversation

        return updated_context

    def add_response_to_context(
        self, response: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ajoute la réponse du système au contexte.

        Args:
            response (str): La réponse générée
            context (Dict[str, Any]): Le contexte actuel

        Returns:
            Dict[str, Any]: Le contexte mis à jour
        """
        # Créer une copie du contexte
        updated_context = context.copy() if context else {}

        # Accéder à la section conversation
        conversation = updated_context.get("conversation", {})

        # Ajouter la réponse à l'historique
        message_history = conversation.get("messages", [])

        message_history.append(
            {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Mettre à jour le contexte
        conversation["messages"] = message_history
        conversation["last_assistant_message"] = response
        conversation["last_assistant_message_time"] = datetime.now().isoformat()

        # Si on attendait une réponse, c'est maintenant fait
        if conversation.get("waiting_for_response"):
            conversation["waiting_for_response"] = False

        # Mettre à jour le contexte
        updated_context["conversation"] = conversation

        return updated_context

    def get_relevant_context(
        self, context: Dict[str, Any], max_messages: int = 5
    ) -> Dict[str, Any]:
        """
        Extrait les informations contextuelles les plus pertinentes.

        Args:
            context (Dict[str, Any]): Le contexte complet
            max_messages (int, optional): Nombre maximum de messages à inclure

        Returns:
            Dict[str, Any]: Le contexte pertinent
        """
        if not context:
            return {}

        # Créer un nouveau contexte avec uniquement les informations essentielles
        relevant_context = {"conversation": {}}

        # Copier les informations de conversation pertinentes
        conversation = context.get("conversation", {})

        # Inclure les messages récents
        if "messages" in conversation:
            relevant_context["conversation"]["messages"] = conversation["messages"][
                -max_messages:
            ]

        # Inclure l'intention actuelle
        if "last_intent" in conversation:
            relevant_context["conversation"]["last_intent"] = conversation[
                "last_intent"
            ]
            relevant_context["conversation"]["last_intent_confidence"] = (
                conversation.get("last_intent_confidence")
            )

        # Inclure les entités reconnues
        if "entities_by_type" in conversation:
            relevant_context["conversation"]["entities_by_type"] = conversation[
                "entities_by_type"
            ]

        # Inclure les informations sur l'utilisateur si disponibles
        if "user" in context:
            relevant_context["user"] = {
                "preferences": context["user"].get("preferences", {}),
                "total_messages": context["user"].get("total_messages", 0),
            }

        return relevant_context

    def merge_contexts(
        self, context1: Dict[str, Any], context2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fusionne deux contextes.

        Args:
            context1 (Dict[str, Any]): Premier contexte
            context2 (Dict[str, Any]): Second contexte

        Returns:
            Dict[str, Any]: Le contexte fusionné
        """
        # Créer une copie du premier contexte
        merged_context = context1.copy() if context1 else {}

        # Si le second contexte est vide, retourner le premier
        if not context2:
            return merged_context

        # Parcourir les sections du second contexte
        for section, data in context2.items():
            # Si la section n'existe pas dans le contexte fusionné, la copier
            if section not in merged_context:
                merged_context[section] = data.copy()
                continue

            # Sinon, fusionner les données
            if isinstance(data, dict) and isinstance(merged_context[section], dict):
                # Fusionner les dictionnaires récursivement
                for key, value in data.items():
                    if key not in merged_context[section]:
                        merged_context[section][key] = value
                    elif isinstance(value, list) and isinstance(
                        merged_context[section][key], list
                    ):
                        # Fusionner les listes
                        merged_context[section][key].extend(value)
                    elif isinstance(value, dict) and isinstance(
                        merged_context[section][key], dict
                    ):
                        # Fusionner les dictionnaires récursivement
                        merged_context[section][key] = self.merge_contexts(
                            merged_context[section][key], value
                        )
                    else:
                        # Priorité au second contexte pour les valeurs simples
                        merged_context[section][key] = value
            elif isinstance(data, list) and isinstance(merged_context[section], list):
                # Fusionner les listes
                merged_context[section].extend(data)
            else:
                # Priorité au second contexte pour les valeurs simples
                merged_context[section] = data

        return merged_context


# Créer une instance par défaut
context_handler = ContextHandler()
