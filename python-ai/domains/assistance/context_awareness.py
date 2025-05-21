"""
Module de gestion de la conscience du contexte pour Lucie
Permet à Lucie de comprendre et d'analyser le contexte utilisateur pour des interactions plus pertinentes
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json

# Configuration des logs
logger = logging.getLogger("lucie.assistance.context_awareness")


class ContextAwareness:
    """
    Analyse et gère le contexte utilisateur pour permettre des interactions plus pertinentes.
    Fournit des mécanismes pour détecter le contexte actuel, les modèles de comportement,
    et les situations nécessitant une assistance spécifique.
    """

    def __init__(self, context_threshold: float = 0.75):
        """
        Initialise le gestionnaire de conscience du contexte.

        Args:
            context_threshold (float): Seuil de confiance pour la détection du contexte
        """
        self.context_threshold = context_threshold
        logger.info(
            "ContextAwareness initialized with threshold: %f", context_threshold
        )

    def analyze_user_context(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse le contexte utilisateur à partir des données disponibles.

        Args:
            user_data (Dict[str, Any]): Données de l'utilisateur (historique, préférences, etc.)

        Returns:
            Dict[str, Any]: Contexte analysé avec scores de pertinence
        """
        context_result = {
            "timestamp": datetime.now().isoformat(),
            "contexts": [],
            "primary_context": None,
            "confidence": 0.0,
        }

        # Extraire les données pertinentes
        messages = user_data.get("conversation", {}).get("messages", [])
        recent_activities = user_data.get("activities", [])
        time_of_day = self._get_time_context()

        # Analyser le contexte temporel
        context_result["time_context"] = time_of_day

        # Détecter les contextes possibles à partir des messages récents
        if messages:
            contexts = self._detect_context_from_messages(messages)
            context_result["contexts"] = contexts

            # Identifier le contexte principal
            if contexts:
                primary_context = max(contexts, key=lambda x: x["score"])
                if primary_context["score"] >= self.context_threshold:
                    context_result["primary_context"] = primary_context["type"]
                    context_result["confidence"] = primary_context["score"]

        # Enrichir avec les activités récentes
        if recent_activities:
            activity_context = self._analyze_recent_activities(recent_activities)
            context_result["activity_context"] = activity_context

        return context_result

    def _detect_context_from_messages(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Détecte le contexte à partir des messages récents.

        Args:
            messages (List[Dict[str, Any]]): Liste des messages récents

        Returns:
            List[Dict[str, Any]]: Liste des contextes potentiels avec scores
        """
        # Limiter aux 5 derniers messages pour l'analyse
        recent_messages = messages[-5:] if len(messages) > 5 else messages

        contexts = []
        context_indicators = {
            "work": [
                "projet",
                "travail",
                "réunion",
                "deadline",
                "tâche",
                "collaborateur",
            ],
            "research": [
                "recherche",
                "information",
                "article",
                "étude",
                "analyse",
                "données",
            ],
            "entertainment": [
                "film",
                "musique",
                "jeu",
                "détente",
                "loisir",
                "divertissement",
            ],
            "planning": [
                "planning",
                "agenda",
                "calendrier",
                "rendez-vous",
                "organisation",
            ],
            "learning": ["apprendre", "cours", "formation", "étudier", "comprendre"],
            "technical": [
                "code",
                "programmation",
                "développement",
                "technique",
                "système",
            ],
        }

        # Calculer les scores pour chaque type de contexte
        context_scores = {context_type: 0.0 for context_type in context_indicators}

        for message in recent_messages:
            if message.get("role") == "user":
                content = message.get("content", "").lower()

                # Calculer le score pour chaque contexte
                for context_type, indicators in context_indicators.items():
                    for indicator in indicators:
                        if indicator in content:
                            # Pondérer plus fortement les messages récents
                            recency_factor = 1.0
                            if "timestamp" in message:
                                message_time = datetime.fromisoformat(
                                    message["timestamp"]
                                )
                                elapsed = (
                                    datetime.now() - message_time
                                ).total_seconds() / 3600  # en heures
                                recency_factor = max(
                                    0.5, 1.0 - (elapsed / 24)
                                )  # diminue avec le temps

                            context_scores[context_type] += 0.2 * recency_factor

        # Normaliser les scores
        total_score = sum(context_scores.values())
        if total_score > 0:
            for context_type, score in context_scores.items():
                normalized_score = score / total_score
                if normalized_score > 0.2:  # Seuil minimal pour considérer un contexte
                    contexts.append({"type": context_type, "score": normalized_score})

        # Trier par score décroissant
        return sorted(contexts, key=lambda x: x["score"], reverse=True)

    def _get_time_context(self) -> Dict[str, Any]:
        """
        Détermine le contexte temporel actuel.

        Returns:
            Dict[str, Any]: Informations sur le contexte temporel
        """
        now = datetime.now()
        hour = now.hour

        # Déterminer le moment de la journée
        if 5 <= hour < 9:
            period = "morning_early"
        elif 9 <= hour < 12:
            period = "morning_late"
        elif 12 <= hour < 14:
            period = "lunch"
        elif 14 <= hour < 17:
            period = "afternoon"
        elif 17 <= hour < 20:
            period = "evening"
        elif 20 <= hour < 23:
            period = "night"
        else:
            period = "late_night"

        # Jour de la semaine
        weekday = now.strftime("%A").lower()
        is_weekend = weekday in ["saturday", "sunday"]

        return {
            "timestamp": now.isoformat(),
            "period": period,
            "weekday": weekday,
            "is_weekend": is_weekend,
            "hour": hour,
        }

    def _analyze_recent_activities(
        self, activities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyse les activités récentes pour enrichir le contexte.

        Args:
            activities (List[Dict[str, Any]]): Liste des activités récentes

        Returns:
            Dict[str, Any]: Analyse des activités récentes
        """
        # Limiter aux activités des dernières 24h
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_activities = []

        for activity in activities:
            if "timestamp" in activity:
                activity_time = datetime.fromisoformat(activity["timestamp"])
                if activity_time >= recent_cutoff:
                    recent_activities.append(activity)

        # Analyser les types d'activités
        activity_types = {}
        for activity in recent_activities:
            activity_type = activity.get("type")
            if activity_type:
                if activity_type not in activity_types:
                    activity_types[activity_type] = 0
                activity_types[activity_type] += 1

        # Déterminer l'activité dominante
        dominant_activity = None
        max_count = 0
        for activity_type, count in activity_types.items():
            if count > max_count:
                max_count = count
                dominant_activity = activity_type

        return {
            "recent_count": len(recent_activities),
            "activity_types": activity_types,
            "dominant_activity": dominant_activity,
        }

    def detect_context_switch(
        self, previous_context: Dict[str, Any], current_context: Dict[str, Any]
    ) -> bool:
        """
        Détecte un changement significatif de contexte.

        Args:
            previous_context (Dict[str, Any]): Contexte précédent
            current_context (Dict[str, Any]): Contexte actuel

        Returns:
            bool: True si un changement de contexte significatif est détecté
        """
        # Vérifier s'il y a un changement de contexte principal
        prev_primary = previous_context.get("primary_context")
        curr_primary = current_context.get("primary_context")

        if prev_primary != curr_primary:
            # Un changement de contexte principal est toujours significatif
            return True

        # Vérifier le changement de période de la journée
        prev_time = previous_context.get("time_context", {}).get("period")
        curr_time = current_context.get("time_context", {}).get("period")

        if prev_time != curr_time:
            # Certaines transitions temporelles sont significatives
            significant_transitions = [
                ("morning_early", "morning_late"),
                ("morning_late", "lunch"),
                ("lunch", "afternoon"),
                ("afternoon", "evening"),
                ("evening", "night"),
                ("night", "late_night"),
            ]

            if (prev_time, curr_time) in significant_transitions:
                return True

        return False

    def get_context_relevance_score(
        self, context: Dict[str, Any], user_query: str
    ) -> float:
        """
        Calcule un score de pertinence entre le contexte et la requête utilisateur.

        Args:
            context (Dict[str, Any]): Contexte détecté
            user_query (str): Requête utilisateur

        Returns:
            float: Score de pertinence entre 0 et 1
        """
        if not context or not user_query:
            return 0.0

        # Obtenir le contexte principal
        primary_context = context.get("primary_context")
        if not primary_context:
            return 0.3  # Score de base en l'absence de contexte fort

        # Indicateurs de contexte par type
        context_indicators = {
            "work": [
                "projet",
                "travail",
                "réunion",
                "deadline",
                "tâche",
                "collaborateur",
            ],
            "research": [
                "recherche",
                "information",
                "article",
                "étude",
                "analyse",
                "données",
            ],
            "entertainment": [
                "film",
                "musique",
                "jeu",
                "détente",
                "loisir",
                "divertissement",
            ],
            "planning": [
                "planning",
                "agenda",
                "calendrier",
                "rendez-vous",
                "organisation",
            ],
            "learning": ["apprendre", "cours", "formation", "étudier", "comprendre"],
            "technical": [
                "code",
                "programmation",
                "développement",
                "technique",
                "système",
            ],
        }

        # Vérifier les correspondances entre la requête et le contexte
        query_lower = user_query.lower()
        indicators = context_indicators.get(primary_context, [])

        # Calculer le score de correspondance
        match_score = 0.0
        for indicator in indicators:
            if indicator in query_lower:
                match_score += 0.2

        # Limiter le score à 1.0
        match_score = min(1.0, match_score)

        # Combiner avec le score de confiance du contexte
        confidence = context.get("confidence", 0.5)

        # Calculer le score final (moyenne pondérée)
        relevance_score = (match_score * 0.7) + (confidence * 0.3)

        return relevance_score
