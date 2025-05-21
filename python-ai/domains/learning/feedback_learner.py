from typing import Dict, List, Any, Optional, Union, Tuple, Set
import logging
import json
import time
from datetime import datetime
import hashlib
from collections import defaultdict

from ..knowledge.knowledge_graph import KnowledgeGraph
from ..knowledge.vector_store import VectorStore
from ..knowledge.semantic_search import SemanticSearch
from ..knowledge.knowledge_validation import KnowledgeValidation
from .knowledge_gaps_identifier import KnowledgeGapsIdentifier


class FeedbackLearner:
    """
    Service d'apprentissage par rétroaction.
    Analyse, traite et intègre divers types de feedback pour améliorer la base de connaissances.
    """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        vector_store: VectorStore,
        semantic_search: Optional[SemanticSearch] = None,
        knowledge_validation: Optional[KnowledgeValidation] = None,
        knowledge_gaps_identifier: Optional[KnowledgeGapsIdentifier] = None,
        min_feedback_confidence: float = 0.7,
        correction_threshold: int = 3,
    ):
        """
        Initialise le service d'apprentissage par rétroaction.

        Args:
            knowledge_graph (KnowledgeGraph): Instance du graphe de connaissances
            vector_store (VectorStore): Instance du stockage vectoriel
            semantic_search (Optional[SemanticSearch], optional): Service de recherche sémantique
            knowledge_validation (Optional[KnowledgeValidation], optional): Service de validation
            knowledge_gaps_identifier (Optional[KnowledgeGapsIdentifier], optional): Identifieur de lacunes
            min_feedback_confidence (float, optional): Seuil minimal de confiance pour le feedback. Par défaut à 0.7.
            correction_threshold (int, optional): Nombre de feedbacks nécessaires pour une correction. Par défaut à 3.
        """
        self.logger = logging.getLogger(__name__)
        self.kg = knowledge_graph
        self.vs = vector_store

        # Initialiser les services requis s'ils ne sont pas fournis
        self.semantic_search = semantic_search or SemanticSearch(
            vector_store, knowledge_graph
        )
        self.knowledge_validation = knowledge_validation or KnowledgeValidation(
            knowledge_graph, vector_store, self.semantic_search
        )
        self.knowledge_gaps_identifier = (
            knowledge_gaps_identifier
            or KnowledgeGapsIdentifier(
                knowledge_graph, vector_store, self.semantic_search
            )
        )

        # Paramètres de configuration
        self.min_feedback_confidence = min_feedback_confidence
        self.correction_threshold = correction_threshold

        # État interne
        self.pending_feedback = []
        self.feedback_history = []
        self.correction_counters = defaultdict(int)
        self.learning_stats = {
            "feedback_processed": 0,
            "knowledge_corrected": 0,
            "relations_added": 0,
            "entities_added": 0,
            "low_confidence_rejected": 0,
        }

    def process_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un feedback et l'intègre dans la base de connaissances si pertinent.

        Args:
            feedback (Dict[str, Any]): Feedback à traiter

        Returns:
            Dict[str, Any]: Résultat du traitement
        """
        feedback_id = self._generate_feedback_id(feedback)

        # Ajouter timestamp et id
        processed_feedback = {
            **feedback,
            "feedback_id": feedback_id,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
        }

        # Stocker dans l'historique
        self.feedback_history.append(processed_feedback)

        # Limiter la taille de l'historique
        if len(self.feedback_history) > 1000:
            self.feedback_history = self.feedback_history[-1000:]

        # Analyser le type de feedback
        feedback_type = feedback.get("type", "general")

        # Traiter selon le type
        if feedback_type == "correction":
            result = self._process_correction_feedback(processed_feedback)
        elif feedback_type == "relation":
            result = self._process_relation_feedback(processed_feedback)
        elif feedback_type == "question_answer":
            result = self._process_qa_feedback(processed_feedback)
        elif feedback_type == "content_relevance":
            result = self._process_relevance_feedback(processed_feedback)
        else:
            result = self._process_general_feedback(processed_feedback)

        # Mettre à jour les statistiques
        self.learning_stats["feedback_processed"] += 1

        # Mettre à jour le statut du feedback
        processed_feedback["status"] = result.get("status", "processed")
        processed_feedback["processing_result"] = result

        return result

    def process_batch_feedback(self, feedbacks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Traite un lot de feedbacks.

        Args:
            feedbacks (List[Dict[str, Any]]): Liste des feedbacks à traiter

        Returns:
            Dict[str, Any]: Résumé des résultats
        """
        results = []
        success_count = 0
        rejected_count = 0

        for feedback in feedbacks:
            result = self.process_feedback(feedback)
            results.append(result)

            if result.get("status") == "applied":
                success_count += 1
            elif result.get("status") == "rejected":
                rejected_count += 1

        # Après avoir traité tous les feedbacks, exécuter la validation
        self._validate_after_batch()

        return {
            "total_processed": len(feedbacks),
            "success_count": success_count,
            "rejected_count": rejected_count,
            "pending_count": len(feedbacks) - success_count - rejected_count,
            "detailed_results": results,
        }

    def get_learning_statistics(self) -> Dict[str, Any]:
        """
        Obtient les statistiques d'apprentissage par feedback.

        Returns:
            Dict[str, Any]: Statistiques d'apprentissage
        """
        # Agréger les types de feedback
        feedback_types = {}
        for fb in self.feedback_history:
            fb_type = fb.get("type", "general")
            feedback_types[fb_type] = feedback_types.get(fb_type, 0) + 1

        # Compter les feedbacks par statut
        status_counts = {}
        for fb in self.feedback_history:
            status = fb.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Construire les statistiques
        stats = {
            **self.learning_stats,
            "total_feedback_received": len(self.feedback_history),
            "feedback_by_type": feedback_types,
            "feedback_by_status": status_counts,
            "pending_feedback": len(self.pending_feedback),
            "active_correction_counters": len(self.correction_counters),
        }

        return stats

    def get_feedback_history(
        self,
        limit: int = 50,
        feedback_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des feedbacks traités.

        Args:
            limit (int, optional): Nombre maximum de résultats. Par défaut à 50.
            feedback_type (Optional[str], optional): Filtrer par type. Par défaut à None.
            status (Optional[str], optional): Filtrer par statut. Par défaut à None.

        Returns:
            List[Dict[str, Any]]: Historique des feedbacks
        """
        filtered_history = self.feedback_history

        # Filtrer par type si spécifié
        if feedback_type:
            filtered_history = [
                fb for fb in filtered_history if fb.get("type") == feedback_type
            ]

        # Filtrer par statut si spécifié
        if status:
            filtered_history = [
                fb for fb in filtered_history if fb.get("status") == status
            ]

        # Trier par timestamp décroissant (plus récent d'abord)
        sorted_history = sorted(
            filtered_history, key=lambda x: x.get("timestamp", ""), reverse=True
        )

        # Limiter le nombre de résultats
        return sorted_history[:limit]

    def reset_learning_statistics(self) -> Dict[str, Any]:
        """
        Réinitialise les statistiques d'apprentissage.

        Returns:
            Dict[str, Any]: Nouvelles statistiques (vides)
        """
        # Sauvegarder les anciennes statistiques
        old_stats = self.get_learning_statistics()

        # Réinitialiser
        self.learning_stats = {
            "feedback_processed": 0,
            "knowledge_corrected": 0,
            "relations_added": 0,
            "entities_added": 0,
            "low_confidence_rejected": 0,
        }

        return {
            "previous_stats": old_stats,
            "current_stats": self.get_learning_statistics(),
        }

    def _process_correction_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un feedback de correction (information incorrecte).

        Args:
            feedback (Dict[str, Any]): Feedback à traiter

        Returns:
            Dict[str, Any]: Résultat du traitement
        """
        # Extraire les informations
        concept_id = feedback.get("concept_id")
        property_name = feedback.get("property")
        incorrect_value = feedback.get("incorrect_value")
        correct_value = feedback.get("correct_value")
        confidence = feedback.get("confidence", 0.5)
        source = feedback.get("source", "user_feedback")

        # Vérifier les informations obligatoires
        if not concept_id or not property_name or not correct_value:
            return {
                "status": "rejected",
                "reason": "missing_required_fields",
                "message": "concept_id, property et correct_value sont requis",
            }

        # Vérifier le seuil de confiance
        if confidence < self.min_feedback_confidence:
            self.learning_stats["low_confidence_rejected"] += 1
            return {
                "status": "rejected",
                "reason": "low_confidence",
                "confidence": confidence,
                "min_threshold": self.min_feedback_confidence,
            }

        # Vérifier si le concept existe
        concept = self.kg.get_concept(concept_id)
        if not concept:
            return {
                "status": "rejected",
                "reason": "concept_not_found",
                "concept_id": concept_id,
            }

        # Générer une clé unique pour ce type de correction
        correction_key = f"{concept_id}:{property_name}:{correct_value}"

        # Incrémenter le compteur de correction
        self.correction_counters[correction_key] += 1

        # Vérifier si le seuil de correction est atteint
        if self.correction_counters[correction_key] >= self.correction_threshold:
            # Appliquer la correction
            try:
                if property_name == "description":
                    self.kg.update_concept_description(concept_id, correct_value)
                    # Mettre également à jour le vecteur
                    self.vs.update_concept(
                        concept_id=concept_id,
                        name=concept.get("name", ""),
                        description=correct_value,
                        metadata=concept.get("metadata", {}),
                    )
                elif property_name == "name":
                    self.kg.update_concept_name(concept_id, correct_value)
                    # Mettre également à jour le vecteur
                    self.vs.update_concept(
                        concept_id=concept_id,
                        name=correct_value,
                        description=concept.get("description", ""),
                        metadata=concept.get("metadata", {}),
                    )
                else:
                    # Pour les autres propriétés, mettre à jour les métadonnées
                    metadata = concept.get("metadata", {})
                    metadata[property_name] = correct_value
                    self.kg.update_concept_metadata(concept_id, metadata)
                    # Mettre également à jour le vecteur
                    self.vs.update_concept(
                        concept_id=concept_id,
                        name=concept.get("name", ""),
                        description=concept.get("description", ""),
                        metadata=metadata,
                    )

                # Réinitialiser le compteur
                del self.correction_counters[correction_key]

                # Incrémenter les statistiques
                self.learning_stats["knowledge_corrected"] += 1

                return {
                    "status": "applied",
                    "correction_type": "property_update",
                    "concept_id": concept_id,
                    "property": property_name,
                    "old_value": incorrect_value,
                    "new_value": correct_value,
                }

            except Exception as e:
                self.logger.error(
                    f"Erreur lors de la correction du concept {concept_id}: {e}"
                )
                return {
                    "status": "error",
                    "error": str(e),
                    "concept_id": concept_id,
                }
        else:
            # Pas encore atteint le seuil, mettre en attente
            return {
                "status": "pending",
                "correction_key": correction_key,
                "current_count": self.correction_counters[correction_key],
                "threshold": self.correction_threshold,
                "remaining": self.correction_threshold
                - self.correction_counters[correction_key],
            }

    def _process_relation_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un feedback concernant une relation manquante ou incorrecte.

        Args:
            feedback (Dict[str, Any]): Feedback à traiter

        Returns:
            Dict[str, Any]: Résultat du traitement
        """
        # Extraire les informations
        source_id = feedback.get("source_id")
        target_id = feedback.get("target_id")
        relation_type = feedback.get("relation_type")
        confidence = feedback.get("confidence", 0.5)
        bidirectional = feedback.get("bidirectional", False)

        # Vérifier les informations obligatoires
        if not source_id or not target_id or not relation_type:
            return {
                "status": "rejected",
                "reason": "missing_required_fields",
                "message": "source_id, target_id et relation_type sont requis",
            }

        # Vérifier le seuil de confiance
        if confidence < self.min_feedback_confidence:
            self.learning_stats["low_confidence_rejected"] += 1
            return {
                "status": "rejected",
                "reason": "low_confidence",
                "confidence": confidence,
                "min_threshold": self.min_feedback_confidence,
            }

        # Vérifier si les concepts existent
        source_concept = self.kg.get_concept(source_id)
        target_concept = self.kg.get_concept(target_id)

        if not source_concept:
            return {
                "status": "rejected",
                "reason": "source_concept_not_found",
                "concept_id": source_id,
            }

        if not target_concept:
            return {
                "status": "rejected",
                "reason": "target_concept_not_found",
                "concept_id": target_id,
            }

        # Générer une clé unique pour ce type de relation
        relation_key = f"{source_id}:{relation_type}:{target_id}"

        # Incrémenter le compteur
        self.correction_counters[relation_key] += 1

        # Vérifier si le seuil est atteint
        if self.correction_counters[relation_key] >= self.correction_threshold:
            # Appliquer la nouvelle relation
            try:
                # Ajouter la relation
                self.kg.add_relation(
                    source_id=source_id,
                    relation_type=relation_type,
                    target_id=target_id,
                )

                # Si bidirectionnel, ajouter également la relation inverse
                if bidirectional:
                    inverse_relation = self._get_inverse_relation(relation_type)
                    if inverse_relation:
                        self.kg.add_relation(
                            source_id=target_id,
                            relation_type=inverse_relation,
                            target_id=source_id,
                        )

                # Réinitialiser le compteur
                del self.correction_counters[relation_key]

                # Incrémenter les statistiques
                self.learning_stats["relations_added"] += 1

                return {
                    "status": "applied",
                    "correction_type": "relation_added",
                    "source_id": source_id,
                    "target_id": target_id,
                    "relation_type": relation_type,
                    "bidirectional": bidirectional,
                }

            except Exception as e:
                self.logger.error(
                    f"Erreur lors de l'ajout de la relation entre {source_id} et {target_id}: {e}"
                )
                return {
                    "status": "error",
                    "error": str(e),
                    "source_id": source_id,
                    "target_id": target_id,
                }
        else:
            # Pas encore atteint le seuil, mettre en attente
            return {
                "status": "pending",
                "relation_key": relation_key,
                "current_count": self.correction_counters[relation_key],
                "threshold": self.correction_threshold,
                "remaining": self.correction_threshold
                - self.correction_counters[relation_key],
            }

    def _process_qa_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un feedback sur une question/réponse.

        Args:
            feedback (Dict[str, Any]): Feedback à traiter

        Returns:
            Dict[str, Any]: Résultat du traitement
        """
        # Extraire les informations
        question = feedback.get("question")
        correct_answer = feedback.get("correct_answer")
        incorrect_answer = feedback.get("incorrect_answer")
        relevance_score = feedback.get("relevance_score", 0)
        correctness_score = feedback.get("correctness_score", 0)

        # Vérifier les informations obligatoires
        if not question or not correct_answer:
            return {
                "status": "rejected",
                "reason": "missing_required_fields",
                "message": "question et correct_answer sont requis",
            }

        # Calculer un score global pour la pertinence du feedback
        global_score = (relevance_score + correctness_score) / 2

        # Vérifier si le score est suffisant pour traiter ce feedback
        if global_score < self.min_feedback_confidence:
            self.learning_stats["low_confidence_rejected"] += 1
            return {
                "status": "rejected",
                "reason": "low_confidence",
                "global_score": global_score,
                "min_threshold": self.min_feedback_confidence,
            }

        # Identifier les lacunes potentielles en se basant sur la question
        analysis = self.knowledge_gaps_identifier.analyze_question(question)

        # Si une lacune est détectée, l'enregistrer
        if analysis.get("has_knowledge_gap", False):
            gap_id = self.knowledge_gaps_identifier.register_knowledge_gap(
                topic=question,
                description=f"Lacune identifiée à partir d'un feedback Q/R. "
                f"Réponse correcte: {correct_answer}",
            )

            return {
                "status": "knowledge_gap_registered",
                "gap_id": gap_id,
                "question": question,
                "correct_answer": correct_answer,
                "analysis": analysis,
            }
        else:
            # Aucune lacune identifiée, mais stocker le feedback pour analyse future
            self.pending_feedback.append(feedback)

            return {
                "status": "stored_for_analysis",
                "feedback_id": feedback.get("feedback_id"),
                "analysis": analysis,
            }

    def _process_relevance_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un feedback sur la pertinence du contenu.

        Args:
            feedback (Dict[str, Any]): Feedback à traiter

        Returns:
            Dict[str, Any]: Résultat du traitement
        """
        # Extraire les informations
        concept_id = feedback.get("concept_id")
        query = feedback.get("query", "")
        relevance_score = feedback.get("relevance_score", 0)
        comment = feedback.get("comment", "")

        # Vérifier les informations obligatoires
        if not concept_id or relevance_score == 0:
            return {
                "status": "rejected",
                "reason": "missing_required_fields",
                "message": "concept_id et relevance_score sont requis",
            }

        # Vérifier si le concept existe
        concept = self.kg.get_concept(concept_id)
        if not concept:
            return {
                "status": "rejected",
                "reason": "concept_not_found",
                "concept_id": concept_id,
            }

        # Générer une clé unique pour ce feedback de pertinence
        relevance_key = (
            f"{concept_id}:relevance:{query}" if query else f"{concept_id}:relevance"
        )

        # Si la pertinence est négative, considérer comme un problème à corriger
        if relevance_score < 0:
            # Incrémenter le compteur
            self.correction_counters[relevance_key] += 1

            # Si le seuil est atteint, marquer pour révision
            if self.correction_counters[relevance_key] >= self.correction_threshold:
                # Ajouter un marqueur dans les métadonnées
                metadata = concept.get("metadata", {})
                review_list = metadata.get("needs_review", [])

                if query:
                    review_item = f"Pertinence pour la requête: {query}"
                else:
                    review_item = "Pertinence générale"

                if comment:
                    review_item += f" - Commentaire: {comment}"

                if review_item not in review_list:
                    review_list.append(review_item)

                metadata["needs_review"] = review_list

                # Mettre à jour le concept
                try:
                    self.kg.update_concept_metadata(concept_id, metadata)

                    # Réinitialiser le compteur
                    del self.correction_counters[relevance_key]

                    return {
                        "status": "applied",
                        "correction_type": "marked_for_review",
                        "concept_id": concept_id,
                        "relevance_issue": review_item,
                    }
                except Exception as e:
                    self.logger.error(
                        f"Erreur lors du marquage pour révision du concept {concept_id}: {e}"
                    )
                    return {
                        "status": "error",
                        "error": str(e),
                        "concept_id": concept_id,
                    }
            else:
                # Pas encore atteint le seuil
                return {
                    "status": "pending",
                    "relevance_key": relevance_key,
                    "current_count": self.correction_counters[relevance_key],
                    "threshold": self.correction_threshold,
                    "remaining": self.correction_threshold
                    - self.correction_counters[relevance_key],
                }
        else:
            # Feedback positif, enregistrer pour analyse
            return {
                "status": "positive_feedback_recorded",
                "concept_id": concept_id,
                "relevance_score": relevance_score,
            }

    def _process_general_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traite un feedback général.

        Args:
            feedback (Dict[str, Any]): Feedback à traiter

        Returns:
            Dict[str, Any]: Résultat du traitement
        """
        # Enregistrer le feedback pour analyse future
        self.pending_feedback.append(feedback)

        return {
            "status": "stored_for_analysis",
            "feedback_id": feedback.get("feedback_id"),
            "message": "Feedback général enregistré pour analyse future",
        }

    def _validate_after_batch(self) -> None:
        """
        Exécute une validation après le traitement d'un lot de feedbacks.
        """
        # Si des concepts ont été modifiés, exécuter une validation
        if (
            self.learning_stats["knowledge_corrected"] > 0
            or self.learning_stats["relations_added"] > 0
        ):
            try:
                # Pour l'instant, on ne valide que les concepts récemment modifiés
                recent_concepts = self.kg.get_recent_concepts(hours=1, limit=50)

                if recent_concepts:
                    concept_ids = [c.get("id") for c in recent_concepts]
                    self.knowledge_validation.validate_concepts(concept_ids)
            except Exception as e:
                self.logger.error(f"Erreur lors de la validation post-feedback: {e}")

    def _generate_feedback_id(self, feedback: Dict[str, Any]) -> str:
        """
        Génère un ID unique pour un feedback.

        Args:
            feedback (Dict[str, Any]): Feedback

        Returns:
            str: ID unique
        """
        # Créer une représentation stable du feedback
        fb_type = feedback.get("type", "general")
        timestamp = str(int(time.time()))

        # Différentes clés en fonction du type de feedback
        if fb_type == "correction":
            key_parts = [
                fb_type,
                feedback.get("concept_id", ""),
                feedback.get("property", ""),
                str(feedback.get("correct_value", "")),
                timestamp,
            ]
        elif fb_type == "relation":
            key_parts = [
                fb_type,
                feedback.get("source_id", ""),
                feedback.get("relation_type", ""),
                feedback.get("target_id", ""),
                timestamp,
            ]
        elif fb_type == "question_answer":
            key_parts = [
                fb_type,
                feedback.get("question", "")[:50],  # Limiter la longueur
                timestamp,
            ]
        else:
            # Cas général
            key_parts = [
                fb_type,
                str(hash(json.dumps(feedback, sort_keys=True))),
                timestamp,
            ]

        # Créer une empreinte unique
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode("utf-8")).hexdigest()

    def _get_inverse_relation(self, relation_type: str) -> Optional[str]:
        """
        Détermine la relation inverse pour un type de relation donné.

        Args:
            relation_type (str): Type de relation

        Returns:
            Optional[str]: Type de relation inverse, ou None si non défini
        """
        # Mapping des relations inverses courantes
        inverse_relations = {
            "contains": "is_part_of",
            "is_part_of": "contains",
            "depends_on": "is_dependency_for",
            "is_dependency_for": "depends_on",
            "parent_of": "child_of",
            "child_of": "parent_of",
            "related_to": "related_to",  # Relation symétrique
            "causes": "caused_by",
            "caused_by": "causes",
            "precedes": "follows",
            "follows": "precedes",
            "similar_to": "similar_to",  # Relation symétrique
            "opposite_of": "opposite_of",  # Relation symétrique
        }

        return inverse_relations.get(relation_type)
