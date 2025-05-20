"""
Générateur de réponses pour la conversation
Produit des réponses naturelles et adaptées au contexte
"""

import logging
import json
import os
import re
import random
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple

# Configuration des logs
logger = logging.getLogger("lucie.conversation.response_generator")

# Constantes
DEFAULT_RESPONSES_FILE = os.path.join(
    os.path.dirname(__file__), "data", "responses.json"
)
FALLBACK_RESPONSES = [
    "Je ne suis pas sûre de comprendre. Pouvez-vous reformuler ?",
    "Je ne suis pas certaine de saisir votre demande. Pourriez-vous préciser ?",
    "Pardonnez-moi, mais je n'ai pas bien compris ce que vous attendez de moi.",
    "Je ne suis pas sûre de pouvoir répondre à cela. Pouvez-vous être plus précis ?",
    "Je suis désolée, mais je ne comprends pas bien ce que vous me demandez.",
]


class ResponseGenerator:
    """
    Générateur de réponses basé sur des modèles et templates.
    Produit des réponses adaptées en fonction de l'intention et du contexte.
    """

    def __init__(self, responses_file: str = None):
        """
        Initialise le générateur de réponses.

        Args:
            responses_file (str, optional): Chemin vers le fichier de définition des réponses
        """
        self.responses = {}
        self.templates = {}
        self.trained = False

        # Charger les réponses
        responses_file = responses_file or DEFAULT_RESPONSES_FILE
        self._load_responses(responses_file)

        logger.info(
            f"ResponseGenerator initialized with {len(self.responses)} intent responses"
        )

    def _load_responses(self, responses_file: str) -> None:
        """
        Charge les définitions de réponses depuis un fichier JSON.

        Args:
            responses_file (str): Chemin vers le fichier de définition des réponses
        """
        try:
            # Vérifier si le fichier existe
            if not os.path.exists(responses_file):
                logger.warning(
                    f"Responses file {responses_file} not found, using default responses"
                )
                self._init_default_responses()
                return

            # Charger le fichier
            with open(responses_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.responses = data.get("responses", {})
            self.templates = data.get("templates", {})

            self.trained = True
            logger.info(
                f"Loaded {len(self.responses)} intent responses from {responses_file}"
            )

        except Exception as e:
            logger.error(f"Error loading responses from {responses_file}: {str(e)}")
            self._init_default_responses()

    def _init_default_responses(self) -> None:
        """
        Initialise des réponses par défaut en cas d'erreur de chargement.
        """
        self.responses = {
            "conversation.greeting": {
                "responses": [
                    "Bonjour ! Comment puis-je vous aider aujourd'hui ?",
                    "Bonjour ! Je suis Lucie, votre assistant IA. Que puis-je faire pour vous ?",
                    "Bonjour ! Comment puis-je vous être utile ?",
                    "Bonjour ! Je suis là pour vous aider. Que recherchez-vous ?",
                ]
            },
            "conversation.farewell": {
                "responses": [
                    "Au revoir ! N'hésitez pas à revenir si vous avez besoin d'aide.",
                    "Au revoir ! Passez une excellente journée.",
                    "À bientôt ! Ce fut un plaisir de vous aider.",
                    "Au revoir ! Je serai là si vous avez d'autres questions.",
                ]
            },
            "conversation.thanks": {
                "responses": [
                    "De rien ! Je suis contente d'avoir pu vous aider.",
                    "C'est avec plaisir ! Avez-vous besoin d'autre chose ?",
                    "Je vous en prie, c'est mon rôle de vous assister.",
                    "Pas de problème ! N'hésitez pas si vous avez d'autres questions.",
                ]
            },
            "conversation.help": {
                "responses": [
                    "Je peux vous aider sur divers sujets. Je peux répondre à vos questions, vous fournir des informations, ou vous assister dans vos tâches. Que souhaitez-vous faire ?",
                    "En tant qu'assistant IA, je peux vous aider de plusieurs façons. Je peux répondre à vos questions, faire des recherches pour vous, ou vous aider à organiser vos idées. Comment puis-je vous être utile aujourd'hui ?",
                    "Je suis Lucie, votre assistant personnel. Je peux vous aider en répondant à vos questions, en cherchant des informations, ou en vous assistant dans diverses tâches. Que puis-je faire pour vous ?",
                ]
            },
            "system.status": {
                "responses": [
                    "Je suis opérationnelle et prête à vous aider !",
                    "Tous mes systèmes fonctionnent normalement. Je suis à votre disposition.",
                    "Je suis en parfait état de fonctionnement et prête à vous assister.",
                ]
            },
            "fallback.general": {"responses": FALLBACK_RESPONSES},
        }

        self.templates = {
            "greeting": {
                "morning": "Bonjour, {name} ! Comment puis-je vous aider ce matin ?",
                "afternoon": "Bonjour, {name} ! Comment puis-je vous être utile cet après-midi ?",
                "evening": "Bonsoir, {name} ! Comment puis-je vous assister ce soir ?",
            }
        }

        self.trained = True
        logger.info(f"Initialized {len(self.responses)} default responses")

    async def generate_response(
        self,
        message: str,
        intent: str,
        entities: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Génère une réponse adaptée à l'intention et au contexte.

        Args:
            message (str): Le message original
            intent (str): L'intention reconnue
            entities (List[Dict[str, Any]]): Les entités reconnues
            context (Dict[str, Any]): Le contexte de la conversation

        Returns:
            Dict[str, Any]: La réponse générée avec métadonnées
        """
        if not self.trained:
            logger.warning("Response generator not trained yet")
            return {"response": random.choice(FALLBACK_RESPONSES), "method": "fallback"}

        start_time = time.time()

        # Chercher des réponses pour l'intention
        intent_responses = self.responses.get(intent)

        if not intent_responses:
            # Chercher des réponses pour une catégorie plus générale
            intent_category = intent.split(".")[0] if "." in intent else intent
            intent_responses = self.responses.get(f"{intent_category}.general")

        # Si toujours pas de réponses, utiliser le fallback
        if not intent_responses:
            logger.debug(f"No responses found for intent {intent}, using fallback")
            intent_responses = self.responses.get(
                "fallback.general", {"responses": FALLBACK_RESPONSES}
            )

        # Sélectionner une réponse
        responses_list = intent_responses.get("responses", [])

        if not responses_list:
            return {"response": random.choice(FALLBACK_RESPONSES), "method": "fallback"}

        # Sélectionner une réponse aléatoire
        raw_response = random.choice(responses_list)

        # Vérifier s'il s'agit d'un template
        if raw_response.startswith("@template:"):
            template_name = raw_response.replace("@template:", "").strip()
            raw_response = self._process_template(template_name, entities, context)

        # Traiter les placeholders d'entités
        response = self._replace_entity_placeholders(raw_response, entities)

        # Traiter les placeholders de contexte
        response = self._replace_context_placeholders(response, context)

        # Traiter les placeholders de fonction
        response = self._process_function_calls(response, context)

        # Calculer le temps de génération
        generation_time = time.time() - start_time

        return {
            "response": response,
            "intent": intent,
            "method": "template",
            "generation_time": generation_time,
        }

    def _process_template(
        self,
        template_name: str,
        entities: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> str:
        """
        Traite un template pour générer une réponse.

        Args:
            template_name (str): Nom du template
            entities (List[Dict[str, Any]]): Les entités reconnues
            context (Dict[str, Any]): Le contexte de la conversation

        Returns:
            str: La réponse générée
        """
        # Vérifier si le template existe
        template_parts = template_name.split(".")

        if len(template_parts) < 2:
            logger.warning(f"Invalid template name format: {template_name}")
            return random.choice(FALLBACK_RESPONSES)

        category = template_parts[0]
        subtype = ".".join(template_parts[1:])

        # Récupérer le template
        if category not in self.templates:
            logger.warning(f"Template category not found: {category}")
            return random.choice(FALLBACK_RESPONSES)

        category_templates = self.templates[category]

        if subtype not in category_templates:
            logger.warning(
                f"Template subtype not found: {subtype} in category {category}"
            )
            return random.choice(list(category_templates.values()))

        template = category_templates[subtype]

        # Si le template est une liste, choisir un élément aléatoire
        if isinstance(template, list):
            template = random.choice(template)

        return template

    def _replace_entity_placeholders(
        self, response: str, entities: List[Dict[str, Any]]
    ) -> str:
        """
        Remplace les placeholders d'entités dans la réponse.

        Args:
            response (str): La réponse avec placeholders
            entities (List[Dict[str, Any]]): Les entités reconnues

        Returns:
            str: La réponse avec les placeholders remplacés
        """
        # Créer un dictionnaire d'entités par type
        entities_by_type = {}

        for entity in entities:
            entity_type = entity["type"]
            entity_value = entity["value"]

            if entity_type not in entities_by_type:
                entities_by_type[entity_type] = []

            entities_by_type[entity_type].append(entity_value)

        # Remplacer les placeholders
        updated_response = response

        # Pattern: {entity:type}
        pattern = r"\{entity:([a-zA-Z0-9_.-]+)\}"
        matches = re.findall(pattern, response)

        for entity_type in matches:
            if entity_type in entities_by_type and entities_by_type[entity_type]:
                # Utiliser la première entité du type
                replacement = entities_by_type[entity_type][0]
                updated_response = updated_response.replace(
                    f"{{entity:{entity_type}}}", str(replacement)
                )

        return updated_response

    def _replace_context_placeholders(
        self, response: str, context: Dict[str, Any]
    ) -> str:
        """
        Remplace les placeholders de contexte dans la réponse.

        Args:
            response (str): La réponse avec placeholders
            context (Dict[str, Any]): Le contexte de la conversation

        Returns:
            str: La réponse avec les placeholders remplacés
        """
        # Pattern: {context:path.to.value}
        pattern = r"\{context:([a-zA-Z0-9_.-]+)\}"
        matches = re.findall(pattern, response)

        updated_response = response

        for path in matches:
            # Diviser le chemin en parties
            parts = path.split(".")

            # Naviguer dans le contexte
            value = context
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    value = None
                    break

            # Remplacer le placeholder s'il y a une valeur
            if value is not None:
                updated_response = updated_response.replace(
                    f"{{context:{path}}}", str(value)
                )

        return updated_response

    def _process_function_calls(self, response: str, context: Dict[str, Any]) -> str:
        """
        Traite les appels de fonction dans la réponse.

        Args:
            response (str): La réponse avec appels de fonction
            context (Dict[str, Any]): Le contexte de la conversation

        Returns:
            str: La réponse avec les résultats des fonctions
        """
        # Pattern: {function:name(param1,param2)}
        pattern = r"\{function:([a-zA-Z0-9_]+)\(([^)]*)\)\}"
        matches = re.findall(pattern, response)

        updated_response = response

        for function_name, params_str in matches:
            # Séparer les paramètres
            params = [p.strip() for p in params_str.split(",")] if params_str else []

            # Appeler la fonction appropriée
            result = ""

            if function_name == "time":
                result = self._function_time(params)
            elif function_name == "date":
                result = self._function_date(params)
            elif function_name == "random":
                result = self._function_random(params)
            elif function_name == "count":
                result = self._function_count(params, context)

            # Remplacer l'appel de fonction par le résultat
            updated_response = updated_response.replace(
                f"{{function:{function_name}({params_str})}}", result
            )

        return updated_response

    def _function_time(self, params: List[str]) -> str:
        """
        Fonction pour obtenir l'heure actuelle.

        Args:
            params (List[str]): Paramètres de la fonction

        Returns:
            str: L'heure actuelle formatée
        """
        now = datetime.now()
        format_str = params[0] if params else "%H:%M"

        try:
            return now.strftime(format_str)
        except:
            return now.strftime("%H:%M")

    def _function_date(self, params: List[str]) -> str:
        """
        Fonction pour obtenir la date actuelle.

        Args:
            params (List[str]): Paramètres de la fonction

        Returns:
            str: La date actuelle formatée
        """
        now = datetime.now()
        format_str = params[0] if params else "%d/%m/%Y"

        try:
            return now.strftime(format_str)
        except:
            return now.strftime("%d/%m/%Y")

    def _function_random(self, params: List[str]) -> str:
        """
        Fonction pour obtenir un élément aléatoire.

        Args:
            params (List[str]): Paramètres de la fonction (liste d'éléments)

        Returns:
            str: Un élément aléatoire
        """
        if not params:
            return ""

        return random.choice(params)

    def _function_count(self, params: List[str], context: Dict[str, Any]) -> str:
        """
        Fonction pour compter des éléments dans le contexte.

        Args:
            params (List[str]): Paramètres de la fonction (chemin dans le contexte)
            context (Dict[str, Any]): Le contexte de la conversation

        Returns:
            str: Le nombre d'éléments
        """
        if not params:
            return "0"

        path = params[0]
        parts = path.split(".")

        # Naviguer dans le contexte
        value = context
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                value = None
                break

        # Compter les éléments
        if isinstance(value, list):
            return str(len(value))
        elif isinstance(value, dict):
            return str(len(value))
        else:
            return "0"

    async def train(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Entraîne le générateur avec de nouvelles données.

        Args:
            training_data (Dict[str, Any]): Les données d'entraînement

        Returns:
            Dict[str, Any]: Les résultats de l'entraînement
        """
        start_time = time.time()

        # Mise à jour des réponses
        if "responses" in training_data:
            for intent, responses_data in training_data["responses"].items():
                # Mettre à jour ou ajouter les réponses
                if intent in self.responses:
                    # Mettre à jour les réponses existantes
                    if "responses" in responses_data:
                        self.responses[intent]["responses"] = list(
                            set(
                                self.responses[intent].get("responses", [])
                                + responses_data["responses"]
                            )
                        )

                    # Mettre à jour les autres champs
                    for key, value in responses_data.items():
                        if key != "responses":
                            self.responses[intent][key] = value
                else:
                    # Ajouter de nouvelles réponses
                    self.responses[intent] = responses_data

        # Mise à jour des templates
        if "templates" in training_data:
            for category, templates in training_data["templates"].items():
                if category in self.templates:
                    # Fusionner les templates existants
                    self.templates[category].update(templates)
                else:
                    # Ajouter de nouveaux templates
                    self.templates[category] = templates

        # Marquer comme entraîné
        self.trained = True

        # Calculer les statistiques
        training_time = time.time() - start_time

        return {
            "success": True,
            "training_time": training_time,
            "responses_count": sum(
                len(r.get("responses", [])) for r in self.responses.values()
            ),
            "intents_count": len(self.responses),
            "templates_count": sum(len(t) for t in self.templates.values()),
        }


# Créer une instance par défaut
response_generator = ResponseGenerator()
