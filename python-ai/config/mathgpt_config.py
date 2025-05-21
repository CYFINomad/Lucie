from typing import Dict, List
from dataclasses import dataclass


@dataclass
class MathGPTConfig:
    """Configuration for MathGPT integration."""

    base_url: str = "https://api.mathgpt.example.com/v1"  # Placeholder URL
    default_model: str = "mathgpt-default"

    # Default parameters for model generation
    default_temperature: float = (
        0.3  # Lower temperature for more precise math responses
    )
    default_max_tokens: int = 2500

    # Model categories and their recommended use cases
    model_categories: Dict[str, List[str]] = {
        "general": [
            "mathgpt-default",
            "mathgpt-advanced",
            "mathgpt-expert",
        ],
        "high_performance": [
            "mathgpt-expert",
        ],
        "balanced": [
            "mathgpt-advanced",
        ],
        "basic": [
            "mathgpt-default",
        ],
        "specialized": [
            "mathgpt-algebra",
            "mathgpt-calculus",
            "mathgpt-statistics",
        ],
    }

    # Recommended model combinations for different tasks
    task_model_mappings: Dict[str, List[str]] = {
        "math": ["mathgpt-expert", "mathgpt-advanced"],
        "algebra": ["mathgpt-algebra", "mathgpt-expert"],
        "calculus": ["mathgpt-calculus", "mathgpt-expert"],
        "statistics": ["mathgpt-statistics", "mathgpt-expert"],
        "arithmetic": ["mathgpt-default"],
        "general_math": ["mathgpt-default", "mathgpt-advanced"],
        "advanced_math": ["mathgpt-expert"],
    }

    # System prompts for different math tasks
    system_prompts: Dict[str, str] = {
        "math": """You are MathGPT, an expert mathematical assistant.
Solve mathematical problems step-by-step, showing all work clearly. Use mathematical notation where appropriate, verify solutions, and explain concepts as needed.""",
        "algebra": """You are MathGPT, specialized in algebraic problem-solving.
Solve algebraic equations, manipulate expressions, and explain abstract algebraic concepts with clarity. Show step-by-step work for all solutions.""",
        "calculus": """You are MathGPT, specialized in calculus.
Tackle differentiation, integration, limits, and other calculus concepts with precision. Show the intermediate steps in your solutions and explain the underlying principles.""",
        "statistics": """You are MathGPT, specialized in statistical analysis.
Analyze data, perform statistical tests, explain probability concepts, and interpret results clearly. Present statistical reasoning in an understandable manner.""",
        "arithmetic": """You are MathGPT, focused on providing clear arithmetic solutions.
Perform calculations step-by-step, explaining the process for each operation and ensuring accurate results.""",
        "general_math": """You are MathGPT, a versatile mathematical assistant.
Address a wide range of mathematical topics with accuracy and clarity. Show your work for each problem and explain key concepts.""",
        "advanced_math": """You are MathGPT, specializing in advanced mathematics.
Tackle complex topics like linear algebra, differential equations, number theory, and abstract mathematics. Provide rigorous solutions with detailed explanations.""",
    }

    def get_recommended_models(self, task: str) -> List[str]:
        """Get recommended models for a specific math task."""
        # Default to general math if the specific task isn't found
        if task == "math":
            return self.task_model_mappings["math"]
        return self.task_model_mappings.get(
            task, self.task_model_mappings["general_math"]
        )

    def get_system_prompt(self, task: str) -> str:
        """Get the system prompt for a specific math task."""
        # Default to general math prompt if the specific task isn't found
        if task == "math":
            return self.system_prompts["math"]
        return self.system_prompts.get(task, self.system_prompts["general_math"])
