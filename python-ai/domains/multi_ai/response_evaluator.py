from typing import Dict, List, Any, Optional, Union, Tuple
import json
import re
import logging
from dataclasses import dataclass


@dataclass
class EvaluationMetrics:
    """Data class to hold evaluation metrics for an AI response."""

    relevance_score: float  # How relevant the response is to the query (0.0-1.0)
    coherence_score: float  # How coherent/logical the response is (0.0-1.0)
    completeness_score: float  # How complete the response is (0.0-1.0)
    factuality_score: float  # Estimated factual accuracy (0.0-1.0)
    hallucination_risk: float  # Risk of hallucinated content (0.0-1.0)
    creativity_score: Optional[float] = None  # For creative tasks (0.0-1.0)
    instruction_following: Optional[float] = (
        None  # How well instructions were followed (0.0-1.0)
    )

    @property
    def overall_score(self) -> float:
        """Calculate weighted overall score from individual metrics."""
        # Calculate basic score with required fields
        scores = [
            self.relevance_score * 0.3,
            self.coherence_score * 0.25,
            self.completeness_score * 0.2,
            self.factuality_score * 0.25,
        ]

        divisor = 1.0

        # Add optional scores if they exist
        if self.creativity_score is not None:
            scores.append(self.creativity_score * 0.15)
            divisor += 0.15

        if self.instruction_following is not None:
            scores.append(self.instruction_following * 0.2)
            divisor += 0.2

        # Calculate weighted average
        return sum(scores) / divisor


