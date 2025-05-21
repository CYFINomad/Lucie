from typing import Dict, List, Any, Optional, Union, Tuple
import logging
import numpy as np
import weaviate
from weaviate.exceptions import WeaviateException
from sentence_transformers import SentenceTransformer


class VectorStore:
    """
    Gestionnaire de stockage de vecteurs pour la recherche sémantique.
    Utilise Weaviate comme base de données vectorielle et SentenceTransformers pour les embeddings.
    """

    def __init__(
        self,
        weaviate_url: str,
        weaviate_api_key: Optional[str] = None,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialise le gestionnaire de stockage de vecteurs.

        Args:
            weaviate_url (str): URL du serveur Weaviate
            weaviate_api_key (Optional[str], optional): Clé API Weaviate. Par défaut à None.
            model_name (str, optional): Nom du modèle SentenceTransformer. Par défaut à "all-MiniLM-L6-v2".
        """
        self.logger = logging.getLogger(__name__)

        # Initialisation de l'encodeur de texte
        try:
            self.encoder = SentenceTransformer(model_name)
        except Exception as e:
            self.logger.error(
                f"Erreur lors de l'initialisation du modèle d'embedding: {e}"
            )
            raise

        # Connexion à Weaviate
        auth_config = (
            weaviate.auth.AuthApiKey(api_key=weaviate_api_key)
            if weaviate_api_key
            else None
        )
        try:
            self.client = weaviate.Client(
                url=weaviate_url, auth_client_secret=auth_config
            )
            self.logger.info(f"Connexion établie à Weaviate: {weaviate_url}")
        except Exception as e:
            self.logger.error(f"Erreur de connexion à Weaviate: {e}")
            raise

        # Vérification de la classe Concept
        self._ensure_schema_exists()

    def _ensure_schema_exists(self):
        """S'assure que le schéma nécessaire existe dans Weaviate."""
        concept_class = {
            "class": "Concept",
            "description": "Un concept de connaissances",
            "vectorizer": "none",  # Nous fournissons nos propres vecteurs
            "properties": [
                {
                    "name": "concept_id",
                    "dataType": ["string"],
                    "description": "Identifiant unique du concept",
                },
                {
                    "name": "name",
                    "dataType": ["string"],
                    "description": "Nom du concept",
                },
                {
                    "name": "description",
                    "dataType": ["text"],
                    "description": "Description du concept",
                },
                {
                    "name": "category",
                    "dataType": ["string"],
                    "description": "Catégorie du concept",
                },
                {
                    "name": "source",
                    "dataType": ["string"],
                    "description": "Source du concept",
                },
            ],
        }

        try:
            # Vérifier si la classe existe déjà
            schema = self.client.schema.get()
            existing_classes = (
                [c["class"] for c in schema["classes"]] if "classes" in schema else []
            )

            if "Concept" not in existing_classes:
                self.client.schema.create_class(concept_class)
                self.logger.info("Classe 'Concept' créée dans Weaviate")
        except WeaviateException as e:
            self.logger.error(f"Erreur lors de la création du schéma: {e}")
            raise

    def add_concept(
        self,
        concept_id: str,
        name: str,
        description: str,
        category: str = "general",
        source: str = "manual",
        custom_embedding: Optional[List[float]] = None,
    ) -> bool:
        """
        Ajoute un concept au stockage vectoriel.

        Args:
            concept_id (str): Identifiant unique du concept
            name (str): Nom du concept
            description (str): Description du concept
            category (str, optional): Catégorie du concept. Par défaut à "general".
            source (str, optional): Source du concept. Par défaut à "manual".
            custom_embedding (Optional[List[float]], optional): Embedding personnalisé.

        Returns:
            bool: True si le concept a été ajouté avec succès
        """
        try:
            # Générer l'embedding à partir du nom et de la description
            if custom_embedding is None:
                text_to_encode = f"{name}: {description}"
                embedding = self.encoder.encode(text_to_encode).tolist()
            else:
                embedding = custom_embedding

            # Vérifier si le concept existe déjà
            existing = (
                self.client.query.get("Concept", ["concept_id"])
                .with_where(
                    {
                        "path": ["concept_id"],
                        "operator": "Equal",
                        "valueString": concept_id,
                    }
                )
                .do()
            )

            # Supprimer le concept existant si nécessaire
            if "data" in existing and existing["data"]["Get"]["Concept"]:
                self.delete_concept(concept_id)

            # Ajouter le concept avec son embedding
            self.client.data_object.create(
                class_name="Concept",
                data_object={
                    "concept_id": concept_id,
                    "name": name,
                    "description": description,
                    "category": category,
                    "source": source,
                },
                vector=embedding,
            )
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajout du concept vectoriel: {e}")
            return False

    def search_similar(
        self, query: str, limit: int = 5, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recherche des concepts similaires à la requête.

        Args:
            query (str): Texte de la requête
            limit (int, optional): Nombre maximum de résultats. Par défaut à 5.
            category (Optional[str], optional): Filtrer par catégorie. Par défaut à None.

        Returns:
            List[Dict[str, Any]]: Liste des concepts similaires
        """
        try:
            # Générer l'embedding de la requête
            query_embedding = self.encoder.encode(query).tolist()

            # Construire la requête Weaviate
            weaviate_query = (
                self.client.query.get(
                    "Concept",
                    ["concept_id", "name", "description", "category", "source"],
                )
                .with_near_vector({"vector": query_embedding, "certainty": 0.7})
                .with_limit(limit)
            )

            # Ajouter un filtre par catégorie si spécifié
            if category:
                weaviate_query = weaviate_query.with_where(
                    {"path": ["category"], "operator": "Equal", "valueString": category}
                )

            result = weaviate_query.do()

            # Extraire les résultats
            if "data" in result and "Get" in result["data"]:
                concepts = result["data"]["Get"]["Concept"]
                return concepts
            return []
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche vectorielle: {e}")
            return []

    def get_embedding(self, text: str) -> List[float]:
        """
        Génère l'embedding d'un texte.

        Args:
            text (str): Texte à encoder

        Returns:
            List[float]: Vecteur d'embedding
        """
        try:
            return self.encoder.encode(text).tolist()
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération de l'embedding: {e}")
            return []

    def delete_concept(self, concept_id: str) -> bool:
        """
        Supprime un concept du stockage vectoriel.

        Args:
            concept_id (str): Identifiant du concept à supprimer

        Returns:
            bool: True si le concept a été supprimé avec succès
        """
        try:
            # Rechercher l'objet à supprimer
            result = (
                self.client.query.get("Concept", ["_additional {id}"])
                .with_where(
                    {
                        "path": ["concept_id"],
                        "operator": "Equal",
                        "valueString": concept_id,
                    }
                )
                .do()
            )

            # Supprimer l'objet s'il existe
            if (
                "data" in result
                and "Get" in result["data"]
                and result["data"]["Get"]["Concept"]
            ):
                uuid = result["data"]["Get"]["Concept"][0]["_additional"]["id"]
                self.client.data_object.delete(uuid, "Concept")
                return True

            return False
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression du concept: {e}")
            return False

    def get_concept(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un concept par son ID.

        Args:
            concept_id (str): ID du concept à récupérer

        Returns:
            Optional[Dict[str, Any]]: Données du concept ou None si non trouvé
        """
        try:
            result = (
                self.client.query.get(
                    "Concept",
                    ["concept_id", "name", "description", "category", "source"],
                )
                .with_where(
                    {
                        "path": ["concept_id"],
                        "operator": "Equal",
                        "valueString": concept_id,
                    }
                )
                .do()
            )

            if (
                "data" in result
                and "Get" in result["data"]
                and result["data"]["Get"]["Concept"]
            ):
                return result["data"]["Get"]["Concept"][0]

            return None
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du concept: {e}")
            return None
