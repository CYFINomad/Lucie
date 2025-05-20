"""
Classificateur d'intentions pour l'analyse des messages
Détermine l'intention de l'utilisateur et extrait les entités pertinentes
"""

import logging
import json
import os
import re
import time
import asyncio
from typing import Dict, Any, List, Optional, Union, Set, Tuple
from datetime import datetime

# Configuration des logs
logger = logging.getLogger("lucie.conversation.intent_classifier")

# Constantes
DEFAULT_INTENTS_FILE = os.path.join(os.path.dirname(__file__), "data", "intents.json")
FALLBACK_INTENT = "fallback.general"


class IntentClassifier:
    """
    Classificateur d'intentions basé sur des règles et des modèles.
    Détecte l'intention de l'utilisateur et extrait les entités mentionnées.
    """

    def __init__(self, intents_file: str = None):
        """
        Initialise le classificateur d'intentions.

        Args:
            intents_file (str, optional): Chemin vers le fichier de définition des intentions
        """
        self.intents = {}
        self.entities = {}
        self.patterns = {}
        self.keywords = {}
        self.trained = False

        # Charger les intentions
        intents_file = intents_file or DEFAULT_INTENTS_FILE
        self._load_intents(intents_file)

        logger.info(f"IntentClassifier initialized with {len(self.intents)} intents")

    def _load_intents(self, intents_file: str) -> None:
        """
        Charge les définitions d'intentions depuis un fichier JSON.

        Args:
            intents_file (str): Chemin vers le fichier de définition des intentions
        """
        try:
            # Vérifier si le fichier existe
            if not os.path.exists(intents_file):
                logger.warning(
                    f"Intents file {intents_file} not found, using default intents"
                )
                self._init_default_intents()
                return

            # Charger le fichier
            with open(intents_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.intents = data.get("intents", {})
            self.entities = data.get("entities", {})

            # Précompiler les expressions régulières pour les intentions
            for intent_name, intent_data in self.intents.items():
                patterns = intent_data.get("patterns", [])
                self.patterns[intent_name] = [
                    re.compile(p, re.IGNORECASE) for p in patterns
                ]

                keywords = intent_data.get("keywords", [])
                self.keywords[intent_name] = set(keywords)

            # Précompiler les expressions régulières pour les entités
            for entity_name, entity_data in self.entities.items():
                patterns = entity_data.get("patterns", [])
                self.entities[entity_name] = {
                    "patterns": [re.compile(p, re.IGNORECASE) for p in patterns],
                    "values": entity_data.get("values", {}),
                    "type": entity_data.get("type", "string"),
                }

            self.trained = True
            logger.info(
                f"Loaded {len(self.intents)} intents and {len(self.entities)} entities from {intents_file}"
            )

        except Exception as e:
            logger.error(f"Error loading intents from {intents_file}: {str(e)}")
            self._init_default_intents()

    def _init_default_intents(self) -> None:
        """
        Initialise des intentions par défaut en cas d'erreur de chargement.
        """
        self.intents = {
            "conversation.greeting": {
                "description": "Salutations",
                "patterns": [
                    r"^(bonjour|salut|hello|hi|hey|coucou|yo|hola)[\s\.,!]*$",
                    r"^(bonsoir|good evening)[\s\.,!]*$",
                ],
                "keywords": [
                    "bonjour",
                    "salut",
                    "hello",
                    "bonsoir",
                    "hey",
                    "coucou",
                    "yo",
                    "hola",
                ],
            },
            "conversation.farewell": {
                "description": "Au revoir",
                "patterns": [
                    r"^(au revoir|bye|ciao|adieu|à bientôt|à plus|à\+)[\s\.,!]*$",
                    r"^(bonne (journée|soirée|nuit))[\s\.,!]*$",
                ],
                "keywords": [
                    "au revoir",
                    "bye",
                    "ciao",
                    "adieu",
                    "bientôt",
                    "plus",
                    "bonne journée",
                    "bonne soirée",
                ],
            },
            "conversation.thanks": {
                "description": "Remerciements",
                "patterns": [
                    r"^(merci|thanks|thank you|je te remercie|je vous remercie)[\s\.,!]*$",
                    r"(merci|thanks|thank you) (beaucoup|bien|infiniment)[\s\.,!]*$",
                ],
                "keywords": ["merci", "thanks", "thank you", "remercie"],
            },
            "conversation.help": {
                "description": "Demande d'aide",
                "patterns": [
                    r"^(aide|help|aidez-moi|besoin d'aide|comment ça marche|aide-moi)[\s\?]*$",
                    r"(que sais-tu faire|quelles sont tes capacités|que peux-tu faire)",
                ],
                "keywords": [
                    "aide",
                    "help",
                    "aidez-moi",
                    "aide-moi",
                    "capacités",
                    "fonctionnalités",
                ],
            },
            "system.status": {
                "description": "Demande de statut",
                "patterns": [
                    r"(quel est ton|quel est|status|statut)",
                    r"(comment te portes-tu|comment vas-tu|ça va)",
                ],
                "keywords": ["statut", "status", "portes-tu", "vas-tu", "ça va"],
            },
        }

        # Précompiler les expressions régulières pour les intentions par défaut
        for intent_name, intent_data in self.intents.items():
            patterns = intent_data.get("patterns", [])
            self.patterns[intent_name] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

            keywords = intent_data.get("keywords", [])
            self.keywords[intent_name] = set(keywords)

        self.trained = True
        logger.info(f"Initialized {len(self.intents)} default intents")

    async def classify(
        self, message: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Classifie un message pour déterminer l'intention de l'utilisateur.

        Args:
            message (str): Le message à classifier
            context (Dict[str, Any], optional): Le contexte de la conversation

        Returns:
            Dict[str, Any]: Les résultats de la classification, incluant l'intention et les entités
        """
        if not self.trained:
            logger.warning("Intent classifier not trained yet")
            return {"intent": FALLBACK_INTENT, "confidence": 1.0, "entities": []}

        # Normaliser le message
        normalized_message = message.strip().lower()

        # Extraire les entités
        entities = self._extract_entities(message)

        # Rechercher une correspondance exacte avec les modèles
        for intent_name, patterns in self.patterns.items():
            for pattern in patterns:
                if pattern.search(normalized_message):
                    logger.debug(f"Pattern match for intent {intent_name}")
                    return {
                        "intent": intent_name,
                        "confidence": 0.95,
                        "entities": entities,
                        "method": "pattern_match",
                    }

        # Si pas de correspondance exacte, utiliser une approche par mots-clés
        intent_scores = {}

        # Diviser le message en mots
        words = set(re.findall(r"\b\w+\b", normalized_message.lower()))

        for intent_name, keywords in self.keywords.items():
            matches = words.intersection(keywords)
            if matches:
                # Calculer un score basé sur le nombre de mots-clés trouvés
                score = len(matches) / len(keywords) if keywords else 0
                intent_scores[intent_name] = min(0.9, score + 0.4)  # Plafonner à 0.9

        # Prendre en compte le contexte si disponible
        if context and "conversation" in context:
            # Si la conversation a une intention récente, augmenter son score
            last_intent = context.get("conversation", {}).get("last_intent")
            if last_intent and last_intent in intent_scores:
                intent_scores[last_intent] *= 1.1  # +10%

            # Si le message est court et semble être une réponse à une question
            if len(words) <= 3 and context.get("conversation", {}).get(
                "waiting_for_response"
            ):
                expected_intent = context.get("conversation", {}).get("expected_intent")
                if expected_intent:
                    intent_scores[expected_intent] = max(
                        intent_scores.get(expected_intent, 0), 0.8
                    )

        # Sélectionner l'intention avec le score le plus élevé
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            logger.debug(
                f"Keyword match for intent {best_intent[0]} with score {best_intent[1]}"
            )
            return {
                "intent": best_intent[0],
                "confidence": best_intent[1],
                "entities": entities,
                "method": "keyword_match",
                "all_scores": intent_scores,
            }

        # Aucune correspondance, utiliser l'intention par défaut
        logger.debug(f"No match found, using fallback intent")
        return {
            "intent": FALLBACK_INTENT,
            "confidence": 1.0,
            "entities": entities,
            "method": "fallback",
        }

    def _extract_entities(self, message: str) -> List[Dict[str, Any]]:
        """
        Extrait les entités du message.

        Args:
            message (str): Le message à analyser

        Returns:
            List[Dict[str, Any]]: Les entités extraites
        """
        entities = []

        # Pour chaque type d'entité
        for entity_name, entity_data in self.entities.items():
            patterns = entity_data.get("patterns", [])

            # Chercher des correspondances avec les modèles
            for pattern in patterns:
                matches = pattern.finditer(message)

                for match in matches:
                    value = match.group(0)

                    # Normaliser la valeur si nécessaire
                    normalized_value = value.lower()

                    # Rechercher une correspondance avec les valeurs connues
                    resolved_value = entity_data.get("values", {}).get(
                        normalized_value, value
                    )

                    # Ajouter l'entité
                    entity = {
                        "type": entity_name,
                        "value": resolved_value,
                        "raw": value,
                        "start": match.start(),
                        "end": match.end(),
                    }

                    entities.append(entity)

        return entities

    async def train(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Entraîne le classificateur avec de nouvelles données.

        Args:
            training_data (Dict[str, Any]): Les données d'entraînement

        Returns:
            Dict[str, Any]: Les résultats de l'entraînement
        """
        start_time = time.time()

        # Mise à jour des intentions
        if "intents" in training_data:
            for intent_name, intent_data in training_data["intents"].items():
                # Mettre à jour ou ajouter l'intention
                if intent_name in self.intents:
                    # Mettre à jour l'intention existante
                    for key, value in intent_data.items():
                        if key == "patterns" or key == "keywords":
                            # Ajouter aux listes existantes
                            self.intents[intent_name][key] = list(
                                set(self.intents[intent_name].get(key, []) + value)
                            )
                        else:
                            # Remplacer les autres champs
                            self.intents[intent_name][key] = value
                else:
                    # Ajouter une nouvelle intention
                    self.intents[intent_name] = intent_data

                # Mettre à jour les modèles compilés
                patterns = self.intents[intent_name].get("patterns", [])
                self.patterns[intent_name] = [
                    re.compile(p, re.IGNORECASE) for p in patterns
                ]

                keywords = self.intents[intent_name].get("keywords", [])
                self.keywords[intent_name] = set(keywords)

        # Mise à jour des entités
        if "entities" in training_data:
            for entity_name, entity_data in training_data["entities"].items():
                # Mettre à jour ou ajouter l'entité
                if entity_name in self.entities:
                    # Mettre à jour l'entité existante
                    for key, value in entity_data.items():
                        if key == "patterns":
                            # Ajouter aux listes existantes
                            patterns = list(
                                set(
                                    self.entities[entity_name].get("patterns", [])
                                    + value
                                )
                            )
                            self.entities[entity_name]["patterns"] = [
                                re.compile(p, re.IGNORECASE) for p in patterns
                            ]
                        elif key == "values":
                            # Fusionner les dictionnaires
                            self.entities[entity_name]["values"] = {
                                **self.entities[entity_name].get("values", {}),
                                **value,
                            }
                        else:
                            # Remplacer les autres champs
                            self.entities[entity_name][key] = value
                else:
                    # Ajouter une nouvelle entité
                    patterns = entity_data.get("patterns", [])
                    self.entities[entity_name] = {
                        "patterns": [re.compile(p, re.IGNORECASE) for p in patterns],
                        "values": entity_data.get("values", {}),
                        "type": entity_data.get("type", "string"),
                    }

        # Marquer comme entraîné
        self.trained = True

        # Calculer les statistiques
        training_time = time.time() - start_time

        return {
            "success": True,
            "training_time": training_time,
            "intents_count": len(self.intents),
            "entities_count": len(self.entities),
            "patterns_count": sum(len(patterns) for patterns in self.patterns.values()),
            "keywords_count": sum(len(keywords) for keywords in self.keywords.values()),
        }


# Créer une instance par défaut
intent_classifier = IntentClassifier()
