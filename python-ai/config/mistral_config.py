from typing import Dict, List
from dataclasses import dataclass


@dataclass
class MistralConfig:
    """Configuration for Mistral AI integration."""

    base_url: str = "https://api.mistral.ai/v1"
    default_model: str = "mistral-medium"

    # Default parameters for model generation
    default_temperature: float = 0.7
    default_max_tokens: int = 2000

    # Model categories and their recommended use cases
    model_categories: Dict[str, List[str]] = {
        "general": [
            "mistral-medium",
            "mistral-small",
            "mistral-large-latest",
            "mistral-embed",
        ],
        "high_performance": [
            "mistral-large-latest",
        ],
        "balanced": [
            "mistral-medium",
        ],
        "efficient": [
            "mistral-small",
            "mistral-tiny",
        ],
        "embedding": [
            "mistral-embed",
        ],
        "open_source": [
            "open-mistral-7b",
            "open-mixtral-8x7b",
        ],
    }

    # Recommended model combinations for different tasks
    task_model_mappings: Dict[str, List[str]] = {
        "code_generation": ["mistral-large-latest", "mistral-medium"],
        "general_chat": ["mistral-medium", "mistral-small"],
        "creative_writing": ["mistral-large-latest", "mistral-medium"],
        "reasoning": ["mistral-large-latest"],
        "math": ["mistral-large-latest"],
        "analysis": ["mistral-large-latest", "mistral-medium"],
        "lightweight": ["mistral-small", "mistral-tiny"],
        "embedding": ["mistral-embed"],
    }

    # System prompts for different tasks
    system_prompts: Dict[str, str] = {
        "code_generation": """You are an expert programmer and software developer. 
Provide clean, efficient, and well-documented code solutions. Consider best practices, error handling, and performance optimization.""",
        "general_chat": """You are a helpful, accurate, and friendly AI assistant.
Respond to user queries with relevant information while maintaining a natural conversational style.""",
        "creative_writing": """You are a creative writing assistant with expertise in storytelling, narrative structure, and engaging prose.
Create compelling content that resonates with readers through vivid descriptions, believable characters, and engaging plots.""",
        "reasoning": """You are a logical reasoning assistant with expertise in critical thinking and problem-solving.
Analyze problems methodically, provide clear step-by-step reasoning, and deliver well-justified conclusions.""",
        "math": """You are a mathematics expert capable of solving complex problems with precision.
Show your work step-by-step, explain your reasoning clearly, and verify your solutions.""",
        "analysis": """You are an analytical assistant specialized in data interpretation and critical analysis.
Extract meaningful insights, identify patterns, and provide thorough evaluations of complex information.""",
        "lightweight": """You are an efficient AI assistant optimized for quick, concise responses.
Provide accurate information in a direct manner while maintaining helpfulness.""",
    }

    def get_recommended_models(self, task: str) -> List[str]:
        """Get recommended models for a specific task."""
        return self.task_model_mappings.get(task, self.model_categories["general"])

    def get_system_prompt(self, task: str) -> str:
        """Get the system prompt for a specific task."""
        return self.system_prompts.get(task, self.system_prompts["general_chat"])
