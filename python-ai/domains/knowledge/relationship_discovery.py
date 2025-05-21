from typing import Dict, List, Any, Optional, Union, Set, Tuple
import logging
import re
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from .knowledge_graph import KnowledgeGraph
from .vector_store import VectorStore


class RelationshipDiscovery:
    """
    Service de découverte de relations entre concepts.
    Utilise l'analyse vectorielle et textuelle pour suggérer des relations potentielles.
    """

    def __init__(self, knowledge_graph: KnowledgeGraph, vector_store: VectorStore):
        """
        Initialise le service de découverte de relations.

        Args:
            knowledge_graph (KnowledgeGraph): Instance du graphe de connaissances
            vector_store (VectorStore): Instance du stockage vectoriel
        """
        self.kg = knowledge_graph
        self.vs = vector_store
        self.logger = logging.getLogger(__name__)
        self.relation_types = self._initialize_relation_types()

    def _initialize_relation_types(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialise les types de relations prédéfinis.

        Returns:
            Dict[str, Dict[str, Any]]: Dictionnaire des types de relations
        """
        return {
            "SIMILAR_TO": {
                "threshold": 0.85,
                "description": "Indique une similarité sémantique entre deux concepts",
                "bidirectional": True,
            },
            "PART_OF": {
                "threshold": 0.7,
                "description": "Indique qu'un concept est une partie d'un autre",
                "bidirectional": False,
                "patterns": [
                    r"(?i)partie de|composant de|élément de|appartient à",
                    r"(?i)contient|comprend|inclut",
                ],
            },
            "CAUSES": {
                "threshold": 0.7,
                "description": "Indique une relation de causalité",
                "bidirectional": False,
                "patterns": [
                    r"(?i)cause|provoque|entraîne|conduit à",
                    r"(?i)résulte de|est causé par|est provoqué par",
                ],
            },
            "RELATED_TO": {
                "threshold": 0.6,
                "description": "Indique une relation générale entre concepts",
                "bidirectional": True,
            },
            "USED_FOR": {
                "threshold": 0.7,
                "description": "Indique qu'un concept est utilisé pour un autre",
                "bidirectional": False,
                "patterns": [
                    r"(?i)utilisé pour|sert à|permet de",
                    r"(?i)utilise|nécessite|requiert",
                ],
            },
            "TYPE_OF": {
                "threshold": 0.75,
                "description": "Indique une relation d'héritage ou de classification",
                "bidirectional": False,
                "patterns": [
                    r"(?i)type de|sorte de|espèce de|catégorie de",
                    r"(?i)est un|est une",
                ],
            },
        }

    def add_relation_type(
        self,
        name: str,
        description: str,
        threshold: float = 0.7,
        bidirectional: bool = False,
        patterns: Optional[List[str]] = None,
    ) -> bool:
        """
        Ajoute un nouveau type de relation.

        Args:
            name (str): Nom de la relation (en majuscules)
            description (str): Description de la relation
            threshold (float, optional): Seuil de confiance. Par défaut à 0.7.
            bidirectional (bool, optional): Si la relation est bidirectionnelle. Par défaut à False.
            patterns (Optional[List[str]], optional): Motifs textuels pour détecter la relation.

        Returns:
            bool: True si le type a été ajouté avec succès
        """
        if name in self.relation_types:
            self.logger.warning(f"Le type de relation '{name}' existe déjà")
            return False

        self.relation_types[name] = {
            "threshold": threshold,
            "description": description,
            "bidirectional": bidirectional,
        }

        if patterns:
            self.relation_types[name]["patterns"] = patterns

        return True

    def discover_similar_concepts(
        self, limit: int = 100, threshold: float = 0.85, batch_size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Découvre des concepts similaires basés sur la proximité vectorielle.

        Args:
            limit (int, optional): Nombre maximal de relations à créer. Par défaut à 100.
            threshold (float, optional): Seuil de similarité. Par défaut à 0.85.
            batch_size (int, optional): Taille de lot pour le traitement. Par défaut à 20.

        Returns:
            List[Dict[str, Any]]: Liste des relations découvertes
        """
        # Trouver tous les concepts
        all_concepts = self._get_all_concepts()
        self.logger.info(
            f"Découverte de concepts similaires parmi {len(all_concepts)} concepts"
        )

        if len(all_concepts) < 2:
            self.logger.warning("Pas assez de concepts pour découvrir des similarités")
            return []

        discovered_relations = []
        pairs_checked = set()

        # Traiter par lots pour éviter de surcharger la mémoire
        for i in range(0, len(all_concepts), batch_size):
            batch = all_concepts[i : i + batch_size]

            # Pour chaque concept dans le lot
            for idx, concept in enumerate(batch):
                concept_id = concept.get("concept_id")
                if not concept_id:
                    continue

                # Récupérer l'embedding
                concept_embedding = self._get_concept_embedding(concept)
                if not concept_embedding:
                    continue

                # Comparer avec tous les autres concepts
                for j in range(idx + 1, len(batch)):
                    other_concept = batch[j]
                    other_id = other_concept.get("concept_id")

                    if not other_id or concept_id == other_id:
                        continue

                    # Éviter les paires déjà vérifiées
                    pair_key = tuple(sorted([concept_id, other_id]))
                    if pair_key in pairs_checked:
                        continue

                    pairs_checked.add(pair_key)

                    # Vérifier si une relation existe déjà
                    if self._relation_exists(concept_id, other_id, "SIMILAR_TO"):
                        continue

                    # Récupérer l'embedding de l'autre concept
                    other_embedding = self._get_concept_embedding(other_concept)
                    if not other_embedding:
                        continue

                    # Calculer la similarité
                    similarity = self._calculate_similarity(
                        concept_embedding, other_embedding
                    )

                    if similarity >= threshold:
                        # Créer la relation
                        self.kg.add_relationship(
                            concept_id,
                            other_id,
                            "SIMILAR_TO",
                            {"similarity": similarity, "discovered": True},
                        )

                        # Si la relation est bidirectionnelle, créer dans l'autre sens aussi
                        if self.relation_types["SIMILAR_TO"]["bidirectional"]:
                            self.kg.add_relationship(
                                other_id,
                                concept_id,
                                "SIMILAR_TO",
                                {"similarity": similarity, "discovered": True},
                            )

                        discovered_relations.append(
                            {
                                "source": concept_id,
                                "target": other_id,
                                "relation_type": "SIMILAR_TO",
                                "similarity": similarity,
                            }
                        )

                        if len(discovered_relations) >= limit:
                            return discovered_relations

        return discovered_relations

    def discover_textual_relations(self, concept_id: str) -> List[Dict[str, Any]]:
        """
        Découvre des relations potentielles basées sur l'analyse textuelle.

        Args:
            concept_id (str): ID du concept à analyser

        Returns:
            List[Dict[str, Any]]: Liste des relations découvertes
        """
        # Récupérer le concept
        concept = self.kg.get_concept(concept_id)
        if not concept:
            self.logger.error(f"Concept non trouvé: {concept_id}")
            return []

        discovered_relations = []

        # Analyser le texte du concept (nom et description)
        name = concept.get("name", "")
        description = concept.get("description", "")
        text = f"{name}: {description}"

        # Pour chaque type de relation ayant des motifs
        for relation_type, relation_info in self.relation_types.items():
            if "patterns" not in relation_info:
                continue

            patterns = relation_info["patterns"]
            threshold = relation_info.get("threshold", 0.7)

            for pattern in patterns:
                # Rechercher les correspondances
                matches = re.finditer(pattern, text)

                for match in matches:
                    # Analyser le contexte autour de la correspondance
                    match_text = match.group(0)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end]

                    # Rechercher des concepts potentiellement reliés
                    potential_targets = self._find_potential_targets(
                        context, concept_id, relation_type, threshold
                    )

                    # Ajouter les relations découvertes
                    for target in potential_targets:
                        target_id = target.get("concept_id")
                        confidence = target.get("confidence", 0.0)

                        if target_id and confidence >= threshold:
                            # Éviter d'ajouter des relations existantes
                            if self._relation_exists(
                                concept_id, target_id, relation_type
                            ):
                                continue

                            # Créer la relation
                            self.kg.add_relationship(
                                concept_id,
                                target_id,
                                relation_type,
                                {
                                    "confidence": confidence,
                                    "discovered": True,
                                    "context": context,
                                },
                            )

                            discovered_relations.append(
                                {
                                    "source": concept_id,
                                    "target": target_id,
                                    "relation_type": relation_type,
                                    "confidence": confidence,
                                    "context": context,
                                    "match": match_text,
                                }
                            )

        return discovered_relations

    def suggest_relations(
        self, concept_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Suggère des relations potentielles pour un concept donné.

        Args:
            concept_id (str): ID du concept
            limit (int, optional): Nombre maximal de suggestions. Par défaut à 5.

        Returns:
            List[Dict[str, Any]]: Liste des relations suggérées
        """
        concept = self.kg.get_concept(concept_id)
        if not concept:
            self.logger.error(f"Concept non trouvé: {concept_id}")
            return []

        # Récupérer l'embedding du concept
        embedding = self._get_concept_embedding_by_id(concept_id)
        if not embedding:
            return []

        # Trouver des concepts similaires
        similar_concepts = self.vs.search_similar(
            query=f"{concept.get('name', '')}: {concept.get('description', '')}",
            limit=20,  # Chercher plus que nécessaire pour avoir plus d'options
        )

        # Filtrer le concept lui-même
        similar_concepts = [
            c for c in similar_concepts if c.get("concept_id") != concept_id
        ]

        # Suggérer des relations
        suggestions = []

        # Relations de similarité
        for similar in similar_concepts[:limit]:
            target_id = similar.get("concept_id")
            if not target_id:
                continue

            # Éviter de suggérer des relations existantes
            if self._relation_exists(concept_id, target_id, "SIMILAR_TO"):
                continue

            # Calculer la similarité plus précisément
            target_embedding = self._get_concept_embedding_by_id(target_id)
            if not target_embedding:
                continue

            similarity = self._calculate_similarity(embedding, target_embedding)

            suggestions.append(
                {
                    "source": concept_id,
                    "target": target_id,
                    "target_name": similar.get("name", ""),
                    "relation_type": "SIMILAR_TO",
                    "confidence": similarity,
                    "already_exists": False,
                }
            )

            if len(suggestions) >= limit:
                break

        # Suggérer d'autres types de relations basées sur l'analyse textuelle
        textual_suggestions = self.discover_textual_relations(concept_id)

        # Ajouter les suggestions textuelles qui ne sont pas déjà dans la liste
        target_ids = {s["target"] for s in suggestions}

        for suggestion in textual_suggestions:
            target_id = suggestion.get("target")
            if target_id and target_id not in target_ids:
                target = self.kg.get_concept(target_id)
                if target:
                    suggestion["target_name"] = target.get("name", "")
                    suggestion["already_exists"] = False
                    suggestions.append(suggestion)
                    target_ids.add(target_id)

                    if len(suggestions) >= limit:
                        break

        return suggestions[:limit]

    def _get_all_concepts(self) -> List[Dict[str, Any]]:
        """
        Récupère tous les concepts du stockage vectoriel.

        Returns:
            List[Dict[str, Any]]: Liste de tous les concepts
        """
        query = """
        MATCH (c:Concept)
        WHERE NOT c.type = 'domain'
        RETURN c
        LIMIT 1000
        """

        try:
            with self.kg.driver.session(database=self.kg.database) as session:
                result = session.run(query)
                concept_ids = [dict(record["c"]) for record in result]

                # Récupérer les détails complets depuis le stockage vectoriel
                all_concepts = []
                for concept in concept_ids:
                    concept_id = concept.get("id")
                    if concept_id:
                        vector_data = self.vs.get_concept(concept_id)
                        if vector_data:
                            all_concepts.append(vector_data)

                return all_concepts
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des concepts: {e}")
            return []

    def _get_concept_embedding(self, concept: Dict[str, Any]) -> Optional[List[float]]:
        """
        Récupère ou génère l'embedding d'un concept.

        Args:
            concept (Dict[str, Any]): Données du concept

        Returns:
            Optional[List[float]]: Embedding du concept ou None
        """
        concept_id = concept.get("concept_id")
        name = concept.get("name", "")
        description = concept.get("description", "")

        if not concept_id or not (name or description):
            return None

        # Générer l'embedding du texte
        text = f"{name}: {description}"
        return self.vs.get_embedding(text)

    def _get_concept_embedding_by_id(self, concept_id: str) -> Optional[List[float]]:
        """
        Récupère l'embedding d'un concept par son ID.

        Args:
            concept_id (str): ID du concept

        Returns:
            Optional[List[float]]: Embedding du concept ou None
        """
        # Récupérer le concept depuis le stockage vectoriel
        concept = self.vs.get_concept(concept_id)
        if not concept:
            # Essayer depuis le graphe de connaissances
            concept_data = self.kg.get_concept(concept_id)
            if concept_data:
                name = concept_data.get("name", "")
                description = concept_data.get("description", "")
                text = f"{name}: {description}"
                return self.vs.get_embedding(text)
            return None

        return self._get_concept_embedding(concept)

    def _calculate_similarity(
        self, embedding1: List[float], embedding2: List[float]
    ) -> float:
        """
        Calcule la similarité cosinus entre deux embeddings.

        Args:
            embedding1 (List[float]): Premier embedding
            embedding2 (List[float]): Second embedding

        Returns:
            float: Score de similarité entre 0 et 1
        """
        try:
            # Convertir en tableaux numpy
            vec1 = np.array(embedding1).reshape(1, -1)
            vec2 = np.array(embedding2).reshape(1, -1)

            # Calculer la similarité cosinus
            similarity = cosine_similarity(vec1, vec2)[0][0]

            # Normaliser entre 0 et 1
            return float(max(0.0, min(1.0, similarity)))
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul de similarité: {e}")
            return 0.0

    def _relation_exists(
        self, source_id: str, target_id: str, relation_type: str
    ) -> bool:
        """
        Vérifie si une relation existe déjà entre deux concepts.

        Args:
            source_id (str): ID du concept source
            target_id (str): ID du concept cible
            relation_type (str): Type de relation

        Returns:
            bool: True si la relation existe
        """
        query = f"""
        MATCH (source:Concept {{id: $source_id}})-[r:`{relation_type}`]->(target:Concept {{id: $target_id}})
        RETURN count(r) as count
        """

        try:
            with self.kg.driver.session(database=self.kg.database) as session:
                result = session.run(query, source_id=source_id, target_id=target_id)
                record = result.single()
                return record and record["count"] > 0
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification de relation: {e}")
            return False

    def _find_potential_targets(
        self, context: str, source_id: str, relation_type: str, threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Trouve des concepts potentiellement reliés dans un contexte textuel.

        Args:
            context (str): Texte contextuel
            source_id (str): ID du concept source
            relation_type (str): Type de relation
            threshold (float): Seuil de confiance minimum

        Returns:
            List[Dict[str, Any]]: Liste des cibles potentielles
        """
        # Rechercher des concepts similaires au contexte
        search_results = self.vs.search_similar(query=context, limit=10)

        # Filtrer le concept source
        candidates = [c for c in search_results if c.get("concept_id") != source_id]

        # Calculer la confiance en fonction de la similarité
        for candidate in candidates:
            confidence = candidate.get("certainty", 0.0)
            if isinstance(confidence, str):
                try:
                    confidence = float(confidence)
                except ValueError:
                    confidence = 0.0

            candidate["confidence"] = confidence

        # Filtrer par seuil
        return [c for c in candidates if c.get("confidence", 0.0) >= threshold]
