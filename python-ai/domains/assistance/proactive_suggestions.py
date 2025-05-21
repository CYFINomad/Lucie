"""
Module de suggestions proactives pour Lucie
Permet à Lucie d'anticiper les besoins utilisateur et de fournir des suggestions pertinentes de manière proactive
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import re
import random

# Configuration des logs
logger = logging.getLogger("lucie.assistance.proactive_suggestions")


class ProactiveSuggestions:
    """
    Gère les suggestions proactives de Lucie.
    Permet d'anticiper les besoins utilisateur et de formuler des propositions pertinentes
    avant même que l'utilisateur n'en fasse la demande explicite.
    """

    def __init__(self, suggestion_threshold: float = 0.65):
        """
        Initialise le gestionnaire de suggestions proactives.

        Args:
            suggestion_threshold (float): Seuil de confiance pour déclencher une suggestion
        """
        self.suggestion_threshold = suggestion_threshold
        logger.info(
            "ProactiveSuggestions initialized with threshold: %f", suggestion_threshold
        )

        # Cache pour limiter la fréquence des suggestions
        self.suggestion_history = {}

    def generate_suggestions(
        self, user_context: Dict[str, Any], user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Génère des suggestions proactives en fonction du contexte et du profil utilisateur.

        Args:
            user_context (Dict[str, Any]): Contexte utilisateur actuel
            user_profile (Dict[str, Any]): Profil de l'utilisateur

        Returns:
            List[Dict[str, Any]]: Liste de suggestions proactives
        """
        suggestions = []

        # Obtenir l'identifiant utilisateur
        user_id = user_context.get("user", {}).get("id", "default_user")

        # Vérifier si nous avons fait des suggestions récemment
        if self._check_suggestion_rate_limit(user_id):
            return []

        # Analyser les opportunités de suggestions
        time_based_suggestions = self._generate_time_based_suggestions(user_context)
        context_based_suggestions = self._generate_context_based_suggestions(
            user_context, user_profile
        )
        pattern_based_suggestions = self._generate_pattern_based_suggestions(
            user_context, user_profile
        )

        # Fusionner toutes les suggestions
        all_suggestions = (
            time_based_suggestions
            + context_based_suggestions
            + pattern_based_suggestions
        )

        # Filtrer les suggestions par score de pertinence
        relevant_suggestions = [
            s for s in all_suggestions if s.get("score", 0) >= self.suggestion_threshold
        ]

        # Limiter le nombre de suggestions pour ne pas submerger l'utilisateur
        if len(relevant_suggestions) > 3:
            # Prioriser les suggestions avec les scores les plus élevés
            relevant_suggestions.sort(key=lambda x: x.get("score", 0), reverse=True)
            suggestions = relevant_suggestions[:3]
        else:
            suggestions = relevant_suggestions

        # Enregistrer l'historique des suggestions
        if suggestions:
            self._update_suggestion_history(user_id, suggestions)

        return suggestions

    def _check_suggestion_rate_limit(self, user_id: str) -> bool:
        """
        Vérifie si nous avons atteint la limite de fréquence des suggestions.

        Args:
            user_id (str): Identifiant de l'utilisateur

        Returns:
            bool: True si nous devons limiter les suggestions, False sinon
        """
        now = datetime.now()

        # Récupérer l'historique des suggestions pour cet utilisateur
        history = self.suggestion_history.get(
            user_id, {"last_suggestion": now - timedelta(hours=2), "count": 0}
        )

        # Limiter à une suggestion toutes les 15 minutes
        time_since_last = (now - history["last_suggestion"]).total_seconds() / 60

        # Limiter aussi le nombre total sur une période (ex: max 10 suggestions par heure)
        if time_since_last < 15:
            return True

        # Si plus de 10 suggestions ont été faites dans la dernière heure, limiter davantage
        if history.get("count", 0) > 10:
            # Vérifier si 1 heure s'est écoulée depuis la première suggestion
            first_suggestion_time = history.get(
                "first_suggestion_time", now - timedelta(hours=2)
            )
            time_since_first = (now - first_suggestion_time).total_seconds() / 3600

            if time_since_first < 1:
                return True

        return False

    def _update_suggestion_history(
        self, user_id: str, suggestions: List[Dict[str, Any]]
    ):
        """
        Met à jour l'historique des suggestions pour un utilisateur.

        Args:
            user_id (str): Identifiant de l'utilisateur
            suggestions (List[Dict[str, Any]]): Suggestions générées
        """
        now = datetime.now()

        if user_id not in self.suggestion_history:
            self.suggestion_history[user_id] = {
                "count": 0,
                "first_suggestion_time": now,
                "suggestions": [],
            }

        history = self.suggestion_history[user_id]

        # Réinitialiser le compteur et l'heure de début si plus d'une heure s'est écoulée
        first_suggestion_time = history.get(
            "first_suggestion_time", now - timedelta(hours=2)
        )
        if (now - first_suggestion_time).total_seconds() / 3600 >= 1:
            history["count"] = 0
            history["first_suggestion_time"] = now

        # Mettre à jour les informations
        history["last_suggestion"] = now
        history["count"] += len(suggestions)

        # Stocker les suggestions récentes (limité aux 10 dernières)
        recent_suggestions = history.get("suggestions", [])
        for suggestion in suggestions:
            recent_suggestions.append(
                {
                    "type": suggestion.get("type"),
                    "timestamp": now.isoformat(),
                    "score": suggestion.get("score"),
                }
            )

        history["suggestions"] = recent_suggestions[-10:]

    def _generate_time_based_suggestions(
        self, user_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Génère des suggestions basées sur l'heure actuelle et le contexte temporel.

        Args:
            user_context (Dict[str, Any]): Contexte utilisateur actuel

        Returns:
            List[Dict[str, Any]]: Suggestions basées sur le temps
        """
        suggestions = []

        # Obtenir le contexte temporel
        time_context = user_context.get("time_context", {})

        if not time_context:
            return suggestions

        period = time_context.get("period")
        weekday = time_context.get("weekday")
        is_weekend = time_context.get("is_weekend", False)

        # Suggestions matinales
        if period in ["morning_early", "morning_late"]:
            # Suggestion de planification en début de journée
            suggestions.append(
                {
                    "type": "planning",
                    "title": "Organiser votre journée",
                    "content": "Voulez-vous que je vous aide à planifier votre journée ?",
                    "action": "plan_day",
                    "score": 0.75 if period == "morning_early" else 0.65,
                }
            )

            # Suggestion de résumé des tâches en cours (plus pertinent en semaine)
            if not is_weekend:
                suggestions.append(
                    {
                        "type": "task_summary",
                        "title": "Résumé des tâches",
                        "content": "Souhaitez-vous un résumé de vos tâches en cours ?",
                        "action": "show_tasks",
                        "score": 0.70,
                    }
                )

        # Suggestions de fin de journée
        elif period in ["evening", "night"]:
            # Suggestion de résumé de la journée
            suggestions.append(
                {
                    "type": "day_summary",
                    "title": "Résumé de votre journée",
                    "content": "Voulez-vous que je vous présente un résumé de votre journée ?",
                    "action": "summarize_day",
                    "score": 0.75 if period == "evening" else 0.60,
                }
            )

            # Suggestion de planification pour demain
            suggestions.append(
                {
                    "type": "tomorrow_planning",
                    "title": "Préparer demain",
                    "content": "Souhaitez-vous préparer votre journée de demain ?",
                    "action": "plan_tomorrow",
                    "score": 0.70 if weekday not in ["friday", "saturday"] else 0.50,
                }
            )

        # Suggestions pour le déjeuner
        elif period == "lunch":
            # Suggestion de pause
            suggestions.append(
                {
                    "type": "break_reminder",
                    "title": "Pause déjeuner",
                    "content": "C'est l'heure du déjeuner. Souhaitez-vous que je vous aide à trouver un restaurant ?",
                    "action": "find_restaurant",
                    "score": 0.65,
                }
            )

        return suggestions

    def _generate_context_based_suggestions(
        self, user_context: Dict[str, Any], user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Génère des suggestions basées sur le contexte utilisateur actuel.

        Args:
            user_context (Dict[str, Any]): Contexte utilisateur actuel
            user_profile (Dict[str, Any]): Profil de l'utilisateur

        Returns:
            List[Dict[str, Any]]: Suggestions basées sur le contexte
        """
        suggestions = []

        # Récupérer le contexte principal
        primary_context = user_context.get("primary_context")

        if not primary_context:
            return suggestions

        # Récupérer les préférences pertinentes
        preferences = user_profile.get("preferences", {})
        topics = preferences.get("topics", {})

        # Suggestions basées sur le contexte de travail
        if primary_context == "work":
            # Suggestion d'aide à la productivité
            suggestions.append(
                {
                    "type": "productivity",
                    "title": "Améliorer votre productivité",
                    "content": "Je peux vous aider à optimiser votre flux de travail. Voulez-vous des conseils ?",
                    "action": "productivity_tips",
                    "score": 0.70,
                }
            )

            # Suggestion de rappel de réunions
            conversation = user_context.get("conversation", {})
            if "réunion" in conversation.get("last_user_message", "").lower():
                suggestions.append(
                    {
                        "type": "meeting_reminder",
                        "title": "Rappel de réunion",
                        "content": "Souhaitez-vous que je vous rappelle les détails de vos prochaines réunions ?",
                        "action": "show_meetings",
                        "score": 0.85,
                    }
                )

        # Suggestions basées sur le contexte de recherche
        elif primary_context == "research":
            # Suggestion d'aide à la recherche
            suggestions.append(
                {
                    "type": "research_assistance",
                    "title": "Aide à la recherche",
                    "content": "Je peux vous aider à trouver des informations supplémentaires. Que recherchez-vous ?",
                    "action": "assist_research",
                    "score": 0.75,
                }
            )

            # Suggestion de recommandation de sources
            if (
                "technology" in topics
                and topics["technology"].get("value") == "interested"
            ):
                suggestions.append(
                    {
                        "type": "tech_resources",
                        "title": "Ressources technologiques",
                        "content": "Voulez-vous que je vous recommande des sources d'information technologique ?",
                        "action": "recommend_tech_resources",
                        "score": 0.80,
                    }
                )

        # Suggestions basées sur le contexte de divertissement
        elif primary_context == "entertainment":
            # Suggestion de recommandations
            suggestions.append(
                {
                    "type": "entertainment_recommendations",
                    "title": "Recommandations personnalisées",
                    "content": "Puis-je vous suggérer du contenu de divertissement en fonction de vos goûts ?",
                    "action": "recommend_entertainment",
                    "score": 0.75,
                }
            )

        # Suggestions basées sur le contexte de planification
        elif primary_context == "planning":
            # Suggestion d'aide à l'organisation
            suggestions.append(
                {
                    "type": "organization_help",
                    "title": "Aide à l'organisation",
                    "content": "Je peux vous aider à mieux organiser vos tâches et rendez-vous. Intéressé(e) ?",
                    "action": "organize_schedule",
                    "score": 0.80,
                }
            )

            # Suggestion de rappel de deadlines
            suggestions.append(
                {
                    "type": "deadline_reminder",
                    "title": "Rappel d'échéances",
                    "content": "Souhaitez-vous que je vous rappelle vos prochaines échéances importantes ?",
                    "action": "show_deadlines",
                    "score": 0.75,
                }
            )

        # Suggestions basées sur le contexte d'apprentissage
        elif primary_context == "learning":
            # Suggestion de ressources d'apprentissage
            suggestions.append(
                {
                    "type": "learning_resources",
                    "title": "Ressources d'apprentissage",
                    "content": "Je peux vous suggérer des ressources pour approfondir vos connaissances. Intéressé(e) ?",
                    "action": "suggest_learning_resources",
                    "score": 0.80,
                }
            )

        # Suggestions basées sur le contexte technique
        elif primary_context == "technical":
            # Suggestion d'aide technique
            suggestions.append(
                {
                    "type": "technical_assistance",
                    "title": "Assistance technique",
                    "content": "Je peux vous aider à résoudre des problèmes techniques. Avez-vous besoin d'aide ?",
                    "action": "technical_help",
                    "score": 0.80,
                }
            )

            # Suggestion de tutoriels
            expertise_levels = user_profile.get("expertise_levels", {})
            tech_expertise = expertise_levels.get("technology", {}).get(
                "level", "beginner"
            )

            if tech_expertise == "beginner":
                suggestions.append(
                    {
                        "type": "tutorials",
                        "title": "Tutoriels recommandés",
                        "content": "Souhaitez-vous accéder à des tutoriels pour débutants ?",
                        "action": "show_beginner_tutorials",
                        "score": 0.85,
                    }
                )
            elif tech_expertise == "intermediate":
                suggestions.append(
                    {
                        "type": "tutorials",
                        "title": "Tutoriels avancés",
                        "content": "Je peux vous recommander des tutoriels pour développer vos compétences. Intéressé(e) ?",
                        "action": "show_intermediate_tutorials",
                        "score": 0.75,
                    }
                )

        return suggestions

    def _generate_pattern_based_suggestions(
        self, user_context: Dict[str, Any], user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Génère des suggestions basées sur les modèles d'interaction détectés.

        Args:
            user_context (Dict[str, Any]): Contexte utilisateur actuel
            user_profile (Dict[str, Any]): Profil de l'utilisateur

        Returns:
            List[Dict[str, Any]]: Suggestions basées sur les modèles
        """
        suggestions = []

        # Récupérer les modèles d'interaction
        interaction_patterns = user_profile.get("interaction_patterns", {})

        # Si l'utilisateur pose beaucoup de questions (style inquisitif)
        dialogue_style = interaction_patterns.get("dialogue_style")
        if dialogue_style == "inquisitive":
            # Suggérer des sujets d'exploration supplémentaires
            primary_context = user_context.get("primary_context")

            if primary_context:
                exploration_topics = {
                    "work": [
                        "productivité",
                        "gestion du temps",
                        "organisation",
                        "collaboration",
                    ],
                    "research": ["sources", "méthodologies", "analyse", "données"],
                    "entertainment": [
                        "recommandations",
                        "nouveautés",
                        "tendances",
                        "critiques",
                    ],
                    "planning": [
                        "optimisation",
                        "priorités",
                        "rappels",
                        "automatisation",
                    ],
                    "learning": [
                        "méthodes d'apprentissage",
                        "ressources",
                        "pratique",
                        "progression",
                    ],
                    "technical": [
                        "solutions",
                        "alternatives",
                        "bonnes pratiques",
                        "optimisation",
                    ],
                }

                topics = exploration_topics.get(primary_context, [])
                if topics:
                    # Choisir un sujet aléatoire à suggérer
                    topic = random.choice(topics)

                    suggestions.append(
                        {
                            "type": "topic_exploration",
                            "title": f"Explorer: {topic.capitalize()}",
                            "content": f"Souhaitez-vous en savoir plus sur {topic} ?",
                            "action": f"explore_{primary_context}_{topic.replace(' ', '_')}",
                            "score": 0.70,
                        }
                    )

        # Si l'utilisateur est plutôt directif
        elif dialogue_style == "directive":
            # Suggérer des actions rapides
            suggestions.append(
                {
                    "type": "quick_actions",
                    "title": "Actions rapides",
                    "content": "Voici quelques actions rapides que vous pourriez vouloir effectuer.",
                    "actions": ["resume", "organize", "find", "create"],
                    "score": 0.75,
                }
            )

        # Basé sur le temps de réponse
        response_time = interaction_patterns.get("response_time", {})
        if response_time:
            avg_time = response_time.get("average_seconds", 0)

            # Si l'utilisateur répond très rapidement (utilisateur engagé)
            if avg_time < 30 and response_time.get("samples", 0) > 5:
                # Suggérer des interactions plus avancées
                suggestions.append(
                    {
                        "type": "advanced_interaction",
                        "title": "Fonctionnalités avancées",
                        "content": "Voulez-vous découvrir des fonctionnalités plus avancées ?",
                        "action": "show_advanced_features",
                        "score": 0.70,
                    }
                )

            # Si l'utilisateur répond très lentement (utilisateur occupé)
            elif avg_time > 300 and response_time.get("samples", 0) > 5:
                # Suggérer des moyens d'interaction asynchrones
                suggestions.append(
                    {
                        "type": "async_communication",
                        "title": "Communication asynchrone",
                        "content": "Je peux vous envoyer des rapports périodiques au lieu d'attendre vos réponses. Intéressé(e) ?",
                        "action": "setup_async_reports",
                        "score": 0.75,
                    }
                )

        return suggestions

    def filter_suggestions_by_feedback(
        self, suggestions: List[Dict[str, Any]], user_feedback: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filtre les suggestions en fonction du feedback utilisateur antérieur.

        Args:
            suggestions (List[Dict[str, Any]]): Suggestions générées
            user_feedback (Dict[str, Any]): Historique de feedback utilisateur

        Returns:
            List[Dict[str, Any]]: Suggestions filtrées
        """
        if not user_feedback:
            return suggestions

        # Récupérer l'historique des suggestions ignorées ou rejetées
        ignored_types = user_feedback.get("ignored_suggestions", [])
        rejected_types = user_feedback.get("rejected_suggestions", [])

        # Filtrer les suggestions des types fréquemment ignorés ou explicitement rejetés
        filtered_suggestions = []
        for suggestion in suggestions:
            suggestion_type = suggestion.get("type")

            # Vérifier si ce type a été explicitement rejeté
            if suggestion_type in rejected_types:
                continue

            # Vérifier si ce type a été fréquemment ignoré (plus de 3 fois)
            ignored_count = ignored_types.count(suggestion_type)
            if ignored_count > 3:
                # Réduire progressivement le score de la suggestion
                suggestion["score"] = suggestion.get("score", 0.5) * (
                    1 - (ignored_count * 0.1)
                )

                # Exclure si le score tombe en dessous du seuil
                if suggestion["score"] < self.suggestion_threshold:
                    continue

            filtered_suggestions.append(suggestion)

        return filtered_suggestions

    def track_suggestion_acceptance(
        self, suggestion_id: str, accepted: bool, user_id: str
    ) -> None:
        """
        Suit l'acceptation ou le rejet des suggestions pour améliorer les futures suggestions.

        Args:
            suggestion_id (str): Identifiant de la suggestion
            accepted (bool): Si la suggestion a été acceptée
            user_id (str): Identifiant de l'utilisateur
        """
        # Dans une implémentation réelle, cette méthode enregistrerait les données
        # dans une base de données pour un apprentissage à long terme
        logger.info(
            "Suggestion %s was %s by user %s",
            suggestion_id,
            "accepted" if accepted else "rejected",
            user_id,
        )

        # Mise à jour de l'historique local (simplifiée)
        if user_id in self.suggestion_history:
            if "feedback" not in self.suggestion_history[user_id]:
                self.suggestion_history[user_id]["feedback"] = {
                    "accepted": [],
                    "rejected": [],
                }

            feedback = self.suggestion_history[user_id]["feedback"]

            if accepted:
                feedback["accepted"].append(suggestion_id)
            else:
                feedback["rejected"].append(suggestion_id)
