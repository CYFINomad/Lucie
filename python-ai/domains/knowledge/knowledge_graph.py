from typing import Dict, List, Any, Optional, Union, Set, Tuple
import logging
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError


class KnowledgeGraph:
    """
    Gestionnaire de graphe de connaissances utilisant Neo4j.
    Permet de stocker et récupérer des concepts et leurs relations.
    """

    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        """
        Initialise la connexion au graphe de connaissances Neo4j.

        Args:
            uri (str): URI du serveur Neo4j
            username (str): Nom d'utilisateur pour la connexion
            password (str): Mot de passe pour la connexion
            database (str, optional): Nom de la base de données. Par défaut à "neo4j".
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self.database = database
        self.logger = logging.getLogger(__name__)

    def close(self):
        """Ferme la connexion au driver Neo4j."""
        self.driver.close()

    def add_concept(self, concept_id: str, properties: Dict[str, Any]) -> bool:
        """
        Ajoute un nouveau concept au graphe de connaissances.

        Args:
            concept_id (str): Identifiant unique du concept
            properties (Dict[str, Any]): Propriétés du concept

        Returns:
            bool: True si le concept a été ajouté avec succès
        """
        query = """
        MERGE (c:Concept {id: $concept_id})
        SET c += $properties
        RETURN c
        """
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(
                    query, concept_id=concept_id, properties=properties
                )
                return result.single() is not None
        except Neo4jError as e:
            self.logger.error(f"Erreur lors de l'ajout du concept: {e}")
            return False

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Dict[str, Any] = None,
    ) -> bool:
        """
        Crée une relation entre deux concepts.

        Args:
            source_id (str): ID du concept source
            target_id (str): ID du concept cible
            relation_type (str): Type de relation
            properties (Dict[str, Any], optional): Propriétés de la relation

        Returns:
            bool: True si la relation a été créée avec succès
        """
        if properties is None:
            properties = {}

        query = """
        MATCH (source:Concept {id: $source_id})
        MATCH (target:Concept {id: $target_id})
        MERGE (source)-[r:`{relation_type}`]->(target)
        SET r += $properties
        RETURN r
        """.format(
            relation_type=relation_type
        )

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(
                    query,
                    source_id=source_id,
                    target_id=target_id,
                    properties=properties,
                )
                return result.single() is not None
        except Neo4jError as e:
            self.logger.error(f"Erreur lors de la création de la relation: {e}")
            return False

    def get_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un concept par son ID.

        Args:
            concept_id (str): ID du concept à récupérer

        Returns:
            Optional[Dict[str, Any]]: Données du concept ou None si non trouvé
        """
        query = """
        MATCH (c:Concept {id: $concept_id})
        RETURN c
        """
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, concept_id=concept_id)
                record = result.single()
                if record:
                    return dict(record["c"])
                return None
        except Neo4jError as e:
            self.logger.error(f"Erreur lors de la récupération du concept: {e}")
            return None

    def get_related_concepts(
        self, concept_id: str, relation_type: Optional[str] = None, max_depth: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Récupère les concepts reliés à un concept donné.

        Args:
            concept_id (str): ID du concept source
            relation_type (Optional[str], optional): Filtrer par type de relation
            max_depth (int, optional): Profondeur maximale de traversée. Par défaut à 1.

        Returns:
            List[Dict[str, Any]]: Liste des concepts reliés
        """
        relation_filter = f":`{relation_type}`" if relation_type else ""
        query = f"""
        MATCH (c:Concept {{id: $concept_id}})-[r{relation_filter}*1..{max_depth}]->(related)
        RETURN related, r
        """

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, concept_id=concept_id)
                related_concepts = []
                for record in result:
                    concept = dict(record["related"])
                    relations = record["r"]
                    related_concepts.append(
                        {
                            "concept": concept,
                            "path": [
                                {"type": r.type, "properties": dict(r)}
                                for r in relations
                            ],
                        }
                    )
                return related_concepts
        except Neo4jError as e:
            self.logger.error(
                f"Erreur lors de la récupération des concepts reliés: {e}"
            )
            return []

    def search_concepts(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recherche des concepts par texte.

        Args:
            query_text (str): Texte à rechercher
            limit (int, optional): Nombre maximum de résultats. Par défaut à 10.

        Returns:
            List[Dict[str, Any]]: Liste des concepts correspondants
        """
        # Utilisation de la recherche fulltext si configurée, sinon recherche simple
        query = """
        MATCH (c:Concept)
        WHERE c.name CONTAINS $query_text OR c.description CONTAINS $query_text
        RETURN c
        LIMIT $limit
        """

        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, query_text=query_text, limit=limit)
                return [dict(record["c"]) for record in result]
        except Neo4jError as e:
            self.logger.error(f"Erreur lors de la recherche de concepts: {e}")
            return []

    def delete_concept(self, concept_id: str) -> bool:
        """
        Supprime un concept du graphe.

        Args:
            concept_id (str): ID du concept à supprimer

        Returns:
            bool: True si le concept a été supprimé avec succès
        """
        query = """
        MATCH (c:Concept {id: $concept_id})
        DETACH DELETE c
        """
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, concept_id=concept_id)
                return result.consume().counters.nodes_deleted > 0
        except Neo4jError as e:
            self.logger.error(f"Erreur lors de la suppression du concept: {e}")
            return False
