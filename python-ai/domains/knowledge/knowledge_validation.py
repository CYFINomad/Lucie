from typing import Dict, List, Any, Optional, Union, Tuple, Set
import logging
import re
import json
from enum import Enum
from .knowledge_graph import KnowledgeGraph
from .vector_store import VectorStore


class ValidationSeverity(str, Enum):
    """Niveaux de sévérité des problèmes de validation"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationRule(str, Enum):
    """Types de règles de validation"""

    CONCEPT_COMPLETENESS = "concept_completeness"
    RELATION_CONSISTENCY = "relation_consistency"
    ORPHANED_CONCEPTS = "orphaned_concepts"
    DUPLICATE_CONCEPTS = "duplicate_concepts"
    CIRCULAR_REFERENCES = "circular_references"
    SEMANTIC_CONSISTENCY = "semantic_consistency"


class KnowledgeValidation:
    """
    Service de validation de la qualité et de la cohérence des connaissances.
    Permet de détecter et corriger les incohérences dans le graphe de connaissances.
    """

    def __init__(self, knowledge_graph: KnowledgeGraph, vector_store: VectorStore):
        """
        Initialise le service de validation de connaissances.

        Args:
            knowledge_graph (KnowledgeGraph): Instance du graphe de connaissances
            vector_store (VectorStore): Instance du stockage vectoriel
        """
        self.kg = knowledge_graph
        self.vs = vector_store
        self.logger = logging.getLogger(__name__)
        self.rules = self._initialize_validation_rules()

    def _initialize_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialise les règles de validation.

        Returns:
            Dict[str, Dict[str, Any]]: Règles de validation configurées
        """
        return {
            ValidationRule.CONCEPT_COMPLETENESS.value: {
                "description": "Vérifie que les concepts ont tous les attributs requis",
                "severity": ValidationSeverity.WARNING,
                "required_fields": ["name", "description"],
                "enabled": True,
            },
            ValidationRule.RELATION_CONSISTENCY.value: {
                "description": "Vérifie que les relations pointent vers des concepts existants",
                "severity": ValidationSeverity.ERROR,
                "enabled": True,
            },
            ValidationRule.ORPHANED_CONCEPTS.value: {
                "description": "Identifie les concepts sans aucune relation",
                "severity": ValidationSeverity.INFO,
                "enabled": True,
            },
            ValidationRule.DUPLICATE_CONCEPTS.value: {
                "description": "Détecte les concepts potentiellement dupliqués",
                "severity": ValidationSeverity.WARNING,
                "similarity_threshold": 0.92,
                "enabled": True,
            },
            ValidationRule.CIRCULAR_REFERENCES.value: {
                "description": "Détecte les références circulaires dans les relations hiérarchiques",
                "severity": ValidationSeverity.ERROR,
                "hierarchy_relations": ["PART_OF", "TYPE_OF"],
                "enabled": True,
            },
            ValidationRule.SEMANTIC_CONSISTENCY.value: {
                "description": "Vérifie la cohérence sémantique des relations",
                "severity": ValidationSeverity.WARNING,
                "enabled": True,
            },
        }

    def validate_knowledge_base(self) -> Dict[str, Any]:
        """
        Exécute toutes les règles de validation activées sur la base de connaissances.

        Returns:
            Dict[str, Any]: Résumé des validations et problèmes détectés
        """
        results = {
            "summary": {"total_issues": 0, "errors": 0, "warnings": 0, "info": 0},
            "issues": [],
        }

        # Exécuter chaque règle de validation activée
        for rule_id, rule_config in self.rules.items():
            if not rule_config.get("enabled", False):
                continue

            self.logger.info(f"Exécution de la validation: {rule_id}")

            if rule_id == ValidationRule.CONCEPT_COMPLETENESS.value:
                issues = self.validate_concept_completeness()
            elif rule_id == ValidationRule.RELATION_CONSISTENCY.value:
                issues = self.validate_relation_consistency()
            elif rule_id == ValidationRule.ORPHANED_CONCEPTS.value:
                issues = self.validate_orphaned_concepts()
            elif rule_id == ValidationRule.DUPLICATE_CONCEPTS.value:
                issues = self.validate_duplicate_concepts()
            elif rule_id == ValidationRule.CIRCULAR_REFERENCES.value:
                issues = self.validate_circular_references()
            elif rule_id == ValidationRule.SEMANTIC_CONSISTENCY.value:
                issues = self.validate_semantic_consistency()
            else:
                self.logger.warning(f"Règle de validation inconnue: {rule_id}")
                continue

            # Mettre à jour les statistiques
            for issue in issues:
                severity = issue.get("severity", ValidationSeverity.INFO.value)
                results["summary"]["total_issues"] += 1

                if severity == ValidationSeverity.ERROR.value:
                    results["summary"]["errors"] += 1
                elif severity == ValidationSeverity.WARNING.value:
                    results["summary"]["warnings"] += 1
                else:
                    results["summary"]["info"] += 1

            # Ajouter les problèmes détectés
            results["issues"].extend(issues)

        return results

    def validate_concept_completeness(self) -> List[Dict[str, Any]]:
        """
        Vérifie que les concepts ont tous les attributs requis.

        Returns:
            List[Dict[str, Any]]: Problèmes détectés
        """
        issues = []
        rule_config = self.rules[ValidationRule.CONCEPT_COMPLETENESS.value]
        required_fields = rule_config.get("required_fields", [])

        query = """
        MATCH (c:Concept)
        RETURN c
        LIMIT 1000
        """

        try:
            with self.kg.driver.session(database=self.kg.database) as session:
                result = session.run(query)

                for record in result:
                    concept = dict(record["c"])
                    concept_id = concept.get("id")

                    # Vérifier les champs obligatoires
                    for field in required_fields:
                        if field not in concept or not concept[field]:
                            issues.append(
                                {
                                    "rule": ValidationRule.CONCEPT_COMPLETENESS.value,
                                    "severity": rule_config["severity"],
                                    "concept_id": concept_id,
                                    "description": f"Champ obligatoire manquant: '{field}'",
                                    "fix_suggestion": f"Ajouter le champ '{field}' au concept",
                                }
                            )
        except Exception as e:
            self.logger.error(
                f"Erreur lors de la validation de complétude des concepts: {e}"
            )

        return issues

    def validate_relation_consistency(self) -> List[Dict[str, Any]]:
        """
        Vérifie que les relations pointent vers des concepts existants.

        Returns:
            List[Dict[str, Any]]: Problèmes détectés
        """
        issues = []
        rule_config = self.rules[ValidationRule.RELATION_CONSISTENCY.value]

        query = """
        MATCH (source:Concept)-[r]->(target:Concept)
        RETURN source.id as source_id, type(r) as relation_type, target.id as target_id
        LIMIT 1000
        """

        try:
            with self.kg.driver.session(database=self.kg.database) as session:
                result = session.run(query)
                checked_ids = set()

                for record in result:
                    source_id = record["source_id"]
                    target_id = record["target_id"]
                    relation_type = record["relation_type"]

                    # Vérifier si les concepts existent à la fois dans Neo4j et Weaviate
                    for concept_id in (source_id, target_id):
                        if concept_id in checked_ids:
                            continue

                        checked_ids.add(concept_id)

                        # Vérifier dans Weaviate
                        vector_concept = self.vs.get_concept(concept_id)
                        if not vector_concept:
                            issues.append(
                                {
                                    "rule": ValidationRule.RELATION_CONSISTENCY.value,
                                    "severity": rule_config["severity"],
                                    "concept_id": concept_id,
                                    "description": f"Concept référencé dans une relation mais absent du stockage vectoriel",
                                    "fix_suggestion": "Synchroniser le stockage vectoriel avec le graphe de connaissances",
                                }
                            )
        except Exception as e:
            self.logger.error(
                f"Erreur lors de la validation de cohérence des relations: {e}"
            )

        return issues

    def validate_orphaned_concepts(self) -> List[Dict[str, Any]]:
        """
        Identifie les concepts sans aucune relation.

        Returns:
            List[Dict[str, Any]]: Problèmes détectés
        """
        issues = []
        rule_config = self.rules[ValidationRule.ORPHANED_CONCEPTS.value]

        query = """
        MATCH (c:Concept)
        WHERE NOT (c)--()
        RETURN c
        LIMIT 1000
        """

        try:
            with self.kg.driver.session(database=self.kg.database) as session:
                result = session.run(query)

                for record in result:
                    concept = dict(record["c"])
                    concept_id = concept.get("id")
                    concept_name = concept.get("name", "")

                    # Ignorer les concepts de type domaine
                    if concept.get("type") == "domain":
                        continue

                    issues.append(
                        {
                            "rule": ValidationRule.ORPHANED_CONCEPTS.value,
                            "severity": rule_config["severity"],
                            "concept_id": concept_id,
                            "concept_name": concept_name,
                            "description": f"Concept orphelin sans aucune relation: '{concept_name}'",
                            "fix_suggestion": "Ajouter des relations pertinentes ou supprimer le concept s'il n'est pas nécessaire",
                        }
                    )
        except Exception as e:
            self.logger.error(
                f"Erreur lors de la validation des concepts orphelins: {e}"
            )

        return issues

    def validate_duplicate_concepts(self) -> List[Dict[str, Any]]:
        """
        Détecte les concepts potentiellement dupliqués.

        Returns:
            List[Dict[str, Any]]: Problèmes détectés
        """
        issues = []
        rule_config = self.rules[ValidationRule.DUPLICATE_CONCEPTS.value]
        threshold = rule_config.get("similarity_threshold", 0.92)

        # Récupérer tous les concepts
        query = """
        MATCH (c:Concept)
        WHERE NOT c.type = 'domain'
        RETURN c
        LIMIT 1000
        """

        try:
            with self.kg.driver.session(database=self.kg.database) as session:
                result = session.run(query)
                concepts = []

                for record in result:
                    concept = dict(record["c"])
                    concepts.append(concept)

                # Pour chaque paire de concepts, vérifier la similarité textuelle et vectorielle
                pairs_checked = set()

                for i, concept1 in enumerate(concepts):
                    concept1_id = concept1.get("id")
                    concept1_name = concept1.get("name", "")
                    concept1_desc = concept1.get("description", "")

                    # Générer l'embedding pour le concept1
                    vector1 = self._get_concept_embedding(
                        concept1_id, concept1_name, concept1_desc
                    )
                    if not vector1:
                        continue

                    for j in range(i + 1, len(concepts)):
                        concept2 = concepts[j]
                        concept2_id = concept2.get("id")

                        # Éviter les paires déjà vérifiées
                        pair_key = tuple(sorted([concept1_id, concept2_id]))
                        if pair_key in pairs_checked:
                            continue

                        pairs_checked.add(pair_key)

                        concept2_name = concept2.get("name", "")
                        concept2_desc = concept2.get("description", "")

                        # Vérifier la similarité des noms si disponible
                        name_similarity = self._string_similarity(
                            concept1_name, concept2_name
                        )
                        if name_similarity >= threshold:
                            issues.append(
                                {
                                    "rule": ValidationRule.DUPLICATE_CONCEPTS.value,
                                    "severity": rule_config["severity"],
                                    "concept_id": concept1_id,
                                    "duplicate_id": concept2_id,
                                    "description": f"Noms très similaires: '{concept1_name}' et '{concept2_name}' ({name_similarity:.3f})",
                                    "fix_suggestion": f"Fusionner les concepts {concept1_id} et {concept2_id}, ou différencier leurs noms",
                                }
                            )
                            continue

                        # Générer l'embedding pour le concept2
                        vector2 = self._get_concept_embedding(
                            concept2_id, concept2_name, concept2_desc
                        )
                        if not vector2:
                            continue

                        # Calculer la similarité vectorielle
                        from sklearn.metrics.pairwise import cosine_similarity
                        import numpy as np

                        vec1 = np.array(vector1).reshape(1, -1)
                        vec2 = np.array(vector2).reshape(1, -1)
                        similarity = float(cosine_similarity(vec1, vec2)[0][0])

                        if similarity >= threshold:
                            issues.append(
                                {
                                    "rule": ValidationRule.DUPLICATE_CONCEPTS.value,
                                    "severity": rule_config["severity"],
                                    "concept_id": concept1_id,
                                    "duplicate_id": concept2_id,
                                    "similarity": similarity,
                                    "description": f"Concepts sémantiquement très similaires ({similarity:.3f})",
                                    "fix_suggestion": f"Vérifier si les concepts {concept1_id} et {concept2_id} doivent être fusionnés",
                                }
                            )
        except Exception as e:
            self.logger.error(
                f"Erreur lors de la validation des concepts dupliqués: {e}"
            )

        return issues

    def validate_circular_references(self) -> List[Dict[str, Any]]:
        """
        Détecte les références circulaires dans les relations hiérarchiques.

        Returns:
            List[Dict[str, Any]]: Problèmes détectés
        """
        issues = []
        rule_config = self.rules[ValidationRule.CIRCULAR_REFERENCES.value]
        hierarchy_relations = rule_config.get(
            "hierarchy_relations", ["PART_OF", "TYPE_OF"]
        )

        # Construire la clause Cypher pour les types de relations hiérarchiques
        relation_types = "|".join([f"`{r}`" for r in hierarchy_relations])

        query = f"""
        MATCH path = (c:Concept)-[:{relation_types}*2..10]->(c)
        RETURN c.id as concept_id, c.name as concept_name, [rel in relationships(path) | type(rel)] as relation_path
        LIMIT 100
        """

        try:
            with self.kg.driver.session(database=self.kg.database) as session:
                result = session.run(query)

                for record in result:
                    concept_id = record["concept_id"]
                    concept_name = record["concept_name"]
                    relation_path = record["relation_path"]

                    issues.append(
                        {
                            "rule": ValidationRule.CIRCULAR_REFERENCES.value,
                            "severity": rule_config["severity"],
                            "concept_id": concept_id,
                            "concept_name": concept_name,
                            "description": f"Référence circulaire détectée pour '{concept_name}' avec les relations: {relation_path}",
                            "fix_suggestion": "Identifier et supprimer au moins une des relations dans la boucle",
                        }
                    )
        except Exception as e:
            self.logger.error(
                f"Erreur lors de la validation des références circulaires: {e}"
            )

        return issues

    def validate_semantic_consistency(self) -> List[Dict[str, Any]]:
        """
        Vérifie la cohérence sémantique des relations.

        Returns:
            List[Dict[str, Any]]: Problèmes détectés
        """
        issues = []
        rule_config = self.rules[ValidationRule.SEMANTIC_CONSISTENCY.value]

        query = """
        MATCH (source:Concept)-[r]->(target:Concept)
        RETURN source.id as source_id, source.name as source_name, 
               target.id as target_id, target.name as target_name,
               type(r) as relation_type
        LIMIT 1000
        """

        try:
            with self.kg.driver.session(database=self.kg.database) as session:
                result = session.run(query)

                for record in result:
                    source_id = record["source_id"]
                    source_name = record["source_name"]
                    target_id = record["target_id"]
                    target_name = record["target_name"]
                    relation_type = record["relation_type"]

                    # Pour chaque relation, vérifier la cohérence sémantique
                    # On utilise un système simple basé sur les embeddings pour estimer
                    # si la relation est sémantiquement cohérente
                    consistency_score = self._check_relation_consistency(
                        source_id, source_name, target_id, target_name, relation_type
                    )

                    if consistency_score < 0.5:  # Seuil arbitraire de cohérence
                        issues.append(
                            {
                                "rule": ValidationRule.SEMANTIC_CONSISTENCY.value,
                                "severity": rule_config["severity"],
                                "source_id": source_id,
                                "source_name": source_name,
                                "target_id": target_id,
                                "target_name": target_name,
                                "relation_type": relation_type,
                                "consistency_score": consistency_score,
                                "description": f"Relation potentiellement incohérente: '{source_name}' -{relation_type}-> '{target_name}' (score: {consistency_score:.2f})",
                                "fix_suggestion": "Vérifier si cette relation est appropriée ou si un autre type de relation serait plus adapté",
                            }
                        )
        except Exception as e:
            self.logger.error(
                f"Erreur lors de la validation de la cohérence sémantique: {e}"
            )

        return issues

    def fix_issues(
        self, issues: List[Dict[str, Any]], auto_fix: bool = False
    ) -> Dict[str, Any]:
        """
        Applique des corrections pour les problèmes détectés.

        Args:
            issues (List[Dict[str, Any]]): Liste des problèmes à corriger
            auto_fix (bool, optional): Appliquer automatiquement les corrections possibles. Par défaut à False.

        Returns:
            Dict[str, Any]: Résumé des corrections appliquées
        """
        results = {"fixed": [], "manual_fix_required": [], "failed": []}

        for issue in issues:
            rule = issue.get("rule")

            try:
                # Appliquer la correction appropriée selon le type de problème
                if rule == ValidationRule.CONCEPT_COMPLETENESS.value:
                    # Les problèmes de complétude nécessitent généralement une intervention manuelle
                    results["manual_fix_required"].append(issue)

                elif rule == ValidationRule.RELATION_CONSISTENCY.value and auto_fix:
                    # Synchroniser le stockage vectoriel avec le graphe
                    concept_id = issue.get("concept_id")
                    if concept_id:
                        concept = self.kg.get_concept(concept_id)
                        if concept:
                            # Ajouter au stockage vectoriel
                            success = self.vs.add_concept(
                                concept_id=concept_id,
                                name=concept.get("name", ""),
                                description=concept.get("description", ""),
                                category=concept.get("category", "general"),
                            )

                            if success:
                                results["fixed"].append(
                                    {
                                        **issue,
                                        "action": "Concept ajouté au stockage vectoriel",
                                    }
                                )
                            else:
                                results["failed"].append(
                                    {
                                        **issue,
                                        "error": "Échec de l'ajout au stockage vectoriel",
                                    }
                                )
                        else:
                            results["failed"].append(
                                {**issue, "error": "Concept introuvable dans le graphe"}
                            )
                    else:
                        results["failed"].append(
                            {**issue, "error": "ID de concept manquant"}
                        )

                elif rule == ValidationRule.ORPHANED_CONCEPTS.value:
                    # Les concepts orphelins nécessitent une intervention manuelle
                    results["manual_fix_required"].append(issue)

                elif rule == ValidationRule.DUPLICATE_CONCEPTS.value and auto_fix:
                    # Fusionner les concepts dupliqués
                    concept_id = issue.get("concept_id")
                    duplicate_id = issue.get("duplicate_id")

                    if concept_id and duplicate_id:
                        # Marquer l'un des concepts comme un alias de l'autre
                        success = self._merge_duplicate_concepts(
                            concept_id, duplicate_id
                        )

                        if success:
                            results["fixed"].append(
                                {
                                    **issue,
                                    "action": f"Concepts {concept_id} et {duplicate_id} fusionnés",
                                }
                            )
                        else:
                            results["failed"].append(
                                {**issue, "error": "Échec de la fusion"}
                            )
                    else:
                        results["failed"].append(
                            {**issue, "error": "IDs de concepts manquants"}
                        )

                elif rule == ValidationRule.CIRCULAR_REFERENCES.value and auto_fix:
                    # Supprimer une relation dans la boucle
                    # (Nécessite généralement une intervention manuelle)
                    results["manual_fix_required"].append(issue)

                elif rule == ValidationRule.SEMANTIC_CONSISTENCY.value:
                    # Cohérence sémantique nécessite une intervention manuelle
                    results["manual_fix_required"].append(issue)

                else:
                    # Si auto_fix est désactivé ou le type n'est pas reconnu
                    results["manual_fix_required"].append(issue)

            except Exception as e:
                self.logger.error(f"Erreur lors de la correction d'un problème: {e}")
                results["failed"].append({**issue, "error": str(e)})

        return results

    def export_validation_report(self, results: Dict[str, Any], filepath: str) -> bool:
        """
        Exporte les résultats de validation dans un fichier JSON.

        Args:
            results (Dict[str, Any]): Résultats de validation
            filepath (str): Chemin du fichier de sortie

        Returns:
            bool: True si l'exportation a réussi
        """
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'exportation du rapport: {e}")
            return False

    def _string_similarity(self, str1: str, str2: str) -> float:
        """
        Calcule la similarité entre deux chaînes de caractères.
        Utilise la distance de Levenshtein normalisée.

        Args:
            str1 (str): Première chaîne
            str2 (str): Deuxième chaîne

        Returns:
            float: Score de similarité entre 0 et 1
        """
        if not str1 and not str2:
            return 1.0
        if not str1 or not str2:
            return 0.0

        # Normaliser
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()

        if str1 == str2:
            return 1.0

        # Importer la fonction de distance de Levenshtein
        try:
            import Levenshtein

            distance = Levenshtein.distance(str1, str2)
            max_len = max(len(str1), len(str2))
            return 1.0 - (distance / max_len)
        except ImportError:
            # Fallback simple si le module n'est pas disponible
            # Compare les premiers caractères comme estimation grossière
            min_len = min(len(str1), len(str2))
            common_prefix_len = 0
            for i in range(min_len):
                if str1[i] == str2[i]:
                    common_prefix_len += 1
                else:
                    break
            return common_prefix_len / max(len(str1), len(str2))

    def _get_concept_embedding(
        self, concept_id: str, name: str = "", description: str = ""
    ) -> Optional[List[float]]:
        """
        Récupère l'embedding d'un concept.

        Args:
            concept_id (str): ID du concept
            name (str, optional): Nom du concept si disponible
            description (str, optional): Description du concept si disponible

        Returns:
            Optional[List[float]]: Embedding du concept
        """
        # Essayer de récupérer depuis le stockage vectoriel
        concept = self.vs.get_concept(concept_id)
        if concept:
            text = f"{concept.get('name', '')}: {concept.get('description', '')}"
            return self.vs.get_embedding(text)

        # Générer à partir des données fournies si disponibles
        if name or description:
            text = f"{name}: {description}"
            return self.vs.get_embedding(text)

        return None

    def _check_relation_consistency(
        self,
        source_id: str,
        source_name: str,
        target_id: str,
        target_name: str,
        relation_type: str,
    ) -> float:
        """
        Vérifie la cohérence sémantique d'une relation.

        Args:
            source_id (str): ID du concept source
            source_name (str): Nom du concept source
            target_id (str): ID du concept cible
            target_name (str): Nom du concept cible
            relation_type (str): Type de relation

        Returns:
            float: Score de cohérence entre 0 et 1
        """
        # Modèle de vérification simple basé sur la similarité vectorielle
        # et des heuristiques spécifiques au type de relation

        # Obtenir les embeddings
        source_embedding = self._get_concept_embedding(source_id, source_name)
        target_embedding = self._get_concept_embedding(target_id, target_name)

        if not source_embedding or not target_embedding:
            return 0.5  # Valeur par défaut si pas assez d'information

        # Calculer la similarité de base
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np

        vec1 = np.array(source_embedding).reshape(1, -1)
        vec2 = np.array(target_embedding).reshape(1, -1)
        similarity = float(cosine_similarity(vec1, vec2)[0][0])

        # Ajuster selon le type de relation
        if relation_type == "SIMILAR_TO":
            # Pour "SIMILAR_TO", la similarité devrait être élevée
            return similarity
        elif relation_type in ("PART_OF", "TYPE_OF"):
            # Pour les relations hiérarchiques, une certaine similarité est attendue
            # mais pas trop élevée (sinon ils seraient plutôt "SIMILAR_TO")
            if 0.3 <= similarity <= 0.8:
                return 0.8  # Bonne cohérence
            else:
                return max(0.3, min(similarity, 0.6))  # Limiter entre 0.3 et 0.6
        elif relation_type == "CAUSES":
            # Pas d'heuristique spéciale, mais maintenir un seuil minimum
            return max(0.4, similarity)
        else:
            # Pour les autres types, utiliser la similarité comme indicateur de base
            return similarity

    def _merge_duplicate_concepts(self, primary_id: str, duplicate_id: str) -> bool:
        """
        Fusionne deux concepts dupliqués.

        Args:
            primary_id (str): ID du concept à conserver
            duplicate_id (str): ID du concept à marquer comme dupliqué

        Returns:
            bool: True si la fusion a réussi
        """
        try:
            # 1. Récupérer les concepts
            primary = self.kg.get_concept(primary_id)
            duplicate = self.kg.get_concept(duplicate_id)

            if not primary or not duplicate:
                self.logger.error(
                    f"Impossible de fusionner: un des concepts est introuvable"
                )
                return False

            # 2. Marquer le doublon comme un alias
            duplicate_update = {
                **duplicate,
                "is_alias_of": primary_id,
                "status": "merged",
            }

            self.kg.add_concept(duplicate_id, duplicate_update)

            # 3. Transférer les relations du doublon vers le concept principal
            self._transfer_relationships(duplicate_id, primary_id)

            # 4. Mettre à jour le stockage vectoriel
            primary_vector = self.vs.get_concept(primary_id)
            duplicate_vector = self.vs.get_concept(duplicate_id)

            if primary_vector and duplicate_vector:
                # Marquer le doublon dans le stockage vectoriel
                self.vs.add_concept(
                    concept_id=duplicate_id,
                    name=f"[ALIAS] {duplicate_vector.get('name', '')}",
                    description=f"Alias de {primary_id}: {duplicate_vector.get('description', '')}",
                    category=duplicate_vector.get("category", "general"),
                )

            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la fusion des concepts: {e}")
            return False

    def _transfer_relationships(self, from_id: str, to_id: str) -> bool:
        """
        Transfère les relations d'un concept vers un autre.

        Args:
            from_id (str): ID du concept source
            to_id (str): ID du concept cible

        Returns:
            bool: True si le transfert a réussi
        """
        # 1. Récupérer toutes les relations entrantes
        query_in = f"""
        MATCH (source:Concept)-[r]->(target:Concept {{id: $from_id}})
        WHERE source.id <> $to_id
        RETURN source.id as source_id, type(r) as relation_type, properties(r) as properties
        """

        # 2. Récupérer toutes les relations sortantes
        query_out = f"""
        MATCH (source:Concept {{id: $from_id}})-[r]->(target:Concept)
        WHERE target.id <> $to_id
        RETURN target.id as target_id, type(r) as relation_type, properties(r) as properties
        """

        try:
            with self.kg.driver.session(database=self.kg.database) as session:
                # Traiter les relations entrantes
                result_in = session.run(query_in, from_id=from_id, to_id=to_id)
                for record in result_in:
                    source_id = record["source_id"]
                    relation_type = record["relation_type"]
                    properties = record["properties"]

                    # Créer la relation vers le nouveau concept
                    self.kg.add_relationship(
                        source_id, to_id, relation_type, properties
                    )

                # Traiter les relations sortantes
                result_out = session.run(query_out, from_id=from_id, to_id=to_id)
                for record in result_out:
                    target_id = record["target_id"]
                    relation_type = record["relation_type"]
                    properties = record["properties"]

                    # Créer la relation depuis le nouveau concept
                    self.kg.add_relationship(
                        to_id, target_id, relation_type, properties
                    )

            return True
        except Exception as e:
            self.logger.error(f"Erreur lors du transfert des relations: {e}")
            return False
