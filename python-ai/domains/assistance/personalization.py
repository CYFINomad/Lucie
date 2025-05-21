"""
Module de personnalisation pour Lucie
Permet d'adapter les interactions et suggestions en fonction des préférences et habitudes de l'utilisateur
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import json
import re

# Configuration des logs
logger = logging.getLogger("lucie.assistance.personalization")


class Personalization:
    """
    Gère la personnalisation des interactions et suggestions de Lucie.
    Analyse les préférences utilisateur, les habitudes et adapte les réponses en conséquence.
    """

    def __init__(self):
        """Initialise le gestionnaire de personnalisation."""
        logger.info("Personalization module initialized")
        self.preference_cache = {}

    def build_user_profile(self, user_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construit un profil utilisateur basé sur l'historique d'interactions.

        Args:
            user_history (Dict[str, Any]): Historique des interactions avec l'utilisateur

        Returns:
            Dict[str, Any]: Profil utilisateur avec préférences et habitudes
        """
        profile = {
            "preferences": {},
            "interaction_patterns": {},
            "expertise_levels": {},
            "last_updated": datetime.now().isoformat(),
        }

        # Extraction des messages
        messages = user_history.get("conversation", {}).get("messages", [])

        # Analyse des préférences explicites
        explicit_preferences = self._extract_explicit_preferences(messages)
        if explicit_preferences:
            profile["preferences"].update(explicit_preferences)

        # Analyse des préférences implicites basées sur les interactions
        implicit_preferences = self._analyze_implicit_preferences(
            messages, user_history
        )
        if implicit_preferences:
            # Fusionner avec les préférences explicites en donnant priorité aux explicites
            for category, prefs in implicit_preferences.items():
                if category not in profile["preferences"]:
                    profile["preferences"][category] = {}

                for key, value in prefs.items():
                    # Ne pas écraser les préférences explicites
                    if (
                        category not in profile["preferences"]
                        or key not in profile["preferences"][category]
                    ):
                        profile["preferences"][category][key] = value

        # Analyse des modèles d'interaction
        interaction_patterns = self._analyze_interaction_patterns(messages)
        profile["interaction_patterns"] = interaction_patterns

        # Estimation des niveaux d'expertise
        expertise_levels = self._estimate_expertise_levels(messages, user_history)
        profile["expertise_levels"] = expertise_levels

        return profile

    def _extract_explicit_preferences(
        self, messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extrait les préférences explicitement mentionnées par l'utilisateur.

        Args:
            messages (List[Dict[str, Any]]): Historique des messages

        Returns:
            Dict[str, Any]: Préférences explicites structurées
        """
        preferences = {"communication": {}, "content": {}, "ui": {}, "notification": {}}

        # Modèles pour la détection de préférences explicites
        preference_patterns = {
            "communication": {
                "verbosity": r"(?:je|j'|préfère).*?(concis|détaillé|court|long|bref)",
                "formality": r"(?:je|j'|préfère).*?(formel|informel|tutoiement|vouvoiement)",
                "language": r"(?:je|j'|préfère).*?(?:parl|communi).*?(français|anglais|espagnol)",
            },
            "content": {
                "detail_level": r"(?:je|j'|préfère).*?(superficiel|détaillé|approfondi)",
                "examples": r"(?:je|j'|préfère).*?(avec|sans).*?exemples",
            },
            "ui": {
                "theme": r"(?:je|j'|préfère).*?(?:thème|mode).*?(sombre|clair|dark|light)",
                "layout": r"(?:je|j'|préfère).*?(?:interface|disposition).*?(compacte|étendue)",
            },
            "notification": {
                "frequency": r"(?:je|j'|préfère).*?notif.*?(peu|beaucoup|rarement|jamais)"
            },
        }

        # Analyser uniquement les messages de l'utilisateur
        user_messages = [msg for msg in messages if msg.get("role") == "user"]

        for message in user_messages:
            content = message.get("content", "").lower()

            # Chercher les correspondances de préférences dans chaque catégorie
            for category, patterns in preference_patterns.items():
                for pref_key, pattern in patterns.items():
                    matches = re.search(pattern, content)
                    if matches:
                        # Extraire et traiter la valeur de préférence
                        value = matches.group(1)

                        # Normaliser certaines valeurs
                        if pref_key == "verbosity":
                            if value in ["concis", "court", "bref"]:
                                value = "concise"
                            elif value in ["détaillé", "long"]:
                                value = "detailed"
                        elif pref_key == "formality":
                            if value in ["informel", "tutoiement"]:
                                value = "informal"
                            elif value in ["formel", "vouvoiement"]:
                                value = "formal"

                        # Stocker la préférence
                        preferences[category][pref_key] = {
                            "value": value,
                            "confidence": 0.9,  # Haute confiance car explicitement indiqué
                            "timestamp": message.get(
                                "timestamp", datetime.now().isoformat()
                            ),
                        }

        # Filtrer les catégories vides
        return {k: v for k, v in preferences.items() if v}

    def _analyze_implicit_preferences(
        self, messages: List[Dict[str, Any]], user_history: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyse les préférences implicites basées sur les comportements observés.

        Args:
            messages (List[Dict[str, Any]]): Historique des messages
            user_history (Dict[str, Any]): Historique utilisateur complet

        Returns:
            Dict[str, Dict[str, Any]]: Préférences implicites avec niveau de confiance
        """
        preferences = {"communication": {}, "content": {}, "timing": {}, "topics": {}}

        # Filtrer les messages utilisateur
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if not user_messages:
            return preferences

        # Analyser la verbosité préférée en fonction des réponses appréciées
        message_lengths = [len(msg.get("content", "")) for msg in user_messages]
        avg_message_length = (
            sum(message_lengths) / len(message_lengths) if message_lengths else 0
        )

        if avg_message_length < 50:
            preferences["communication"]["verbosity"] = {
                "value": "concise",
                "confidence": 0.7,
                "timestamp": datetime.now().isoformat(),
            }
        elif avg_message_length > 150:
            preferences["communication"]["verbosity"] = {
                "value": "detailed",
                "confidence": 0.7,
                "timestamp": datetime.now().isoformat(),
            }

        # Analyser les moments d'utilisation préférés
        usage_times = []
        for msg in user_messages:
            if "timestamp" in msg:
                timestamp = datetime.fromisoformat(msg["timestamp"])
                usage_times.append(timestamp.hour)

        if usage_times:
            # Identifier la période la plus active
            morning_count = sum(1 for t in usage_times if 5 <= t < 12)
            afternoon_count = sum(1 for t in usage_times if 12 <= t < 18)
            evening_count = sum(1 for t in usage_times if 18 <= t < 22)
            night_count = sum(1 for t in usage_times if t >= 22 or t < 5)

            periods = {
                "morning": morning_count,
                "afternoon": afternoon_count,
                "evening": evening_count,
                "night": night_count,
            }

            # Trouver la période la plus active
            most_active_period = max(periods.items(), key=lambda x: x[1])
            if most_active_period[1] > 0:
                preferences["timing"]["preferred_period"] = {
                    "value": most_active_period[0],
                    "confidence": min(
                        0.6, 0.3 + (most_active_period[1] / len(usage_times)) * 0.5
                    ),
                    "timestamp": datetime.now().isoformat(),
                }

        # Analyser les sujets fréquemment abordés
        content_all = " ".join(
            [msg.get("content", "") for msg in user_messages]
        ).lower()

        # Mots-clés par catégorie de sujet
        topic_keywords = {
            "technology": [
                "technologie",
                "code",
                "programme",
                "développement",
                "web",
                "application",
                "système",
            ],
            "business": [
                "business",
                "entreprise",
                "projet",
                "client",
                "réunion",
                "stratégie",
                "objectif",
            ],
            "science": [
                "science",
                "recherche",
                "étude",
                "analyse",
                "données",
                "résultat",
                "expérience",
            ],
            "entertainment": [
                "film",
                "série",
                "musique",
                "jeu",
                "livre",
                "lecture",
                "loisir",
            ],
        }

        topic_scores = {}
        for topic, keywords in topic_keywords.items():
            score = 0
            for keyword in keywords:
                matches = re.findall(r"\b" + keyword + r"\b", content_all)
                score += len(matches)

            if score > 0:
                topic_scores[topic] = score

        # Identifier les sujets les plus fréquents
        if topic_scores:
            total_mentions = sum(topic_scores.values())
            for topic, score in topic_scores.items():
                if (
                    score / total_mentions > 0.2
                ):  # Seuil minimal pour considérer comme préférence
                    preferences["topics"][topic] = {
                        "value": "interested",
                        "score": score / total_mentions,
                        "confidence": min(0.8, 0.4 + (score / total_mentions) * 0.6),
                        "timestamp": datetime.now().isoformat(),
                    }

        return preferences

    def _analyze_interaction_patterns(
        self, messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyse les modèles d'interaction pour comprendre les habitudes de communication.

        Args:
            messages (List[Dict[str, Any]]): Historique des messages

        Returns:
            Dict[str, Any]: Modèles d'interaction détectés
        """
        patterns = {
            "response_time": None,
            "session_duration": None,
            "question_frequency": 0.0,
            "command_frequency": 0.0,
            "dialogue_style": None,
        }

        if not messages:
            return patterns

        # Filtrer les messages utilisateur
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if not user_messages:
            return patterns

        # Analyser les temps de réponse
        response_times = []
        last_assistant_time = None

        for msg in messages:
            if "timestamp" not in msg:
                continue

            current_time = datetime.fromisoformat(msg["timestamp"])

            if msg.get("role") == "assistant":
                last_assistant_time = current_time
            elif msg.get("role") == "user" and last_assistant_time:
                # Calculer le temps de réponse de l'utilisateur
                response_time = (current_time - last_assistant_time).total_seconds()
                if 0 < response_time < 3600:  # Ignorer les temps de réponse > 1h
                    response_times.append(response_time)

        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            patterns["response_time"] = {
                "average_seconds": avg_response_time,
                "samples": len(response_times),
            }

        # Analyser la fréquence des questions vs commandes
        question_count = 0
        command_count = 0

        for msg in user_messages:
            content = msg.get("content", "")
            if content.endswith("?") or re.search(
                r"\b(quoi|comment|pourquoi|quand|où|qui)\b", content.lower()
            ):
                question_count += 1
            elif re.search(
                r"\b(fais|montre|affiche|cherche|trouve|crée|lance)\b", content.lower()
            ):
                command_count += 1

        total_count = len(user_messages)
        if total_count > 0:
            patterns["question_frequency"] = question_count / total_count
            patterns["command_frequency"] = command_count / total_count

            # Déterminer le style de dialogue dominant
            if patterns["question_frequency"] > 0.6:
                patterns["dialogue_style"] = "inquisitive"
            elif patterns["command_frequency"] > 0.6:
                patterns["dialogue_style"] = "directive"
            elif (
                patterns["question_frequency"] > 0.3
                and patterns["command_frequency"] > 0.3
            ):
                patterns["dialogue_style"] = "balanced"
            else:
                patterns["dialogue_style"] = "conversational"

        return patterns

    def _estimate_expertise_levels(
        self, messages: List[Dict[str, Any]], user_history: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Estime le niveau d'expertise de l'utilisateur dans différents domaines.

        Args:
            messages (List[Dict[str, Any]]): Historique des messages
            user_history (Dict[str, Any]): Historique utilisateur complet

        Returns:
            Dict[str, Any]: Niveaux d'expertise estimés par domaine
        """
        expertise = {
            "technology": {"level": "beginner", "confidence": 0.5},
            "business": {"level": "beginner", "confidence": 0.5},
            "science": {"level": "beginner", "confidence": 0.5},
        }

        # Filtrer les messages utilisateur
        user_messages = [msg for msg in messages if msg.get("role") == "user"]
        if not user_messages:
            return expertise

        # Indicateurs de niveau d'expertise par domaine
        expertise_indicators = {
            "technology": {
                "beginner": [
                    "comment",
                    "aide",
                    "explique",
                    "simplement",
                    "base",
                    "débutant",
                ],
                "intermediate": ["optimiser", "améliorer", "problème", "erreur", "bug"],
                "expert": [
                    "architecture",
                    "paradigme",
                    "conception",
                    "complexité",
                    "algorithme",
                ],
            },
            "business": {
                "beginner": [
                    "comment",
                    "aide",
                    "explique",
                    "simplement",
                    "base",
                    "débutant",
                ],
                "intermediate": ["stratégie", "objectif", "performance", "rentabilité"],
                "expert": ["acquisition", "fusion", "scaling", "investissement", "ROI"],
            },
            "science": {
                "beginner": [
                    "comment",
                    "aide",
                    "explique",
                    "simplement",
                    "base",
                    "débutant",
                ],
                "intermediate": [
                    "analyse",
                    "méthode",
                    "résultat",
                    "données",
                    "interprétation",
                ],
                "expert": [
                    "hypothèse",
                    "significativité",
                    "causalité",
                    "corrélation",
                    "méthodologie",
                ],
            },
        }

        # Analyser tous les messages utilisateur
        content_all = " ".join(
            [msg.get("content", "") for msg in user_messages]
        ).lower()

        for domain, levels in expertise_indicators.items():
            # Calculer les scores pour chaque niveau
            level_scores = {}
            for level, indicators in levels.items():
                score = 0
                for indicator in indicators:
                    matches = re.findall(r"\b" + indicator + r"\b", content_all)
                    score += len(matches)
                level_scores[level] = score

            # Déterminer le niveau le plus probable
            if sum(level_scores.values()) > 0:
                max_level = max(level_scores.items(), key=lambda x: x[1])
                total_mentions = sum(level_scores.values())
                confidence = min(0.9, 0.5 + (max_level[1] / total_mentions) * 0.5)

                # Mettre à jour seulement si le score est significatif
                if max_level[1] > 2:
                    expertise[domain] = {
                        "level": max_level[0],
                        "confidence": confidence,
                    }

        # Estimer l'ancienneté dans le domaine technologique si possible
        tech_expertise = expertise.get("technology", {})
        tech_level = tech_expertise.get("level", "beginner")

        # Ajuster l'expertise technologique en fonction des intents technologiques
        intent_history = user_history.get("conversation", {}).get("intent_history", [])
        tech_intents = [
            intent
            for intent in intent_history
            if intent.get("intent", "").startswith("tech.")
        ]

        if tech_intents and tech_level == "beginner" and len(tech_intents) > 5:
            # Réévaluer si beaucoup d'intents technologiques mais niveau débutant
            expertise["technology"]["level"] = "intermediate"
            expertise["technology"]["confidence"] = 0.6

        return expertise

    def adapt_response(self, response: str, user_profile: Dict[str, Any]) -> str:
        """
        Adapte une réponse générée en fonction du profil utilisateur.

        Args:
            response (str): Réponse originale
            user_profile (Dict[str, Any]): Profil utilisateur avec préférences

        Returns:
            str: Réponse adaptée aux préférences de l'utilisateur
        """
        adapted_response = response

        # Obtenir les préférences pertinentes
        preferences = user_profile.get("preferences", {})
        comm_prefs = preferences.get("communication", {})

        # Adapter la verbosité
        verbosity = (
            comm_prefs.get("verbosity", {}).get("value")
            if isinstance(comm_prefs.get("verbosity"), dict)
            else None
        )
        if verbosity == "concise" and len(response) > 300:
            # Réduire la verbosité
            # Supprimer les informations secondaires et les phrases d'introduction courantes
            adapted_response = re.sub(
                r"(Pour information|À titre d'information|En outre|Par ailleurs)[^.]*\.",
                "",
                adapted_response,
            )
            adapted_response = re.sub(
                r"(Je vous suggère|Je vous recommande)", "Suggestion:", adapted_response
            )
            adapted_response = re.sub(r"N'hésitez pas à [^.]*\.", "", adapted_response)

        elif verbosity == "detailed" and len(response) < 200:
            # Conserver la réponse telle quelle, car la génération détaillée nécessiterait
            # des informations supplémentaires spécifiques au contexte
            pass

        # Adapter la formalité
        formality = (
            comm_prefs.get("formality", {}).get("value")
            if isinstance(comm_prefs.get("formality"), dict)
            else None
        )
        if formality == "informal":
            # Rendre la réponse plus informelle
            adapted_response = adapted_response.replace("vous", "tu")
            adapted_response = adapted_response.replace("Vous", "Tu")
            adapted_response = adapted_response.replace("votre", "ton")
            adapted_response = adapted_response.replace("Votre", "Ton")
            adapted_response = adapted_response.replace("vos", "tes")
            adapted_response = adapted_response.replace("Vos", "Tes")

        elif formality == "formal":
            # Rendre la réponse plus formelle
            adapted_response = adapted_response.replace("tu", "vous")
            adapted_response = adapted_response.replace("Tu", "Vous")
            adapted_response = adapted_response.replace("ton", "votre")
            adapted_response = adapted_response.replace("Ton", "Votre")
            adapted_response = adapted_response.replace("tes", "vos")
            adapted_response = adapted_response.replace("Tes", "Vos")

        # Adapter en fonction du niveau d'expertise
        expertise_levels = user_profile.get("expertise_levels", {})
        tech_expertise = expertise_levels.get("technology", {}).get("level", "beginner")

        if "technology" in adapted_response.lower() and tech_expertise == "expert":
            # Supprimer les explications de base pour les experts
            adapted_response = re.sub(
                r"(C'est-à-dire|En d'autres termes|Cela signifie que)[^.]*\.",
                "",
                adapted_response,
            )

        return adapted_response

    def get_user_preferences(
        self, user_id: str, category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Récupère les préférences d'un utilisateur.

        Args:
            user_id (str): Identifiant de l'utilisateur
            category (Optional[str]): Catégorie de préférence spécifique à récupérer

        Returns:
            Dict[str, Any]: Préférences utilisateur
        """
        # Vérifier si les préférences sont en cache
        cache_key = f"{user_id}_{category if category else 'all'}"
        if cache_key in self.preference_cache:
            cached_data = self.preference_cache[cache_key]
            if cached_data["timestamp"] > datetime.now() - timedelta(minutes=30):
                return cached_data["data"]

        # Simuler la récupération depuis une base de données
        # Dans une implémentation réelle, cela ferait appel à une base de données
        preferences = {
            "communication": {
                "verbosity": {"value": "balanced", "confidence": 0.5},
                "formality": {"value": "formal", "confidence": 0.5},
            },
            "content": {"detail_level": {"value": "balanced", "confidence": 0.5}},
            "ui": {"theme": {"value": "system", "confidence": 0.5}},
        }

        # Mettre en cache
        self.preference_cache[cache_key] = {
            "data": preferences.get(category, preferences) if category else preferences,
            "timestamp": datetime.now(),
        }

        return preferences.get(category, preferences) if category else preferences

    def update_user_preference(
        self, user_id: str, category: str, key: str, value: Any
    ) -> bool:
        """
        Met à jour une préférence utilisateur spécifique.

        Args:
            user_id (str): Identifiant de l'utilisateur
            category (str): Catégorie de préférence
            key (str): Clé de préférence
            value (Any): Nouvelle valeur

        Returns:
            bool: True si la mise à jour a réussi
        """
        # Dans une implémentation réelle, mettrait à jour la base de données
        logger.info(
            f"Updating preference for user {user_id}: {category}.{key} = {value}"
        )

        # Invalider le cache
        for cache_key in list(self.preference_cache.keys()):
            if cache_key.startswith(user_id):
                del self.preference_cache[cache_key]

        return True
