from typing import Dict, List, Any, Optional, Union, Set, Tuple
import logging
import json
from enum import Enum
from .knowledge_graph import KnowledgeGraph
from .vector_store import VectorStore


class DomainType(str, Enum):
    """Types de domaines de connaissances"""

    GENERAL = "general"
    SCIENCE = "science"
    TECHNOLOGY = "technology"
    ARTS = "arts"
    HISTORY = "history"
    MATHEMATICS = "mathematics"
    CUSTOM = "custom"


class CrossDomainKnowledgeGraph:
    """
    Gestionnaire de graphe de connaissances multi-domaines.
    Permet d'organiser et de relier les connaissances provenant de différents domaines.
    """

    def __init__(self, knowledge_graph: KnowledgeGraph, vector_store: VectorStore):
        """
        Initialise le gestionnaire de graphe de connaissances multi-domaines.

        Args:
            knowledge_graph (KnowledgeGraph): Instance du graphe de connaissances
            vector_store (VectorStore): Instance du stockage vectoriel
        """
        self.kg = knowledge_graph
        self.vs = vector_store
        self.logger = logging.getLogger(__name__)
        self.domains = {}
        self._initialize_domains()

    def _initialize_domains(self):
        """Initialise les domaines de connaissances de base."""
        for domain in DomainType:
            self._ensure_domain_exists(domain.value)

    def _ensure_domain_exists(self, domain_name: str) -> bool:
        """
        S'assure qu'un domaine existe dans le graphe de connaissances.

        Args:
            domain_name (str): Nom du domaine

        Returns:
            bool: True si le domaine existe ou a été créé avec succès
        """
        # Vérifier si le domaine existe déjà
        domain_id = f"domain:{domain_name}"
        domain = self.kg.get_concept(domain_id)

        if not domain:
            # Créer le domaine s'il n'existe pas
            properties = {
                "name": domain_name,
                "type": "domain",
                "description": f"Domain de connaissances: {domain_name}",
            }

            result = self.kg.add_concept(domain_id, properties)
            if result:
                self.logger.info(f"Domaine créé: {domain_name}")
                self.domains[domain_name] = domain_id

                # Ajouter également à l'index vectoriel
                try:
                    self.vs.add_concept(
                        concept_id=domain_id,
                        name=domain_name,
                        description=f"Domain de connaissances: {domain_name}",
                        category="domain",
                    )
                except Exception as e:
                    self.logger.error(
                        f"Erreur lors de l'ajout du domaine au stockage vectoriel: {e}"
                    )
            else:
                self.logger.error(f"Échec de la création du domaine: {domain_name}")
                return False
        else:
            self.domains[domain_name] = domain_id

        return True

    def add_concept_to_domain(
        self, concept_id: str, domain_name: str, concept_properties: Dict[str, Any]
    ) -> bool:
        """
        Ajoute un concept à un domaine spécifique.

        Args:
            concept_id (str): Identifiant du concept
            domain_name (str): Nom du domaine
            concept_properties (Dict[str, Any]): Propriétés du concept

        Returns:
            bool: True si le concept a été ajouté avec succès
        """
        # S'assurer que le domaine existe
        if not self._ensure_domain_exists(domain_name):
            return False

        domain_id = self.domains.get(domain_name)
        if not domain_id:
            self.logger.error(f"Domaine non trouvé: {domain_name}")
            return False

        # Ajouter le concept au graphe de connaissances
        result = self.kg.add_concept(concept_id, concept_properties)
        if not result:
            self.logger.error(f"Échec de l'ajout du concept: {concept_id}")
            return False

        # Créer la relation entre le concept et le domaine
        relation = self.kg.add_relationship(
            concept_id, domain_id, "BELONGS_TO_DOMAIN", {"confidence": 1.0}
        )

        # Ajouter le concept au stockage vectoriel
        try:
            self.vs.add_concept(
                concept_id=concept_id,
                name=concept_properties.get("name", concept_id),
                description=concept_properties.get("description", ""),
                category=domain_name,
            )
        except Exception as e:
            self.logger.error(
                f"Erreur lors de l'ajout du concept au stockage vectoriel: {e}"
            )

        return relation

    def connect_concepts(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Dict[str, Any] = None,
    ) -> bool:
        """
        Connecte deux concepts avec une relation spécifique.

        Args:
            source_id (str): ID du concept source
            target_id (str): ID du concept cible
            relation_type (str): Type de relation
            properties (Dict[str, Any], optional): Propriétés de la relation. Par défaut à None.

        Returns:
            bool: True si la relation a été créée avec succès
        """
        if properties is None:
            properties = {}

        return self.kg.add_relationship(source_id, target_id, relation_type, properties)

    def get_domain_concepts(
        self, domain_name: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Récupère tous les concepts appartenant à un domaine spécifique.

        Args:
            domain_name (str): Nom du domaine
            limit (int, optional): Limite de résultats. Par défaut à 100.

        Returns:
            List[Dict[str, Any]]: Liste des concepts du domaine
        """
        domain_id = self.domains.get(domain_name)
        if not domain_id:
            self.logger.error(f"Domaine non trouvé: {domain_name}")
            return []

        # Requête pour trouver les concepts reliés au domaine
        query = f"""
        MATCH (c:Concept)-[:BELONGS_TO_DOMAIN]->(d:Concept {{id: $domain_id}})
        RETURN c
        LIMIT $limit
        """

        try:
            with self.kg.driver.session(database=self.kg.database) as session:
                result = session.run(query, domain_id=domain_id, limit=limit)
                concepts = [dict(record["c"]) for record in result]
                return concepts
        except Exception as e:
            self.logger.error(
                f"Erreur lors de la récupération des concepts du domaine: {e}"
            )
            return []

    def cross_domain_search(
        self, query: str, source_domain: str, target_domains: List[str], limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recherche des concepts dans le domaine source et renvoie des concepts similaires
        dans les domaines cibles.

        Args:
            query (str): Requête de recherche
            source_domain (str): Domaine source
            target_domains (List[str]): Domaines cibles
            limit (int, optional): Limite de résultats par domaine. Par défaut à 5.

        Returns:
            List[Dict[str, Any]]: Résultats de recherche multi-domaines
        """
        results = {}

        # Étape 1: Recherche vectorielle dans le domaine source
        source_results = self.vs.search_similar(
            query=query, limit=limit, category=source_domain
        )

        results[source_domain] = source_results

        # Étape 2: Pour chaque concept trouvé, rechercher des concepts similaires dans les domaines cibles
        cross_domain_results = {}

        for domain in target_domains:
            cross_domain_results[domain] = []

        for result in source_results:
            concept_id = result.get("concept_id")
            if not concept_id:
                continue

            # Récupérer les détails du concept
            concept = self.kg.get_concept(concept_id)
            if not concept:
                continue

            # Construire une requête pour la recherche de concepts similaires
            concept_query = (
                f"{concept.get('name', '')}: {concept.get('description', '')}"
            )

            # Rechercher dans chaque domaine cible
            for domain in target_domains:
                similar_concepts = self.vs.search_similar(
                    query=concept_query, limit=limit, category=domain
                )

                # Ajouter les résultats au domaine correspondant
                for similar in similar_concepts:
                    # Éviter les doublons
                    if similar not in cross_domain_results[domain]:
                        cross_domain_results[domain].append(similar)

        # Fusionner les résultats
        for domain, concepts in cross_domain_results.items():
            results[domain] = concepts

        return results

    def get_bridging_concepts(
        self, domain1: str, domain2: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Trouve des concepts qui peuvent servir de pont entre deux domaines.

        Args:
            domain1 (str): Premier domaine
            domain2 (str): Second domaine
            limit (int, optional): Limite de résultats. Par défaut à 5.

        Returns:
            List[Dict[str, Any]]: Concepts qui sont utilisés dans les deux domaines
        """
        domain_id1 = self.domains.get(domain1)
        domain_id2 = self.domains.get(domain2)

        if not domain_id1 or not domain_id2:
            self.logger.error(f"Domaine(s) non trouvé(s): {domain1} ou {domain2}")
            return []

        # Requête pour trouver des concepts reliés aux deux domaines
        query = f"""
        MATCH (c:Concept)-[:BELONGS_TO_DOMAIN]->(d1:Concept {{id: $domain_id1}})
        MATCH (c)-[:BELONGS_TO_DOMAIN]->(d2:Concept {{id: $domain_id2}})
        RETURN c
        LIMIT $limit
        """

        try:
            with self.kg.driver.session(database=self.kg.database) as session:
                result = session.run(
                    query, domain_id1=domain_id1, domain_id2=domain_id2, limit=limit
                )
                concepts = [dict(record["c"]) for record in result]

                # Si aucun concept direct n'est trouvé, chercher des concepts connectés
                if not concepts:
                    self.logger.info(
                        f"Aucun concept commun trouvé entre {domain1} et {domain2}, recherche de connections"
                    )
                    # Recherche de concepts qui sont reliés entre les deux domaines
                    query2 = f"""
                    MATCH (c1:Concept)-[:BELONGS_TO_DOMAIN]->(d1:Concept {{id: $domain_id1}})
                    MATCH (c2:Concept)-[:BELONGS_TO_DOMAIN]->(d2:Concept {{id: $domain_id2}})
                    MATCH (c1)-[r]-(c2)
                    RETURN c1, c2, type(r) as relation_type
                    LIMIT $limit
                    """

                    result2 = session.run(
                        query2,
                        domain_id1=domain_id1,
                        domain_id2=domain_id2,
                        limit=limit,
                    )
                    for record in result2:
                        concepts.append(
                            {
                                "source_concept": dict(record["c1"]),
                                "target_concept": dict(record["c2"]),
                                "relation_type": record["relation_type"],
                            }
                        )

                return concepts
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche de concepts de pont: {e}")
            return []

    def export_domain_to_json(self, domain_name: str, filepath: str) -> bool:
        """
        Exporte tous les concepts d'un domaine vers un fichier JSON.

        Args:
            domain_name (str): Nom du domaine à exporter
            filepath (str): Chemin du fichier de sortie

        Returns:
            bool: True si l'exportation a réussi
        """
        concepts = self.get_domain_concepts(domain_name)
        if not concepts:
            self.logger.error(f"Aucun concept trouvé pour le domaine: {domain_name}")
            return False

        try:
            # Pour chaque concept, récupérer également ses relations
            enriched_concepts = []
            for concept in concepts:
                concept_id = concept.get("id")
                if concept_id:
                    # Récupérer les relations
                    related = self.kg.get_related_concepts(concept_id)
                    enriched_concept = {"concept": concept, "related": related}
                    enriched_concepts.append(enriched_concept)

            # Exporter vers JSON
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(
                    {"domain": domain_name, "concepts": enriched_concepts},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )

            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'exportation du domaine: {e}")
            return False

    def import_domain_from_json(self, filepath: str) -> bool:
        """
        Importe des concepts depuis un fichier JSON vers un domaine.

        Args:
            filepath (str): Chemin du fichier JSON à importer

        Returns:
            bool: True si l'importation a réussi
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            domain_name = data.get("domain")
            if not domain_name:
                self.logger.error("Domaine non spécifié dans le fichier JSON")
                return False

            # S'assurer que le domaine existe
            if not self._ensure_domain_exists(domain_name):
                return False

            # Importer les concepts
            concepts = data.get("concepts", [])
            for concept_data in concepts:
                concept = concept_data.get("concept")
                if not concept:
                    continue

                concept_id = concept.get("id")
                if not concept_id:
                    continue

                # Ajouter le concept au domaine
                self.add_concept_to_domain(concept_id, domain_name, concept)

                # Ajouter les relations
                related = concept_data.get("related", [])
                for relation in related:
                    target_concept = relation.get("concept")
                    path = relation.get("path", [])

                    if target_concept and path:
                        target_id = target_concept.get("id")
                        if target_id:
                            # Ajouter le concept cible s'il n'existe pas
                            if not self.kg.get_concept(target_id):
                                self.kg.add_concept(target_id, target_concept)

                            # Ajouter la relation
                            for step in path:
                                relation_type = step.get("type")
                                properties = step.get("properties", {})

                                if relation_type:
                                    self.kg.add_relationship(
                                        concept_id, target_id, relation_type, properties
                                    )

            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'importation du domaine: {e}")
            return False
