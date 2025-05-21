from typing import Dict, List, Any, Optional, Union, Tuple
import logging
from .vector_store import VectorStore
from .knowledge_graph import KnowledgeGraph


class SemanticSearch:
    """
    Service de recherche sémantique qui combine la recherche vectorielle et le graphe de connaissances.
    Permet d'effectuer des recherches sémantiques enrichies par les relations structurées.
    """

    def __init__(self, vector_store: VectorStore, knowledge_graph: KnowledgeGraph):
        """
        Initialise le service de recherche sémantique.

        Args:
            vector_store (VectorStore): Instance du gestionnaire de stockage vectoriel
            knowledge_graph (KnowledgeGraph): Instance du graphe de connaissances
        """
        self.vector_store = vector_store
        self.knowledge_graph = knowledge_graph
        self.logger = logging.getLogger(__name__)

    def search(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None,
        enrich_with_relations: bool = True,
        relation_depth: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Effectue une recherche sémantique combinée.

        Args:
            query (str): Texte de la requête
            limit (int, optional): Nombre maximum de résultats. Par défaut à 5.
            category (Optional[str], optional): Filtrer par catégorie. Par défaut à None.
            enrich_with_relations (bool, optional): Enrichir les résultats avec des relations. Par défaut à True.
            relation_depth (int, optional): Profondeur des relations à récupérer. Par défaut à 1.

        Returns:
            List[Dict[str, Any]]: Résultats de recherche enrichis
        """
        # Étape 1: Recherche vectorielle
        self.logger.info(f"Recherche sémantique pour: '{query}'")
        vector_results = self.vector_store.search_similar(query, limit, category)

        if not vector_results:
            self.logger.info("Aucun résultat trouvé dans la recherche vectorielle")
            return []

        # Étape 2: Enrichissement avec le graphe de connaissances
        enriched_results = []

        for result in vector_results:
            concept_id = result.get("concept_id")
            enriched_result = {**result}

            if enrich_with_relations and concept_id:
                try:
                    # Récupérer les relations depuis le graphe de connaissances
                    related_concepts = self.knowledge_graph.get_related_concepts(
                        concept_id=concept_id, max_depth=relation_depth
                    )

                    # Ajouter les concepts reliés au résultat
                    enriched_result["related_concepts"] = related_concepts
                except Exception as e:
                    self.logger.error(
                        f"Erreur lors de l'enrichissement des relations: {e}"
                    )
                    enriched_result["related_concepts"] = []

            enriched_results.append(enriched_result)

        return enriched_results

    def search_by_concept(
        self,
        concept_id: str,
        relation_types: Optional[List[str]] = None,
        max_depth: int = 2,
    ) -> Dict[str, Any]:
        """
        Recherche à partir d'un concept spécifique.

        Args:
            concept_id (str): ID du concept de départ
            relation_types (Optional[List[str]], optional): Types de relations à suivre. Par défaut à None.
            max_depth (int, optional): Profondeur maximale de traversée. Par défaut à 2.

        Returns:
            Dict[str, Any]: Informations sur le concept et ses relations
        """
        # Récupérer le concept de base
        concept = self.knowledge_graph.get_concept(concept_id)
        if not concept:
            self.logger.info(f"Concept non trouvé: {concept_id}")
            return {}

        # Récupérer les vecteurs associés
        vector_data = self.vector_store.get_concept(concept_id)

        # Récupérer les relations
        related = []
        if relation_types:
            for relation_type in relation_types:
                related_concepts = self.knowledge_graph.get_related_concepts(
                    concept_id=concept_id,
                    relation_type=relation_type,
                    max_depth=max_depth,
                )
                related.extend(related_concepts)
        else:
            related = self.knowledge_graph.get_related_concepts(
                concept_id=concept_id, max_depth=max_depth
            )

        # Construire le résultat
        result = {
            "concept": concept,
            "vector_data": vector_data,
            "related_concepts": related,
        }

        return result

    def get_similar_concepts(
        self, concept_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Trouve des concepts similaires à un concept donné.

        Args:
            concept_id (str): ID du concept de référence
            limit (int, optional): Nombre maximum de résultats. Par défaut à 5.

        Returns:
            List[Dict[str, Any]]: Liste des concepts similaires
        """
        # Récupérer le concept depuis le stockage vectoriel
        concept = self.vector_store.get_concept(concept_id)
        if not concept:
            self.logger.info(f"Concept non trouvé pour la similarité: {concept_id}")
            return []

        # Utiliser le nom et la description pour la recherche
        query = f"{concept.get('name', '')}: {concept.get('description', '')}"

        # Exclure le concept lui-même des résultats
        results = self.vector_store.search_similar(query, limit + 1)

        # Filtrer le concept d'origine
        filtered_results = [r for r in results if r.get("concept_id") != concept_id]

        # Limiter aux résultats demandés
        return filtered_results[:limit]

    def multi_query_search(
        self, queries: List[str], limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Effectue une recherche avec plusieurs requêtes et combine les résultats.

        Args:
            queries (List[str]): Liste de requêtes
            limit (int, optional): Nombre maximum de résultats par requête. Par défaut à 3.

        Returns:
            List[Dict[str, Any]]: Résultats combinés
        """
        all_results = []
        concept_ids_seen = set()

        for query in queries:
            results = self.search(query, limit=limit, enrich_with_relations=False)

            # Ajouter uniquement les nouveaux résultats
            for result in results:
                concept_id = result.get("concept_id")
                if concept_id and concept_id not in concept_ids_seen:
                    all_results.append(result)
                    concept_ids_seen.add(concept_id)

        # Trier les résultats par pertinence (si un score est disponible)
        if all_results and "certainty" in all_results[0]:
            all_results.sort(key=lambda x: x.get("certainty", 0), reverse=True)

        return all_results
