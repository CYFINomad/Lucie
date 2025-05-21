import unittest
import sys
import os
from unittest.mock import Mock, patch
import logging

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from domains.multi_ai.ai_orchestrator import AIOrchestrator
from domains.multi_ai.response_evaluator import ResponseEvaluator
from domains.multi_ai.knowledge_consolidator import KnowledgeConsolidator


class TestMultiAI(unittest.TestCase):
    """Tests for the multi_ai domain."""

    def setUp(self):
        """Set up the test environment."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    @patch("domains.multi_ai.ai_adapter.ollama_adapter.OllamaAdapter")
    def test_ai_orchestrator_initialization(self, mock_ollama):
        """Test that the AIOrchestrator initializes correctly."""
        # Mock the OllamaAdapter
        mock_adapter = Mock()
        mock_ollama.return_value = mock_adapter

        # Initialize the orchestrator with only Ollama
        orchestrator = AIOrchestrator(providers=["ollama"])

        # Verify the orchestrator was initialized correctly
        self.assertIn("ollama", orchestrator.adapters)
        self.assertIn("ollama", orchestrator.configs)

        # Verify that the config has the expected methods
        self.assertTrue(hasattr(orchestrator.configs["ollama"], "get_system_prompt"))
        self.assertTrue(
            hasattr(orchestrator.configs["ollama"], "get_recommended_models")
        )

    def test_response_evaluator(self):
        """Test that the ResponseEvaluator works correctly."""
        evaluator = ResponseEvaluator()

        # Create a simple response to evaluate
        response = {
            "text": "Neural networks are computing systems inspired by the human brain. They consist of interconnected nodes or 'neurons' that process information and learn patterns from data.",
            "metadata": {},
        }

        # Evaluate the response
        evaluation = evaluator.evaluate_response(
            prompt="Explain neural networks", response=response
        )

        # Verify the evaluation contains the expected fields
        self.assertIn("overall_score", evaluation)
        self.assertIn("metrics", evaluation)
        self.assertIn("feedback", evaluation)
        self.assertIn("quality_category", evaluation)

        # Metrics should have values between 0 and 1
        self.assertGreaterEqual(evaluation["metrics"].relevance_score, 0)
        self.assertLessEqual(evaluation["metrics"].relevance_score, 1)
        self.assertGreaterEqual(evaluation["metrics"].coherence_score, 0)
        self.assertLessEqual(evaluation["metrics"].coherence_score, 1)

    def test_knowledge_consolidator(self):
        """Test that the KnowledgeConsolidator works correctly."""
        consolidator = KnowledgeConsolidator()

        # Create some sample responses to consolidate
        responses = [
            {
                "text": "Neural networks are computing systems inspired by biological neural networks.",
                "metadata": {"confidence": 0.8, "model": "model1"},
            },
            {
                "text": "Neural networks consist of connected nodes that process information and learn patterns from data.",
                "metadata": {"confidence": 0.7, "model": "model2"},
            },
        ]

        # Test different consolidation strategies
        for strategy in [
            "weight_by_confidence",
            "majority_vote",
            "highest_confidence",
            "ensemble",
        ]:
            consolidated = consolidator.consolidate_responses(
                responses, strategy=strategy
            )

            # Verify the consolidated response has the expected structure
            self.assertIn("text", consolidated)
            self.assertIn("metadata", consolidated)
            self.assertIn("consolidation_method", consolidated["metadata"])
            self.assertEqual(consolidated["metadata"]["consolidation_method"], strategy)
            self.assertEqual(consolidated["metadata"]["source_count"], 2)


if __name__ == "__main__":
    unittest.main()
