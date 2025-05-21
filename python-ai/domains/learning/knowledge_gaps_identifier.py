from typing import Dict, List, Any, Optional, Union, Tuple, Set
import logging
import re
from collections import Counter
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from ..knowledge.knowledge_graph import KnowledgeGraph
from ..knowledge.vector_store import VectorStore
from ..knowledge.semantic_search import SemanticSearch


class KnowledgeGapsIdentifier:
    """
    Service d'identification des lacunes dans les connaissances.
    Analyse les interactions, questions et sources externes pour détecter les sujets
    manquants ou insuffisamment couverts dans la base de connaissances.
    """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        vector_store: VectorStore,
        semantic_search: Optional[SemanticSearch] = None,
        confidence_threshold: float = 0.75,
        min_gap_score: float = 0.6,
    ):
        """
        Initialise le service d'identification des lacunes.

        Args:
            knowledge_graph (KnowledgeGraph): Instance du graphe de connaissances
            vector_store (VectorStore): Instance du stockage vectoriel
            semantic_search (Optional[SemanticSearch], optional): Service de recherche sémantique
            confidence_threshold (float, optional): Seuil de confiance pour les réponses. Par défaut à 0.75.
            min_gap_score (float, optional): Score minimum pour considérer une lacune. Par défaut à 0.6.
        """
        self.logger = logging.getLogger(__name__)
        self.kg = knowledge_graph
        self.vs = vector_store
        self.semantic_search = semantic_search or SemanticSearch(
            vector_store, knowledge_graph
        )
        self.confidence_threshold = confidence_threshold
        self.min_gap_score = min_gap_score
        self.known_gaps = set()

    def analyze_question(self, question: str) -> Dict[str, Any]:
        """
        Analyse une question pour détecter d'éventuelles lacunes de connaissances.

        Args:
            question (str): Question à analyser

        Returns:
            Dict[str, Any]: Résultat de l'analyse avec lacunes potentielles
        """
        # Extraire les concepts clés de la question
        keywords = self._extract_keywords(question)

        # Recherche sémantique pour chaque concept clé
        search_results = []
        for keyword in keywords:
            results = self.semantic_search.search(
                query=keyword, limit=3, enrich_with_relations=True
            )
            search_results.extend(results)

        # Analyser les résultats pour détecter les lacunes
        coverage = self._analyze_coverage(keywords, search_results)
        missing_concepts = [
            k for k, v in coverage.items() if v < self.confidence_threshold
        ]

        # Calculer le score de confiance global
        if not keywords:
            avg_confidence = 1.0
        else:
            confidences = [v for k, v in coverage.items()]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Déterminer s'il y a une lacune
        has_knowledge_gap = avg_confidence < self.confidence_threshold

        # Construire le résultat
        result = {
            "question": question,
            "keywords": keywords,
            "missing_concepts": missing_concepts,
            "coverage": coverage,
            "confidence": avg_confidence,
            "has_knowledge_gap": has_knowledge_gap,
        }

        # Enregistrer la lacune si détectée
        if has_knowledge_gap:
            gap_signature = " ".join(sorted(missing_concepts))
            self.known_gaps.add(gap_signature)
            result["gap_signature"] = gap_signature

        return result

    def analyze_conversation_history(
        self, conversation: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Analyse l'historique d'une conversation pour détecter des lacunes récurrentes.

        Args:
            conversation (List[Dict[str, str]]): Historique de conversation avec questions et réponses

        Returns:
            List[Dict[str, Any]]: Liste des lacunes détectées
        """
        # Extraire et analyser les questions de la conversation
        questions = [
            msg["text"] for msg in conversation if msg.get("role", "").lower() == "user"
        ]

        analyses = [self.analyze_question(q) for q in questions]

        # Identifier les lacunes récurrentes
        recurring_gaps = self._find_recurring_gaps(analyses)

        return recurring_gaps

    def analyze_external_content(
        self, content: str, source: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Analyse du contenu externe pour identifier des connaissances manquantes.

        Args:
            content (str): Contenu textuel à analyser
            source (str, optional): Source du contenu. Par défaut à "unknown".

        Returns:
            Dict[str, Any]: Analyse des lacunes potentielles dans le contenu
        """
        # Extraire des paragraphes du contenu
        paragraphs = re.split(r"\n\s*\n", content)

        # Analyser chaque paragraphe
        paragraph_analyses = []
        all_keywords = set()
        potential_new_concepts = set()

        for paragraph in paragraphs:
            if len(paragraph.strip()) < 50:  # Ignorer les paragraphes trop courts
                continue

            keywords = self._extract_keywords(paragraph)
            all_keywords.update(keywords)

            # Vérifier la couverture de chaque concept
            for keyword in keywords:
                results = self.semantic_search.search(query=keyword, limit=3)

                # Si peu ou pas de résultats, c'est potentiellement un nouveau concept
                if not results or results[0].get("certainty", 0) < 0.6:
                    potential_new_concepts.add(keyword)

            # Vectoriser le paragraphe pour vérifier sa similarité globale
            paragraph_embedding = self.vs.get_embedding(paragraph)
            most_similar_content = self._find_most_similar_content(paragraph_embedding)

            paragraph_analyses.append(
                {
                    "text": (
                        paragraph[:100] + "..." if len(paragraph) > 100 else paragraph
                    ),
                    "keywords": list(keywords),
                    "best_match": most_similar_content.get("concept_id", ""),
                    "match_certainty": most_similar_content.get("certainty", 0),
                    "potentially_new": most_similar_content.get("certainty", 1) < 0.7,
                }
            )

        # Résumer l'analyse
        return {
            "source": source,
            "keywords": list(all_keywords),
            "potential_new_concepts": list(potential_new_concepts),
            "paragraph_analyses": paragraph_analyses,
            "new_knowledge_probability": len(potential_new_concepts)
            / max(1, len(all_keywords)),
        }

    def prioritize_knowledge_gaps(
        self, gaps: List[Dict[str, Any]], max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Priorise les lacunes de connaissances selon différents critères.

        Args:
            gaps (List[Dict[str, Any]]): Liste des lacunes identifiées
            max_results (int, optional): Nombre maximum de résultats. Par défaut à 10.

        Returns:
            List[Dict[str, Any]]: Lacunes priorisées
        """
        if not gaps:
            return []

        # Critères de priorisation:
        # 1. Fréquence d'apparition (gaps récurrents)
        # 2. Taille de la lacune (nombre de concepts manquants)
        # 3. Score de confiance (plus c'est bas, plus c'est prioritaire)

        for gap in gaps:
            # Calculer un score de priorité
            frequency = gap.get("frequency", 1)
            missing_concepts_count = len(gap.get("missing_concepts", []))
            confidence = gap.get("confidence", 0.5)

            # Formule de priorité: plus le score est élevé, plus c'est prioritaire
            gap["priority_score"] = (
                (frequency * 2)
                + (missing_concepts_count * 1.5)
                + ((1 - confidence) * 3)
            )

        # Trier par score de priorité
        prioritized = sorted(
            gaps, key=lambda x: x.get("priority_score", 0), reverse=True
        )

        return prioritized[:max_results]

    def suggest_learning_topics(
        self, keywords: List[str], limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Suggère des sujets d'apprentissage basés sur les lacunes identifiées.

        Args:
            keywords (List[str]): Mots-clés liés aux lacunes
            limit (int, optional): Nombre maximum de suggestions. Par défaut à 5.

        Returns:
            List[Dict[str, Any]]: Suggestions de sujets d'apprentissage
        """
        suggestions = []

        for keyword in keywords:
            # Recherche de proximité sémantique pour enrichir le sujet
            similar_concepts = self.semantic_search.search(
                query=keyword, limit=3, enrich_with_relations=True
            )

            # Construire une suggestion de sujet d'apprentissage
            related_keywords = set()
            for concept in similar_concepts:
                # Ajouter les concepts reliés s'ils existent
                if "related_concepts" in concept:
                    for related in concept.get("related_concepts", []):
                        if "concept" in related:
                            related_name = related["concept"].get("name", "")
                            if related_name:
                                related_keywords.add(related_name)

            # Créer la suggestion
            suggestion = {
                "main_topic": keyword,
                "related_topics": list(related_keywords)[:5],
                "existing_knowledge": len(similar_concepts) > 0,
                "priority": self._calculate_topic_priority(keyword, similar_concepts),
            }

            suggestions.append(suggestion)

        # Trier par priorité et limiter le nombre
        suggestions.sort(key=lambda x: x.get("priority", 0), reverse=True)

        return suggestions[:limit]

    def register_knowledge_gap(self, topic: str, description: str) -> str:
        """
        Enregistre manuellement une lacune de connaissances identifiée.

        Args:
            topic (str): Sujet de la lacune
            description (str): Description détaillée de la lacune

        Returns:
            str: Identifiant unique de la lacune enregistrée
        """
        # Créer un identifiant unique pour la lacune
        gap_id = f"gap:{topic.lower().replace(' ', '_')}"

        # Ajouter la lacune au graphe de connaissances
        gap_properties = {
            "name": topic,
            "description": description,
            "type": "knowledge_gap",
            "status": "identified",
            "timestamp": self._get_current_timestamp(),
        }

        self.kg.add_concept(gap_id, gap_properties)

        # Ajouter également à l'ensemble des lacunes connues
        self.known_gaps.add(topic.lower())

        return gap_id

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extrait les mots-clés et concepts d'un texte.

        Args:
            text (str): Texte à analyser

        Returns:
            List[str]: Liste des mots-clés extraits
        """
        # Normaliser le texte
        text = text.strip().lower()

        # Pour une implémentation complète, on utiliserait ici des techniques d'extraction
        # d'entités nommées et de phrases nominales (NER, POS tagging, etc.)
        # Pour cette version simplifiée, on extrait les mots importants par fréquence

        # Supprimer la ponctuation et les mots vides
        stopwords = {
            "le",
            "la",
            "les",
            "un",
            "une",
            "des",
            "du",
            "de",
            "a",
            "à",
            "au",
            "aux",
            "et",
            "ou",
            "qui",
            "que",
            "quoi",
            "dont",
            "où",
            "comment",
            "est",
            "sont",
            "suis",
            "es",
            "sommes",
            "êtes",
            "ont",
            "as",
            "avez",
            "pour",
            "par",
            "ce",
            "cette",
            "ces",
            "mon",
            "ton",
            "son",
            "ma",
            "ta",
            "sa",
            "mes",
            "tes",
            "ses",
            "notre",
            "votre",
            "leur",
            "nos",
            "vos",
            "leurs",
        }

        words = re.findall(r"\b\w+\b", text.lower())
        words = [w for w in words if w not in stopwords and len(w) > 2]

        # Trouver les mots les plus fréquents
        word_freq = Counter(words)

        # Extraire les bigrammes (paires de mots consécutifs)
        bigrams = []
        prev_word = None
        for word in words:
            if prev_word:
                bigrams.append(f"{prev_word} {word}")
            prev_word = word

        # Combiner mots uniques et bigrammes
        keywords = [word for word, freq in word_freq.most_common(5)]
        keywords.extend(bigrams[:3])

        # Ajouter le texte original s'il s'agit d'une question courte
        if len(text) < 100 and "?" in text:
            keywords.append(text.replace("?", "").strip())

        return list(set(keywords))

    def _analyze_coverage(
        self, keywords: List[str], search_results: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Analyse la couverture des mots-clés dans les résultats de recherche.

        Args:
            keywords (List[str]): Liste des mots-clés
            search_results (List[Dict[str, Any]]): Résultats de recherche

        Returns:
            Dict[str, float]: Score de couverture pour chaque mot-clé
        """
        coverage = {}

        for keyword in keywords:
            # Chercher les meilleurs résultats pour ce mot-clé
            best_results = []
            for result in search_results:
                # Calculer une similarité simple entre le mot-clé et le concept
                name = result.get("name", "")
                description = result.get("description", "")
                combined_text = f"{name}: {description}"

                similarity = self._calculate_text_similarity(keyword, combined_text)

                if similarity > 0.3:  # Seuil arbitraire
                    best_results.append((result, similarity))

            # Trier par similarité
            best_results.sort(key=lambda x: x[1], reverse=True)

            # Score de couverture basé sur le meilleur résultat
            if best_results:
                best_result, similarity = best_results[0]
                certainty = best_result.get("certainty", 0.5)

                # Combinaison de similarité et certitude
                coverage[keyword] = min(1.0, (similarity * 0.7) + (certainty * 0.3))
            else:
                coverage[keyword] = 0.0

        return coverage

    def _find_recurring_gaps(
        self, analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identifie les lacunes récurrentes dans une série d'analyses.

        Args:
            analyses (List[Dict[str, Any]]): Liste d'analyses de questions

        Returns:
            List[Dict[str, Any]]: Lacunes récurrentes identifiées
        """
        # Extraire les mots-clés manquants de toutes les analyses
        all_missing = []
        for analysis in analyses:
            if analysis.get("has_knowledge_gap", False):
                all_missing.extend(analysis.get("missing_concepts", []))

        # Compter la fréquence de chaque concept manquant
        missing_counter = Counter(all_missing)

        # Identifier les lacunes récurrentes (apparaissant plus d'une fois)
        recurring_gaps = []
        for concept, count in missing_counter.items():
            if count > 1:
                # Trouver les questions associées à cette lacune
                related_questions = [
                    a["question"]
                    for a in analyses
                    if concept in a.get("missing_concepts", [])
                ]

                gap = {
                    "concept": concept,
                    "frequency": count,
                    "related_questions": related_questions,
                    "confidence": 1
                    - (
                        count / len(analyses)
                    ),  # Plus c'est fréquent, moins on est confiant
                }

                recurring_gaps.append(gap)

        return recurring_gaps

    def _find_most_similar_content(self, embedding: List[float]) -> Dict[str, Any]:
        """
        Trouve le contenu le plus similaire à un embedding donné.

        Args:
            embedding (List[float]): Embedding à comparer

        Returns:
            Dict[str, Any]: Contenu le plus similaire trouvé
        """
        # Utiliser directement la recherche par vecteur de Weaviate
        # C'est une simplification, une implémentation complète utiliserait
        # des requêtes plus sophistiquées

        try:
            # Convertir l'embedding en format attendu
            vector = np.array(embedding).reshape(1, -1)

            # Effectuer une recherche par vecteur
            results = (
                self.vs.client.query.get(
                    "Concept", ["concept_id", "name", "description", "category"]
                )
                .with_near_vector({"vector": embedding, "certainty": 0.7})
                .with_limit(1)
                .do()
            )

            # Extraire le résultat
            if (
                "data" in results
                and "Get" in results["data"]
                and results["data"]["Get"]["Concept"]
            ):
                best_match = results["data"]["Get"]["Concept"][0]
                # Calculer la certitude
                certainty = 0.7  # Valeur par défaut
                if (
                    "_additional" in best_match
                    and "certainty" in best_match["_additional"]
                ):
                    certainty = best_match["_additional"]["certainty"]

                best_match["certainty"] = certainty
                return best_match
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche de contenu similaire: {e}")

        # Retourner un résultat vide en cas d'erreur
        return {"concept_id": "", "name": "", "description": "", "certainty": 0}

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calcule la similarité entre deux textes en utilisant les embeddings.

        Args:
            text1 (str): Premier texte
            text2 (str): Second texte

        Returns:
            float: Score de similarité entre 0 et 1
        """
        try:
            # Générer les embeddings
            embedding1 = self.vs.get_embedding(text1)
            embedding2 = self.vs.get_embedding(text2)

            if not embedding1 or not embedding2:
                return 0.0

            # Calculer la similarité cosinus
            vec1 = np.array(embedding1).reshape(1, -1)
            vec2 = np.array(embedding2).reshape(1, -1)

            similarity = cosine_similarity(vec1, vec2)[0][0]

            return float(max(0.0, min(1.0, similarity)))
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul de similarité: {e}")
            return 0.0

    def _calculate_topic_priority(
        self, topic: str, similar_concepts: List[Dict[str, Any]]
    ) -> float:
        """
        Calcule la priorité d'un sujet d'apprentissage.

        Args:
            topic (str): Sujet principal
            similar_concepts (List[Dict[str, Any]]): Concepts similaires trouvés

        Returns:
            float: Score de priorité (plus élevé = plus prioritaire)
        """
        # Facteurs de priorité:
        # 1. Manque de couverture (moins de concepts similaires = plus prioritaire)
        # 2. Faible confiance dans les concepts existants
        # 3. Présence dans les lacunes connues

        # Calculer le score basé sur le nombre de concepts similaires
        coverage_score = max(0, 1 - (len(similar_concepts) / 5))

        # Calculer le score de confiance moyen
        confidences = [c.get("certainty", 0.5) for c in similar_concepts]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        confidence_score = 1 - avg_confidence

        # Vérifier si le sujet est dans les lacunes connues
        known_gap_score = 1.0 if topic.lower() in self.known_gaps else 0.0

        # Combinaison pondérée des scores
        priority = (
            (coverage_score * 0.4) + (confidence_score * 0.3) + (known_gap_score * 0.3)
        )

        return priority

    def _get_current_timestamp(self) -> str:
        """Retourne le timestamp actuel au format ISO."""
        from datetime import datetime

        return datetime.now().isoformat()
