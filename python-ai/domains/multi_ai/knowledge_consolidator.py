from typing import Dict, List, Any, Optional, Union
import json
import logging


class KnowledgeConsolidator:
    """
    Service for consolidating knowledge from multiple AI model outputs.
    This class synthesizes responses from different models to produce more
    comprehensive and accurate information.
    """

    def __init__(self, min_agreement_threshold: float = 0.6):
        """
        Initialize the knowledge consolidator.

        Args:
            min_agreement_threshold (float): Minimum threshold for agreement between models
                to consider information reliable (0.0-1.0). Default is 0.6 (60%).
        """
        self.logger = logging.getLogger(__name__)
        self.min_agreement_threshold = min_agreement_threshold

    def consolidate_responses(
        self, responses: List[Dict[str, Any]], strategy: str = "weight_by_confidence"
    ) -> Dict[str, Any]:
        """
        Consolidate multiple model responses into a single coherent response.

        Args:
            responses (List[Dict[str, Any]]): List of response dictionaries from different models
            strategy (str): Consolidation strategy to use:
                - "weight_by_confidence": Weight responses by model confidence scores
                - "majority_vote": Use information that most models agree on
                - "highest_confidence": Use the response from the most confident model
                - "ensemble": Combine multiple strategies

        Returns:
            Dict[str, Any]: Consolidated response with metadata
        """
        if not responses:
            return {"text": "", "metadata": {"error": "No responses to consolidate"}}

        # If only one response, return it directly
        if len(responses) == 1:
            return {
                "text": responses[0].get("text", ""),
                "metadata": {
                    **responses[0].get("metadata", {}),
                    "consolidation_method": "single_response",
                    "source_count": 1,
                },
            }

        # Apply the selected consolidation strategy
        if strategy == "weight_by_confidence":
            result = self._consolidate_by_weighting(responses)
        elif strategy == "majority_vote":
            result = self._consolidate_by_majority_vote(responses)
        elif strategy == "highest_confidence":
            result = self._consolidate_by_highest_confidence(responses)
        elif strategy == "ensemble":
            result = self._consolidate_by_ensemble(responses)
        else:
            # Default to weighting strategy
            self.logger.warning(
                f"Unknown consolidation strategy: {strategy}. Using weight_by_confidence."
            )
            result = self._consolidate_by_weighting(responses)

        # Add metadata about the consolidation process
        result["metadata"]["source_count"] = len(responses)
        result["metadata"]["consolidation_method"] = strategy
        result["metadata"]["source_models"] = [
            r.get("metadata", {}).get("model", "unknown") for r in responses
        ]

        return result

    def _consolidate_by_weighting(
        self, responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Consolidate responses by weighting them according to confidence scores.

        Args:
            responses (List[Dict[str, Any]]): List of model responses

        Returns:
            Dict[str, Any]: Weighted consolidated response
        """
        # Extract confidence scores when available, default to 1.0
        weights = []
        for response in responses:
            confidence = response.get("metadata", {}).get("confidence", None)
            # If no confidence score, use model tier as a proxy
            if confidence is None:
                model_tier = self._get_model_tier(
                    response.get("metadata", {}).get("model", "")
                )
                confidence = model_tier / 10.0  # Scale to 0.1-1.0
            weights.append(max(0.1, confidence))  # Ensure minimum weight of 0.1

        # Normalize weights to sum to 1
        total_weight = sum(weights)
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        else:
            # Equal weights if all weights are 0
            weights = [1.0 / len(responses) for _ in responses]

        # Create a weighted template for the consolidated response
        consolidated_text = self._create_weighted_text(responses, weights)

        # Calculate average confidence
        avg_confidence = sum(
            r.get("metadata", {}).get("confidence", 0.5) for r in responses
        ) / len(responses)

        return {
            "text": consolidated_text,
            "metadata": {
                "confidence": avg_confidence,
                "weights": weights,
                "agreement_level": self._calculate_agreement_level(responses),
            },
        }

    def _consolidate_by_majority_vote(
        self, responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Consolidate responses by using information that the majority of models agree on.

        Args:
            responses (List[Dict[str, Any]]): List of model responses

        Returns:
            Dict[str, Any]: Majority-voted consolidated response
        """
        # Extract all significant statements or claims from each response
        all_statements = []
        for response in responses:
            statements = self._extract_statements(response.get("text", ""))
            all_statements.extend(statements)

        # Count occurrences of semantically similar statements
        statement_clusters = self._cluster_similar_statements(all_statements)

        # Keep only statements that appear in at least min_agreement_threshold fraction of responses
        threshold_count = max(2, int(len(responses) * self.min_agreement_threshold))
        consensus_clusters = [
            cluster for cluster in statement_clusters if len(cluster) >= threshold_count
        ]

        # Assemble the consolidated response using the consensus statements
        if consensus_clusters:
            # Take the best formulation from each cluster (typically the longest or most detailed)
            consensus_statements = [
                max(cluster, key=len) for cluster in consensus_clusters
            ]
            consolidated_text = " ".join(consensus_statements)
        else:
            # If no consensus, use the response with highest confidence
            consolidated_text = self._consolidate_by_highest_confidence(responses)[
                "text"
            ]

        return {
            "text": consolidated_text,
            "metadata": {
                "confidence": threshold_count / len(responses),
                "agreement_level": len(consensus_clusters)
                / max(1, len(statement_clusters)),
                "threshold_used": threshold_count,
            },
        }

    def _consolidate_by_highest_confidence(
        self, responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Use the response from the model with the highest confidence.

        Args:
            responses (List[Dict[str, Any]]): List of model responses

        Returns:
            Dict[str, Any]: Highest confidence response
        """
        # Sort responses by confidence score (higher is better)
        scored_responses = []
        for response in responses:
            confidence = response.get("metadata", {}).get("confidence", None)
            if confidence is None:
                # Use model tier as proxy for confidence if not available
                model_tier = self._get_model_tier(
                    response.get("metadata", {}).get("model", "")
                )
                confidence = model_tier / 10.0
            scored_responses.append((response, confidence))

        # Sort by confidence (descending)
        scored_responses.sort(key=lambda x: x[1], reverse=True)

        # Return the highest confidence response
        best_response = scored_responses[0][0]
        return {
            "text": best_response.get("text", ""),
            "metadata": {
                **best_response.get("metadata", {}),
                "selection_method": "highest_confidence",
                "selected_confidence": scored_responses[0][1],
            },
        }

    def _consolidate_by_ensemble(
        self, responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Combine multiple consolidation strategies for robust results.

        Args:
            responses (List[Dict[str, Any]]): List of model responses

        Returns:
            Dict[str, Any]: Ensemble consolidated response
        """
        # Generate consolidated responses using different strategies
        weighted_response = self._consolidate_by_weighting(responses)
        majority_response = self._consolidate_by_majority_vote(responses)
        highest_conf_response = self._consolidate_by_highest_confidence(responses)

        # Calculate agreement level between the different methods
        methods_agreement = self._calculate_text_similarity(
            [
                weighted_response["text"],
                majority_response["text"],
                highest_conf_response["text"],
            ]
        )

        # If high agreement between methods, use weighted response
        if methods_agreement > 0.8:
            result = weighted_response
            result["metadata"]["ensemble_choice"] = "weighted"
        # If medium agreement, combine weighted and majority
        elif methods_agreement > 0.5:
            # Combine the weighted and majority responses
            result = {
                "text": self._create_weighted_text(
                    [weighted_response, majority_response], [0.6, 0.4]
                ),
                "metadata": {
                    "confidence": 0.6 * weighted_response["metadata"]["confidence"]
                    + 0.4 * majority_response["metadata"]["confidence"],
                    "ensemble_choice": "weighted_majority_mix",
                },
            }
        # If low agreement, use highest confidence response
        else:
            result = highest_conf_response
            result["metadata"]["ensemble_choice"] = "highest_confidence"

        result["metadata"]["methods_agreement"] = methods_agreement
        return result

    def _extract_statements(self, text: str) -> List[str]:
        """
        Extract individual statements or claims from text.

        Args:
            text (str): Text to extract statements from

        Returns:
            List[str]: List of extracted statements
        """
        # Simple implementation - split by sentence
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]

        # Remove very short sentences (likely not meaningful statements)
        statements = [s for s in sentences if len(s) > 15]

        return statements

    def _cluster_similar_statements(self, statements: List[str]) -> List[List[str]]:
        """
        Group semantically similar statements together.

        Args:
            statements (List[str]): List of statements to cluster

        Returns:
            List[List[str]]: Clusters of similar statements
        """
        # Simple implementation - exact substring matching
        # In a real implementation, this would use semantic similarity

        clusters = []
        unclustered = list(statements)

        while unclustered:
            current = unclustered.pop(0)
            cluster = [current]

            i = 0
            while i < len(unclustered):
                # Check if statements are similar based on shared words
                words1 = set(current.lower().split())
                words2 = set(unclustered[i].lower().split())

                # Calculate word overlap
                if len(words1) > 0 and len(words2) > 0:
                    overlap = len(words1.intersection(words2)) / min(
                        len(words1), len(words2)
                    )

                    # If significant overlap, add to cluster
                    if overlap > 0.5:
                        cluster.append(unclustered.pop(i))
                    else:
                        i += 1
                else:
                    i += 1

            clusters.append(cluster)

        return clusters

    def _create_weighted_text(
        self, responses: List[Dict[str, Any]], weights: List[float]
    ) -> str:
        """
        Create a weighted text combining multiple responses.

        Args:
            responses (List[Dict[str, Any]]): List of responses
            weights (List[float]): Weight for each response

        Returns:
            str: Weighted combined text
        """
        # Sort responses by their weight (descending)
        weighted_responses = sorted(
            zip(responses, weights), key=lambda x: x[1], reverse=True
        )

        if not weighted_responses:
            return ""

        # Extract texts from responses
        texts = [r.get("text", "") for r, _ in weighted_responses]

        # If there's only one response, return it
        if len(texts) == 1:
            return texts[0]

        # For multiple responses, try to combine them more intelligently

        # 1. First, use the highest weighted response as the base
        base_text = texts[0]

        # 2. Extract statements from each response
        all_statements = {}
        for i, (text, weight) in enumerate(
            zip(texts, [w for _, w in weighted_responses])
        ):
            statements = self._extract_statements(text)
            all_statements[i] = {"statements": statements, "weight": weight}

        # 3. For each statement in lower-weight responses, check if it adds new information
        # and merge it if appropriate

        # Start by extracting statements from the base response
        base_statements = set(self._extract_statements(base_text))
        additional_statements = []

        # Check each lower-weight response for new information
        for i in range(1, len(texts)):
            resp_statements = all_statements[i]["statements"]
            resp_weight = all_statements[i]["weight"]

            for statement in resp_statements:
                # Skip very short statements
                if len(statement) < 20:
                    continue

                # Check if this statement contains new information
                # This is a simplified check - in a real implementation, would use semantic similarity
                is_new_info = True
                for base_stmt in base_statements:
                    # Calculate word overlap
                    words1 = set(statement.lower().split())
                    words2 = set(base_stmt.lower().split())

                    if words1 and words2:
                        overlap = len(words1.intersection(words2)) / min(
                            len(words1), len(words2)
                        )

                        # If high overlap, consider it redundant
                        if overlap > 0.7:
                            is_new_info = False
                            break

                if is_new_info:
                    # Weight the statement by the response weight
                    additional_statements.append((statement, resp_weight))

        # 4. Sort additional statements by weight
        additional_statements.sort(key=lambda x: x[1], reverse=True)

        # 5. Add the top additional statements to the base text
        # Limit to 3 additional statements to avoid making the response too long
        max_additions = min(3, len(additional_statements))

        if max_additions > 0:
            enriched_text = base_text

            # Add a separator if the base text doesn't end with a period
            if enriched_text and not enriched_text.endswith("."):
                enriched_text += "."

            # Add additional statements
            for i in range(max_additions):
                statement = additional_statements[i][0]

                # Add a transition phrase based on position
                if i == 0:
                    enriched_text += f" Additionally, {statement}"
                elif i == max_additions - 1:
                    enriched_text += f" Finally, {statement}"
                else:
                    enriched_text += f" Furthermore, {statement}"

            return enriched_text

        return base_text

    def _calculate_agreement_level(self, responses: List[Dict[str, Any]]) -> float:
        """
        Calculate the level of agreement between multiple responses.

        Args:
            responses (List[Dict[str, Any]]): List of model responses

        Returns:
            float: Agreement level (0.0-1.0)
        """
        # Extract text content from responses
        texts = [r.get("text", "") for r in responses]

        # Calculate text similarity
        return self._calculate_text_similarity(texts)

    def _calculate_text_similarity(self, texts: List[str]) -> float:
        """
        Calculate the similarity between multiple texts.

        Args:
            texts (List[str]): List of texts to compare

        Returns:
            float: Similarity score (0.0-1.0)
        """
        # Simple implementation based on shared word ratios
        # In a production environment, this would use embeddings for semantic similarity

        if len(texts) <= 1:
            return 1.0

        # Convert texts to sets of words
        word_sets = [set(text.lower().split()) for text in texts]

        # Calculate average Jaccard similarity between all pairs
        total_similarity = 0.0
        pair_count = 0

        for i in range(len(word_sets)):
            for j in range(i + 1, len(word_sets)):
                # Skip empty sets
                if not word_sets[i] or not word_sets[j]:
                    continue

                # Calculate Jaccard similarity
                intersection = len(word_sets[i].intersection(word_sets[j]))
                union = len(word_sets[i].union(word_sets[j]))

                if union > 0:
                    similarity = intersection / union
                    total_similarity += similarity
                    pair_count += 1

        # Return average similarity
        return total_similarity / max(1, pair_count)

    def _get_model_tier(self, model_name: str) -> int:
        """
        Get an approximation of model capability tier based on model name.

        Args:
            model_name (str): Name of the model

        Returns:
            int: Tier value (1-10, higher is better)
        """
        # Map model names to tiers (1-10 scale)
        model_tiers = {
            # OpenAI models
            "gpt-4o": 10,
            "gpt-4-turbo": 9,
            "gpt-4": 9,
            "gpt-3.5-turbo": 7,
            # Anthropic models
            "claude-3-opus": 10,
            "claude-3-sonnet": 8,
            "claude-3-haiku": 7,
            "claude-2.1": 7,
            # Mistral models
            "mistral-large": 9,
            "mistral-medium": 7,
            "mistral-small": 6,
            "mistral-tiny": 5,
            "open-mixtral-8x7b": 6,
            # Ollama models
            "llama3:70b": 8,
            "llama3:8b": 6,
            "mixtral:8x7b": 6,
            "mistral:7b": 5,
            # MathGPT models
            "mathgpt-v1-pro": 8,
            "mathgpt-v1": 7,
        }

        # Check for partial model name matches
        for key, tier in model_tiers.items():
            if key in model_name.lower():
                return tier

        # Default tier if unknown
        return 5
