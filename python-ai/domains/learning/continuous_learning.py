from typing import Dict, List, Any, Optional, Union, Tuple, Set
import logging
import threading
import time
import json
from datetime import datetime
from collections import deque

from ..knowledge.knowledge_graph import KnowledgeGraph
from ..knowledge.vector_store import VectorStore
from ..knowledge.semantic_search import SemanticSearch
from ..knowledge.cross_domain_knowledge_graph import CrossDomainKnowledgeGraph
from ..knowledge.knowledge_validation import KnowledgeValidation
from .knowledge_gaps_identifier import KnowledgeGapsIdentifier
from .url_knowledge_extractor import URLKnowledgeExtractor


class ContinuousLearning:
    """
    Service d'apprentissage continu.
    Automatise l'acquisition, la validation et l'intégration de nouvelles connaissances
    de façon asynchrone et continue.
    """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        vector_store: VectorStore,
        knowledge_gaps_identifier: Optional[KnowledgeGapsIdentifier] = None,
        url_extractor: Optional[URLKnowledgeExtractor] = None,
        knowledge_validation: Optional[KnowledgeValidation] = None,
        semantic_search: Optional[SemanticSearch] = None,
        cross_domain_kg: Optional[CrossDomainKnowledgeGraph] = None,
        learning_interval: int = 3600,  # 1 heure par défaut
        max_pending_sources: int = 100,
    ):
        """
        Initialise le service d'apprentissage continu.

        Args:
            knowledge_graph (KnowledgeGraph): Instance du graphe de connaissances
            vector_store (VectorStore): Instance du stockage vectoriel
            knowledge_gaps_identifier (Optional[KnowledgeGapsIdentifier], optional): Identifieur de lacunes
            url_extractor (Optional[URLKnowledgeExtractor], optional): Extracteur de connaissances depuis des URLs
            knowledge_validation (Optional[KnowledgeValidation], optional): Service de validation de connaissances
            semantic_search (Optional[SemanticSearch], optional): Service de recherche sémantique
            cross_domain_kg (Optional[CrossDomainKnowledgeGraph], optional): Gestionnaire de graphe multi-domaines
            learning_interval (int, optional): Intervalle entre deux cycles d'apprentissage en secondes. Par défaut à 3600.
            max_pending_sources (int, optional): Nombre maximum de sources en attente. Par défaut à 100.
        """
        self.logger = logging.getLogger(__name__)
        self.kg = knowledge_graph
        self.vs = vector_store
        self.cross_domain_kg = cross_domain_kg

        # Initialiser les services requis s'ils ne sont pas fournis
        self.semantic_search = semantic_search or SemanticSearch(
            vector_store, knowledge_graph
        )
        self.knowledge_gaps_identifier = (
            knowledge_gaps_identifier
            or KnowledgeGapsIdentifier(
                knowledge_graph, vector_store, self.semantic_search
            )
        )
        self.url_extractor = url_extractor or URLKnowledgeExtractor(
            knowledge_graph, vector_store, cross_domain_kg
        )
        self.knowledge_validation = knowledge_validation or KnowledgeValidation(
            knowledge_graph, vector_store, self.semantic_search
        )

        # Paramètres de configuration
        self.learning_interval = learning_interval
        self.max_pending_sources = max_pending_sources

        # État interne
        self.pending_sources = deque(maxlen=max_pending_sources)
        self.learning_queue = deque(maxlen=max_pending_sources * 2)
        self.identified_gaps = set()
        self.learning_sessions = []

        # Contrôle du thread d'apprentissage
        self.is_learning_active = False
        self.learning_thread = None
        self.last_learning_cycle = None

    def start_continuous_learning(self) -> bool:
        """
        Démarre le processus d'apprentissage continu en arrière-plan.

        Returns:
            bool: True si démarré avec succès, False sinon
        """
        if self.is_learning_active:
            self.logger.warning("Le processus d'apprentissage continu est déjà actif")
            return False

        self.is_learning_active = True
        self.learning_thread = threading.Thread(
            target=self._continuous_learning_loop,
            daemon=True,
            name="Continuous-Learning",
        )
        self.learning_thread.start()

        self.logger.info(
            f"Processus d'apprentissage continu démarré (intervalle: {self.learning_interval}s)"
        )
        return True

    def stop_continuous_learning(self) -> bool:
        """
        Arrête le processus d'apprentissage continu.

        Returns:
            bool: True si arrêté avec succès, False sinon
        """
        if not self.is_learning_active:
            self.logger.warning("Le processus d'apprentissage continu n'est pas actif")
            return False

        self.is_learning_active = False
        if self.learning_thread and self.learning_thread.is_alive():
            self.learning_thread.join(timeout=5.0)

        self.logger.info("Processus d'apprentissage continu arrêté")
        return True

    def add_learning_source(
        self, source_url: str, priority: int = 1, domain: str = "general"
    ) -> Dict[str, Any]:
        """
        Ajoute une source d'apprentissage à la file d'attente.

        Args:
            source_url (str): URL de la source
            priority (int, optional): Priorité (1-10). Par défaut à 1.
            domain (str, optional): Domaine de connaissances. Par défaut à "general".

        Returns:
            Dict[str, Any]: Résultat de l'ajout
        """
        # Vérifier si l'URL est déjà dans la file d'attente
        for source in self.pending_sources:
            if source["url"] == source_url:
                self.logger.info(f"Source déjà en file d'attente: {source_url}")
                return {
                    "status": "already_queued",
                    "position": list(self.pending_sources).index(source) + 1,
                    "total_queued": len(self.pending_sources),
                }

        # Ajouter à la file d'attente
        source_item = {
            "url": source_url,
            "priority": max(1, min(10, priority)),  # Entre 1 et 10
            "domain": domain,
            "added_at": datetime.now().isoformat(),
            "status": "pending",
        }

        self.pending_sources.append(source_item)

        # Déclencher un cycle d'apprentissage immédiat si la priorité est élevée
        if priority >= 8 and not self.is_learning_active:
            self.start_continuous_learning()

        return {
            "status": "queued",
            "position": len(self.pending_sources),
            "total_queued": len(self.pending_sources),
            "estimated_processing_time": self._estimate_processing_time(priority),
        }

    def add_knowledge_gap(
        self, topic: str, description: str, priority: int = 5
    ) -> Dict[str, Any]:
        """
        Ajoute une lacune de connaissances identifiée manuellement.

        Args:
            topic (str): Sujet de la lacune
            description (str): Description détaillée
            priority (int, optional): Priorité (1-10). Par défaut à 5.

        Returns:
            Dict[str, Any]: Résultat de l'ajout
        """
        gap_id = self.knowledge_gaps_identifier.register_knowledge_gap(
            topic, description
        )

        # Ajouter à la liste des lacunes identifiées
        self.identified_gaps.add(gap_id)

        # Ajouter à la file d'apprentissage
        learning_item = {
            "type": "knowledge_gap",
            "gap_id": gap_id,
            "topic": topic,
            "description": description,
            "priority": max(1, min(10, priority)),
            "added_at": datetime.now().isoformat(),
            "status": "pending",
        }

        self.learning_queue.append(learning_item)

        # Déclencher un cycle d'apprentissage immédiat si priorité élevée
        if priority >= 8 and not self.is_learning_active:
            self.start_continuous_learning()

        return {
            "status": "registered",
            "gap_id": gap_id,
            "queue_position": len(self.learning_queue),
        }

    def process_conversation_history(
        self, conversation: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Analyse un historique de conversation pour identifier des lacunes et opportunités d'apprentissage.

        Args:
            conversation (List[Dict[str, str]]): Historique de conversation

        Returns:
            Dict[str, Any]: Résultat de l'analyse
        """
        # Identifier les lacunes potentielles
        gaps = self.knowledge_gaps_identifier.analyze_conversation_history(conversation)

        # Prioriser les lacunes identifiées
        prioritized_gaps = self.knowledge_gaps_identifier.prioritize_knowledge_gaps(
            gaps
        )

        # Ajouter les lacunes à la file d'apprentissage
        added_gaps = []
        for gap in prioritized_gaps:
            if gap.get("gap_signature") not in self.identified_gaps:
                gap_id = self.knowledge_gaps_identifier.register_knowledge_gap(
                    " ".join(gap.get("missing_concepts", [])),
                    f"Lacune identifiée dans la conversation: {gap.get('question', '')}",
                )

                self.identified_gaps.add(gap.get("gap_signature"))

                # Ajouter à la file d'apprentissage
                learning_item = {
                    "type": "knowledge_gap",
                    "gap_id": gap_id,
                    "topic": " ".join(gap.get("missing_concepts", [])),
                    "description": f"Lacune identifiée dans la conversation",
                    "priority": min(
                        7, int(gap.get("priority_score", 5) / 2)
                    ),  # Conversion vers une échelle 1-10
                    "added_at": datetime.now().isoformat(),
                    "status": "pending",
                    "source": "conversation",
                }

                self.learning_queue.append(learning_item)
                added_gaps.append(gap_id)

        return {
            "gaps_identified": len(prioritized_gaps),
            "gaps_added_to_learning": len(added_gaps),
            "gap_ids": added_gaps,
        }

    def trigger_learning_cycle(self) -> Dict[str, Any]:
        """
        Déclenche manuellement un cycle d'apprentissage.

        Returns:
            Dict[str, Any]: Résultat du cycle d'apprentissage
        """
        if self.is_learning_active:
            return {
                "status": "already_running",
                "last_cycle": self.last_learning_cycle,
            }

        # Exécuter un cycle d'apprentissage
        cycle_results = self._execute_learning_cycle()

        return {
            "status": "completed",
            "cycle_results": cycle_results,
        }

    def get_learning_status(self) -> Dict[str, Any]:
        """
        Obtient l'état actuel du processus d'apprentissage.

        Returns:
            Dict[str, Any]: État du processus d'apprentissage
        """
        return {
            "is_active": self.is_learning_active,
            "pending_sources": len(self.pending_sources),
            "learning_queue": len(self.learning_queue),
            "identified_gaps": len(self.identified_gaps),
            "last_learning_cycle": self.last_learning_cycle,
            "learning_sessions": len(self.learning_sessions),
            "next_cycle_in": (
                self._get_next_cycle_time() if self.is_learning_active else None
            ),
        }

    def _continuous_learning_loop(self) -> None:
        """
        Boucle principale du processus d'apprentissage continu.
        """
        self.logger.info("Démarrage de la boucle d'apprentissage continu")

        while self.is_learning_active:
            try:
                # Exécuter un cycle d'apprentissage
                cycle_results = self._execute_learning_cycle()

                # Enregistrer les résultats
                self.learning_sessions.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "results": cycle_results,
                    }
                )

                # Limiter le nombre de sessions enregistrées
                if len(self.learning_sessions) > 100:
                    self.learning_sessions = self.learning_sessions[-100:]

                # Attendre jusqu'au prochain cycle
                time.sleep(self.learning_interval)

            except Exception as e:
                self.logger.error(f"Erreur dans la boucle d'apprentissage: {e}")
                time.sleep(60)  # Attendre avant de réessayer

        self.logger.info("Fin de la boucle d'apprentissage continu")

    def _execute_learning_cycle(self) -> Dict[str, Any]:
        """
        Exécute un cycle complet d'apprentissage.

        Returns:
            Dict[str, Any]: Résultats du cycle
        """
        self.logger.info("Exécution d'un cycle d'apprentissage")
        start_time = time.time()

        # Métriques du cycle
        cycle_metrics = {
            "sources_processed": 0,
            "concepts_added": 0,
            "knowledge_gaps_addressed": 0,
            "validation_issues_fixed": 0,
        }

        # 1. Traiter les sources en attente
        sources_processed = self._process_pending_sources()
        cycle_metrics["sources_processed"] = len(sources_processed)

        # Calculer le nombre total de concepts ajoutés
        concepts_added = sum(
            source.get("concepts_added", 0) for source in sources_processed
        )
        cycle_metrics["concepts_added"] = concepts_added

        # 2. Traiter les lacunes de connaissances
        gaps_addressed = self._address_knowledge_gaps()
        cycle_metrics["knowledge_gaps_addressed"] = len(gaps_addressed)

        # 3. Valider les connaissances récemment ajoutées
        validation_results = self._validate_recent_knowledge()
        cycle_metrics["validation_issues_fixed"] = validation_results.get(
            "issues_fixed", 0
        )

        # Mettre à jour le timestamp du dernier cycle
        self.last_learning_cycle = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": time.time() - start_time,
            "metrics": cycle_metrics,
        }

        self.logger.info(
            f"Cycle d'apprentissage terminé: {cycle_metrics['concepts_added']} concepts ajoutés, "
            f"{cycle_metrics['knowledge_gaps_addressed']} lacunes traitées"
        )

        return {
            "timestamp": self.last_learning_cycle["timestamp"],
            "duration": self.last_learning_cycle["duration_seconds"],
            "metrics": cycle_metrics,
            "processed_sources": sources_processed,
            "addressed_gaps": gaps_addressed,
            "validation_results": validation_results,
        }

    def _process_pending_sources(self) -> List[Dict[str, Any]]:
        """
        Traite les sources d'information en attente.

        Returns:
            List[Dict[str, Any]]: Sources traitées
        """
        if not self.pending_sources:
            return []

        # Trier par priorité (décroissante)
        sorted_sources = sorted(
            self.pending_sources, key=lambda x: x.get("priority", 1), reverse=True
        )

        # Traiter un maximum de 5 sources par cycle
        sources_to_process = sorted_sources[:5]
        results = []

        for source in sources_to_process:
            try:
                # Extraire les connaissances de l'URL
                extraction_result = self.url_extractor.extract_from_url(
                    url=source["url"],
                    domain=source.get("domain", "general"),
                )

                # Créer l'entrée de résultat
                result = {
                    **source,
                    "processed_at": datetime.now().isoformat(),
                    "status": extraction_result.get("status", "error"),
                    "concepts_added": extraction_result.get("concepts_added", 0),
                }

                results.append(result)

                # Retirer de la file d'attente
                if source in self.pending_sources:
                    self.pending_sources.remove(source)

            except Exception as e:
                self.logger.error(
                    f"Erreur lors du traitement de la source {source['url']}: {e}"
                )
                # Marquer comme erreur mais conserver dans la file
                source["status"] = "error"
                source["error"] = str(e)
                results.append(source)

        return results

    def _address_knowledge_gaps(self) -> List[Dict[str, Any]]:
        """
        Traite les lacunes de connaissances identifiées.

        Returns:
            List[Dict[str, Any]]: Lacunes traitées
        """
        if not self.learning_queue:
            return []

        # Trier par priorité (décroissante)
        sorted_gaps = sorted(
            self.learning_queue, key=lambda x: x.get("priority", 1), reverse=True
        )

        # Traiter un maximum de 3 lacunes par cycle
        gaps_to_process = [
            gap
            for gap in sorted_gaps[:3]
            if gap.get("type") == "knowledge_gap" and gap.get("status") == "pending"
        ]

        results = []

        for gap in gaps_to_process:
            try:
                # Marquer comme en cours de traitement
                gap["status"] = "processing"

                # Synthétiser des termes de recherche basés sur le sujet et la description
                search_terms = []
                if "topic" in gap:
                    search_terms.append(gap["topic"])
                if "description" in gap and len(gap["description"]) > 10:
                    search_terms.append(gap["description"])

                search_query = " ".join(search_terms[:2])

                # TODO: Implémenter l'acquisition de connaissance externe
                # Cette partie pourrait être étendue pour utiliser des APIs externes,
                # des modèles de langage, ou d'autres sources d'information

                # Pour l'instant, marquer comme adressé
                gap["status"] = "addressed"
                gap["processed_at"] = datetime.now().isoformat()

                # Retirer de la file d'apprentissage
                if gap in self.learning_queue:
                    self.learning_queue.remove(gap)

                results.append(gap)

            except Exception as e:
                self.logger.error(
                    f"Erreur lors du traitement de la lacune {gap.get('gap_id')}: {e}"
                )
                gap["status"] = "error"
                gap["error"] = str(e)
                results.append(gap)

        return results

    def _validate_recent_knowledge(self) -> Dict[str, Any]:
        """
        Valide les connaissances récemment ajoutées.

        Returns:
            Dict[str, Any]: Résultats de la validation
        """
        # Obtenir les concepts récemment ajoutés (dernières 24h)
        recent_concepts = self.kg.get_recent_concepts(hours=24, limit=50)

        if not recent_concepts:
            return {"status": "no_recent_concepts", "issues_fixed": 0}

        # Exécuter la validation
        validation_results = self.knowledge_validation.validate_concepts(
            [concept.get("id") for concept in recent_concepts]
        )

        # Corriger les problèmes détectés
        issues_fixed = 0
        if validation_results.get("issues"):
            for issue in validation_results.get("issues", []):
                if issue.get("auto_fixable", False):
                    try:
                        self.knowledge_validation.fix_issue(issue.get("issue_id"))
                        issues_fixed += 1
                    except Exception as e:
                        self.logger.error(
                            f"Erreur lors de la correction de l'issue {issue.get('issue_id')}: {e}"
                        )

        return {
            "status": "completed",
            "concepts_validated": len(recent_concepts),
            "issues_found": len(validation_results.get("issues", [])),
            "issues_fixed": issues_fixed,
        }

    def _estimate_processing_time(self, priority: int) -> int:
        """
        Estime le temps de traitement d'une source en fonction de sa priorité.

        Args:
            priority (int): Priorité de la source

        Returns:
            int: Temps estimé en secondes
        """
        # Calcul basique: plus la priorité est élevée, plus le traitement sera rapide
        base_time = self.learning_interval

        # Facteur d'ajustement en fonction de la priorité (1-10)
        priority_factor = max(0.1, (11 - priority) / 10)

        # Ajustement en fonction du nombre d'éléments en attente
        queue_factor = len(self.pending_sources) / self.max_pending_sources

        estimated_time = int(base_time * priority_factor * (1 + queue_factor))

        return estimated_time

    def _get_next_cycle_time(self) -> int:
        """
        Calcule le temps restant avant le prochain cycle d'apprentissage.

        Returns:
            int: Temps restant en secondes
        """
        if not self.last_learning_cycle:
            return 0

        # Calculer le temps écoulé depuis le dernier cycle
        last_cycle_time = datetime.fromisoformat(self.last_learning_cycle["timestamp"])
        elapsed = (datetime.now() - last_cycle_time).total_seconds()

        # Temps restant
        remaining = max(0, self.learning_interval - elapsed)

        return int(remaining)