class ResponseEvaluator:
    """
    Class for evaluating the quality of AI model responses based on various metrics.
    This evaluator can be used to:
    1. Score individual responses
    2. Compare responses from different models
    3. Identify potential issues in responses like hallucinations
    4. Provide improvement suggestions
    """

    def __init__(
        self,
        hallucination_patterns: Optional[List[str]] = None,
        truthfulness_indicators: Optional[List[str]] = None,
        quality_thresholds: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize the response evaluator.

        Args:
            hallucination_patterns (List[str], optional): Regex patterns that may indicate hallucinations
            truthfulness_indicators (List[str], optional): Patterns indicating reliable information
            quality_thresholds (Dict[str, float], optional): Thresholds for different quality levels
        """
        self.logger = logging.getLogger(__name__)

        # Default patterns for hallucination detection
        self.hallucination_patterns = hallucination_patterns or [
            r"I think|I believe|probably|might be|could be|may be|possibly",
            r"I'm not sure|I'm not certain|I'm not familiar",
            r"I don't have (specific|exact|detailed|current) information",
            r"As of my last (update|training)",
            r"without further (information|context|details)",
        ]

        # Default indicators of truthfulness
        self.truthfulness_indicators = truthfulness_indicators or [
            r"according to|based on|as stated in|as reported by",
            r"research (shows|indicates|suggests|demonstrates)",
            r"studies have (shown|found|demonstrated)",
            r"data (from|indicates|shows)",
            r"source:|reference:",
        ]

        # Default quality thresholds
        self.quality_thresholds = quality_thresholds or {
            "excellent": 0.85,
            "good": 0.7,
            "acceptable": 0.6,
            "poor": 0.4,
        }

    def evaluate_response(
        self,
        prompt: str,
        response: Dict[str, Any],
        reference_texts: Optional[List[str]] = None,
        is_creative_task: bool = False,
        instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate a single response based on prompt and expected answers.

        Args:
            prompt (str): The original prompt/question
            response (Dict[str, Any]): The model response to evaluate
            reference_texts (List[str], optional): Reference texts for factuality comparison
            is_creative_task (bool): Whether the task requires creativity
            instructions (str, optional): Specific instructions given to the model

        Returns:
            Dict[str, Any]: Evaluation results with metrics and feedback
        """
        try:
            # Validate input
            if not prompt:
                self.logger.warning("Empty prompt provided for evaluation")
                prompt = ""

            response_text = response.get("text", "")
            if not response_text:
                self.logger.warning("Empty response text provided for evaluation")
                return {
                    "metrics": EvaluationMetrics(
                        relevance_score=0.0,
                        coherence_score=0.0,
                        completeness_score=0.0,
                        factuality_score=0.0,
                        hallucination_risk=1.0,
                    ),
                    "feedback": "Empty response",
                    "quality_category": "poor",
                    "error": "empty_response",
                }

            # Calculate individual metrics
            try:
                relevance_score = self._calculate_relevance(prompt, response_text)
            except Exception as e:
                self.logger.error(f"Error calculating relevance: {str(e)}")
                relevance_score = 0.5

            try:
                coherence_score = self._calculate_coherence(response_text)
            except Exception as e:
                self.logger.error(f"Error calculating coherence: {str(e)}")
                coherence_score = 0.5

            try:
                completeness_score = self._calculate_completeness(prompt, response_text)
            except Exception as e:
                self.logger.error(f"Error calculating completeness: {str(e)}")
                completeness_score = 0.5

            # Calculate factuality and hallucination risk
            try:
                factuality_score, hallucination_risk = self._evaluate_factuality(
                    response_text, reference_texts
                )
            except Exception as e:
                self.logger.error(f"Error evaluating factuality: {str(e)}")
                factuality_score, hallucination_risk = 0.5, 0.5

            # Optional metrics
            creativity_score = None
            if is_creative_task:
                try:
                    creativity_score = self._calculate_creativity(response_text)
                except Exception as e:
                    self.logger.error(f"Error calculating creativity: {str(e)}")
                    # Leave as None

            instruction_following = None
            if instructions:
                try:
                    instruction_following = self._evaluate_instruction_following(
                        instructions, response_text
                    )
                except Exception as e:
                    self.logger.error(
                        f"Error evaluating instruction following: {str(e)}"
                    )
                    # Leave as None

            # Create metrics object
            metrics = EvaluationMetrics(
                relevance_score=relevance_score,
                coherence_score=coherence_score,
                completeness_score=completeness_score,
                factuality_score=factuality_score,
                hallucination_risk=hallucination_risk,
                creativity_score=creativity_score,
                instruction_following=instruction_following,
            )

            # Determine quality category
            quality_category = self._get_quality_category(metrics.overall_score)

            # Generate feedback and improvement suggestions
            try:
                feedback, suggestions = self._generate_feedback(metrics, response_text)
            except Exception as e:
                self.logger.error(f"Error generating feedback: {str(e)}")
                feedback = "Unable to generate specific feedback."
                suggestions = ["Consider improving the response."]

            return {
                "metrics": metrics,
                "overall_score": metrics.overall_score,
                "feedback": feedback,
                "suggestions": suggestions,
                "quality_category": quality_category,
                "response_length": len(response_text.split()),
            }

        except Exception as e:
            self.logger.error(f"Unexpected error during response evaluation: {str(e)}")
            # Return a baseline evaluation in case of error
            return {
                "metrics": EvaluationMetrics(
                    relevance_score=0.5,
                    coherence_score=0.5,
                    completeness_score=0.5,
                    factuality_score=0.5,
                    hallucination_risk=0.5,
                ),
                "overall_score": 0.5,
                "feedback": "Unable to properly evaluate the response due to an error.",
                "suggestions": ["The evaluation system encountered an error."],
                "quality_category": "unknown",
                "error": str(e),
            }

    def cross_validate_responses(
        self,
        prompt: str,
        responses: List[Dict[str, Any]],
        validation_method: str = "comparison",
    ) -> Dict[str, Any]:
        """
        Cross-validate multiple responses against each other to detect consensus and outliers.

        Args:
            prompt (str): The original prompt/question
            responses (List[Dict[str, Any]]): List of responses to cross-validate
            validation_method (str): Method to use for validation:
                - "comparison": Compare responses directly
                - "factual_check": Use responses to validate each other's factual claims

        Returns:
            Dict[str, Any]: Cross-validation results, consensus score, and outliers
        """
        if not responses or len(responses) < 2:
            return {"error": "Need at least two responses to cross-validate"}

        # Extract text content
        response_texts = [r.get("text", "") for r in responses]

        # Calculate pairwise agreement between responses
        agreement_matrix = []
        for i in range(len(responses)):
            row = []
            for j in range(len(responses)):
                if i == j:
                    row.append(1.0)  # Perfect agreement with self
                else:
                    # Calculate similarity between responses
                    similarity = self._calculate_text_similarity(
                        [response_texts[i], response_texts[j]]
                    )
                    row.append(similarity)
            agreement_matrix.append(row)

        # Calculate average agreement for each response
        avg_agreements = []
        for i in range(len(responses)):
            # Exclude self-agreement
            agreements = [
                agreement_matrix[i][j] for j in range(len(responses)) if i != j
            ]
            avg_agreement = sum(agreements) / len(agreements) if agreements else 0.0
            avg_agreements.append(avg_agreement)

        # Identify consensus and outliers
        consensus_threshold = 0.6
        outlier_threshold = 0.4

        consensus_indices = [
            i for i, score in enumerate(avg_agreements) if score >= consensus_threshold
        ]
        outlier_indices = [
            i for i, score in enumerate(avg_agreements) if score < outlier_threshold
        ]

        # Calculate overall consensus score
        overall_consensus = (
            sum(avg_agreements) / len(avg_agreements) if avg_agreements else 0.0
        )

        # If using factual check method, extract and compare factual claims
        factual_validation = None
        if validation_method == "factual_check" and len(responses) >= 3:
            # Extract factual claims from each response
            all_claims = []
            for text in response_texts:
                # Simple extraction of statements that look like factual claims
                # In a real implementation, use a more sophisticated approach
                statements = text.split(". ")
                claims = [
                    s
                    for s in statements
                    if len(s) > 20
                    and not any(
                        h in s.lower()
                        for h in [
                            "i think",
                            "i believe",
                            "might",
                            "may",
                            "could",
                            "possibly",
                        ]
                    )
                ]
                all_claims.append(claims)

            # Check each claim against other responses
            validated_claims = []
            for i, claims in enumerate(all_claims):
                # For each claim in this response
                for claim in claims:
                    # Count how many other responses support this claim
                    support_count = 0
                    for j, other_text in enumerate(response_texts):
                        if i != j:
                            # Simple string matching - in a real implementation, use semantic similarity
                            if (
                                claim.lower() in other_text.lower()
                                or self._calculate_text_similarity([claim, other_text])
                                > 0.7
                            ):
                                support_count += 1

                    # Consider a claim validated if supported by at least half of other responses
                    if support_count >= (len(responses) - 1) / 2:
                        validated_claims.append(claim)

            factual_validation = {
                "validated_claims_count": len(validated_claims),
                "validated_claims": validated_claims[
                    :5
                ],  # Limit to first 5 for brevity
                "validation_ratio": len(validated_claims)
                / max(1, sum(len(claims) for claims in all_claims)),
            }

        return {
            "overall_consensus": overall_consensus,
            "agreement_matrix": agreement_matrix,
            "average_agreements": avg_agreements,
            "consensus_response_indices": consensus_indices,
            "outlier_response_indices": outlier_indices,
            "factual_validation": factual_validation,
            "validation_method": validation_method,
        }

    def compare_responses(
        self,
        prompt: str,
        responses: List[Dict[str, Any]],
        reference_texts: Optional[List[str]] = None,
        is_creative_task: bool = False,
        instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compare multiple responses to the same prompt.

        Args:
            prompt (str): The original prompt/question
            responses (List[Dict[str, Any]]): List of model responses to compare
            reference_texts (List[str], optional): Reference texts for factuality
            is_creative_task (bool): Whether the task requires creativity
            instructions (str, optional): Specific instructions given to models

        Returns:
            Dict[str, Any]: Comparison results with ranking and individual evaluations
        """
        if not responses:
            return {"error": "No responses to compare"}

        try:
            # Evaluate each response
            evaluations = []
            for resp in responses:
                eval_result = self.evaluate_response(
                    prompt, resp, reference_texts, is_creative_task, instructions
                )
                evaluations.append(
                    {
                        "response": resp,
                        "evaluation": eval_result,
                        "model": resp.get("metadata", {}).get("model", "unknown"),
                        "provider": resp.get("metadata", {}).get("provider", "unknown"),
                    }
                )

            # Sort by overall score (descending)
            ranked_evaluations = sorted(
                evaluations,
                key=lambda x: x["evaluation"]["overall_score"],
                reverse=True,
            )

            # Calculate agreement between top responses
            agreement_score = 0.0
            if len(ranked_evaluations) > 1:
                top_responses = [
                    r["response"].get("text", "")
                    for r in ranked_evaluations[: min(3, len(ranked_evaluations))]
                ]
                agreement_score = self._calculate_response_agreement(top_responses)

            # Also run cross-validation to get more detailed consensus metrics
            cross_validation = None
            if len(responses) >= 2:
                try:
                    cross_validation = self.cross_validate_responses(
                        prompt=prompt, responses=responses
                    )
                except Exception as e:
                    self.logger.error(f"Error during cross-validation: {str(e)}")

            return {
                "ranked_evaluations": ranked_evaluations,
                "best_response_index": 0,
                "best_model": ranked_evaluations[0]["model"],
                "best_score": ranked_evaluations[0]["evaluation"]["overall_score"],
                "score_range": {
                    "min": min(e["evaluation"]["overall_score"] for e in evaluations),
                    "max": max(e["evaluation"]["overall_score"] for e in evaluations),
                    "avg": sum(e["evaluation"]["overall_score"] for e in evaluations)
                    / len(evaluations),
                },
                "agreement_score": agreement_score,
                "cross_validation": cross_validation,
            }

        except Exception as e:
            self.logger.error(f"Error comparing responses: {str(e)}")
            return {
                "error": f"Failed to compare responses: {str(e)}",
                "response_count": len(responses),
            }

    def _calculate_relevance(self, prompt: str, response: str) -> float:
        """Calculate how relevant the response is to the prompt."""
        # Simple implementation based on keyword matching
        # In a real implementation, this could use semantic similarity
        prompt_keywords = set(re.findall(r"\b\w{3,}\b", prompt.lower()))
        response_keywords = set(re.findall(r"\b\w{3,}\b", response.lower()))

        if not prompt_keywords:
            return 0.8  # Default if no keywords found

        # Calculate overlap ratio
        overlap = prompt_keywords.intersection(response_keywords)
        relevance = len(overlap) / len(prompt_keywords)

        # Adjust score - pure keyword matching is limited
        # Real implementation would use embeddings comparison
        return min(max(relevance * 1.2, 0.0), 1.0)

    def _calculate_coherence(self, text: str) -> float:
        """Evaluate the logical flow and coherence of the response."""
        # Check for structural elements that indicate good organization
        has_paragraphs = len(text.split("\n\n")) > 1

        # Check for transition words that indicate logical flow
        transition_words = [
            "therefore",
            "however",
            "furthermore",
            "additionally",
            "consequently",
            "thus",
            "moreover",
            "in addition",
        ]
        transition_count = sum(1 for word in transition_words if word in text.lower())

        # Check average sentence length (extremely long or short sentences reduce coherence)
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        avg_sentence_length = sum(len(s.split()) for s in sentences) / max(
            1, len(sentences)
        )

        # Penalize for very short or very long average sentence length
        sentence_length_score = 1.0
        if avg_sentence_length < 5:
            sentence_length_score = 0.7
        elif avg_sentence_length > 30:
            sentence_length_score = 0.8

        # Calculate base coherence score
        base_score = 0.6  # Default baseline
        base_score += 0.1 if has_paragraphs else 0
        base_score += min(0.2, transition_count * 0.04)  # Max 0.2 for transitions

        # Combine scores
        coherence_score = base_score * sentence_length_score

        return min(max(coherence_score, 0.0), 1.0)

    def _calculate_completeness(self, prompt: str, response: str) -> float:
        """Evaluate whether the response fully addresses the prompt."""
        # Extract question words from the prompt
        question_words = ["what", "why", "how", "when", "where", "who", "which"]
        questions = [
            q
            for q in re.findall(
                r"\b(" + "|".join(question_words) + r")\b\s[^.?!]*\?", prompt.lower()
            )
        ]

        completeness_score = 0.7  # Default baseline

        # If we have identifiable questions, check if they appear to be addressed
        if questions:
            completeness_score = 0.5  # Lower baseline when we have specific questions

            # Adjust score based on response length relative to prompt
            prompt_word_count = len(prompt.split())
            response_word_count = len(response.split())

            # Longer responses tend to be more complete, but with diminishing returns
            length_ratio = min(response_word_count / max(1, prompt_word_count), 5) / 5
            completeness_score += length_ratio * 0.3

            # Check if response has multiple paragraphs (suggesting in-depth treatment)
            if len(response.split("\n\n")) > 1:
                completeness_score += 0.1

        return min(max(completeness_score, 0.0), 1.0)

    def _evaluate_factuality(
        self, text: str, reference_texts: Optional[List[str]] = None
    ) -> Tuple[float, float]:
        """
        Evaluate factual accuracy and hallucination risk.

        Returns:
            Tuple[float, float]: (factuality_score, hallucination_risk)
        """
        # Count hallucination indicators
        hallucination_count = 0
        for pattern in self.hallucination_patterns:
            hallucination_count += len(re.findall(pattern, text, re.IGNORECASE))

        # Count truthfulness indicators
        truthfulness_count = 0
        for pattern in self.truthfulness_indicators:
            truthfulness_count += len(re.findall(pattern, text, re.IGNORECASE))

        # Calculate base hallucination risk
        word_count = len(text.split())
        if word_count == 0:
            return 0.0, 1.0

        # Normalized hallucination density
        hallucination_density = min(hallucination_count / (word_count / 100), 5) / 5

        # Normalized truthfulness density
        truthfulness_density = min(truthfulness_count / (word_count / 100), 5) / 5

        # Calculate hallucination risk (0-1)
        hallucination_risk = max(
            0, min(hallucination_density - truthfulness_density * 0.5, 1.0)
        )

        # If we have reference texts, compare response to them
        factuality_score = 0.5  # Default baseline
        if reference_texts and reference_texts[0]:
            # In a real implementation, this could use semantic similarity or entailment
            # Here we use a simple keyword matching approach
            reference_keywords = set()
            for ref_text in reference_texts:
                reference_keywords.update(
                    set(re.findall(r"\b\w{3,}\b", ref_text.lower()))
                )

            response_keywords = set(re.findall(r"\b\w{3,}\b", text.lower()))

            if reference_keywords:
                # Calculate overlap
                overlap = reference_keywords.intersection(response_keywords)
                factuality_score = min(
                    len(overlap) / len(reference_keywords) * 1.5, 1.0
                )
        else:
            # Without references, estimate based on hallucination indicators
            factuality_score = max(0.3, 1.0 - hallucination_risk * 0.7)

            # Adjust based on truthfulness indicators
            factuality_score = min(factuality_score + truthfulness_density * 0.3, 1.0)

        return factuality_score, hallucination_risk

    def _calculate_creativity(self, text: str) -> float:
        """Evaluate the creativity of a response."""
        # Simple implementation - could be made more sophisticated
        word_count = len(text.split())

        # Longer responses tend to be more creative
        length_score = min(word_count / 200, 1.0) * 0.3

        # Check for variety in sentence structure
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Calculate average and variance in sentence length
        if sentences:
            sent_lengths = [len(s.split()) for s in sentences]
            avg_length = sum(sent_lengths) / len(sent_lengths)
            variance = sum((l - avg_length) ** 2 for l in sent_lengths) / len(
                sent_lengths
            )

            # Higher variance means more diverse sentence structure
            structure_score = min(variance / 100, 0.5)
        else:
            structure_score = 0.0

        # Base creativity score
        creativity_score = 0.5 + length_score + structure_score

        return min(max(creativity_score, 0.0), 1.0)

    def _evaluate_instruction_following(
        self, instructions: str, response: str
    ) -> float:
        """Evaluate how well the model followed given instructions."""
        # Extract key instruction components
        instruction_keywords = re.findall(r"\b\w{3,}\b", instructions.lower())
        instruction_keyword_set = set(instruction_keywords)

        # Simple implementation based on keyword matching
        response_keywords = set(re.findall(r"\b\w{3,}\b", response.lower()))

        if not instruction_keyword_set:
            return 0.7  # Default if no keywords found

        # Calculate overlap
        overlap = instruction_keyword_set.intersection(response_keywords)
        following_score = len(overlap) / len(instruction_keyword_set)

        # Adjust baseline score
        return min(max(0.5 + following_score * 0.5, 0.0), 1.0)

    def _calculate_response_agreement(self, responses: List[str]) -> float:
        """Calculate how much agreement exists between multiple responses."""
        if len(responses) <= 1:
            return 1.0

        # Extract key statements from each response
        all_keywords = []
        for response in responses:
            # Extract keywords (simple implementation)
            keywords = set(re.findall(r"\b\w{3,}\b", response.lower()))
            all_keywords.append(keywords)

        # Calculate pairwise agreement
        agreement_scores = []
        for i in range(len(all_keywords)):
            for j in range(i + 1, len(all_keywords)):
                if not all_keywords[i] or not all_keywords[j]:
                    continue

                # Jaccard similarity
                intersection = len(all_keywords[i].intersection(all_keywords[j]))
                union = len(all_keywords[i].union(all_keywords[j]))

                if union > 0:
                    agreement_scores.append(intersection / union)

        # Average agreement
        if agreement_scores:
            return sum(agreement_scores) / len(agreement_scores)
        return 0.5  # Default

    def _get_quality_category(self, score: float) -> str:
        """Map the overall score to a quality category."""
        if score >= self.quality_thresholds.get("excellent", 0.85):
            return "excellent"
        elif score >= self.quality_thresholds.get("good", 0.7):
            return "good"
        elif score >= self.quality_thresholds.get("acceptable", 0.6):
            return "acceptable"
        elif score >= self.quality_thresholds.get("poor", 0.4):
            return "poor"
        else:
            return "very_poor"

    def _generate_feedback(
        self, metrics: EvaluationMetrics, text: str
    ) -> Tuple[str, List[str]]:
        """Generate feedback and improvement suggestions based on metrics."""
        feedback_points = []
        suggestions = []

        # Relevance feedback
        if metrics.relevance_score < 0.6:
            feedback_points.append(
                "The response is not sufficiently relevant to the original query."
            )
            suggestions.append(
                "Ensure the response directly addresses the main points in the query."
            )

        # Coherence feedback
        if metrics.coherence_score < 0.6:
            feedback_points.append("The response lacks logical flow and structure.")
            suggestions.append(
                "Improve organization with clear paragraphs and transition phrases."
            )

        # Completeness feedback
        if metrics.completeness_score < 0.6:
            feedback_points.append(
                "The response does not fully address all aspects of the query."
            )
            suggestions.append(
                "Expand the response to cover all parts of the question thoroughly."
            )

        # Factuality and hallucination feedback
        if metrics.hallucination_risk > 0.6:
            feedback_points.append(
                "The response contains statements that may not be factually grounded."
            )
            suggestions.append(
                "Include more specific references or sources to support claims."
            )

        # Creativity feedback (if applicable)
        if metrics.creativity_score is not None and metrics.creativity_score < 0.5:
            feedback_points.append("The response lacks originality and creativity.")
            suggestions.append(
                "Consider more diverse and unique approaches to the problem."
            )

        # Instruction following feedback (if applicable)
        if (
            metrics.instruction_following is not None
            and metrics.instruction_following < 0.6
        ):
            feedback_points.append(
                "The response does not fully follow the given instructions."
            )
            suggestions.append(
                "Carefully address each specific instruction or requirement."
            )

        # Default feedback if all metrics are good
        if not feedback_points:
            feedback = (
                "The response is well-constructed and effectively addresses the query."
            )
            if metrics.overall_score > 0.85:
                feedback += " No significant improvements needed."
            else:
                suggestions.append(
                    "Consider adding more specific details or examples for completeness."
                )
        else:
            feedback = " ".join(feedback_points)

        return feedback, suggestions
