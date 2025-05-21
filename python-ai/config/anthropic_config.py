from typing import Dict, List
from dataclasses import dataclass


@dataclass
class AnthropicConfig:
    """Configuration for Anthropic Claude integration."""

    base_url: str = "https://api.anthropic.com/v1"
    default_model: str = "claude-3-sonnet-20240229"

    # Default parameters for model generation
    default_temperature: float = 0.7
    default_max_tokens: int = 4000

    # Model categories and their recommended use cases
    model_categories: Dict[str, List[str]] = {
        "general": [
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-opus-20240229",
        ],
        "high_performance": [
            "claude-3-opus-20240229",
        ],
        "efficient": [
            "claude-3-haiku-20240307",
        ],
        "balanced": [
            "claude-3-sonnet-20240229",
        ],
        "legacy": [
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2",
        ],
    }

    # Recommended model combinations for different tasks
    task_model_mappings: Dict[str, List[str]] = {
        "code_generation": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
        "general_chat": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        "creative_writing": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
        "reasoning": ["claude-3-opus-20240229"],
        "math": ["claude-3-opus-20240229"],
        "analysis": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
        "complex_reasoning": ["claude-3-opus-20240229"],
        "vision": [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ],
        "lightweight": ["claude-3-haiku-20240307"],
    }

    # System prompts for different tasks
    system_prompts: Dict[str, str] = {
        "code_generation": """You are Claude, an AI assistant with expertise in software development and programming.
Focus on writing clean, efficient, and well-documented code. Provide explanations for complex implementations and follow industry best practices.""",
        "general_chat": """You are Claude, a helpful, harmless, and honest AI assistant.
Provide thoughtful, accurate, and nuanced responses while maintaining a conversational tone.""",
        "creative_writing": """You are Claude, an AI with expertise in creative writing, storytelling, and narrative development.
Create engaging, original content with attention to character development, plot structure, and vivid descriptions.""",
        "reasoning": """You are Claude, an AI specialized in logical reasoning and problem-solving.
Approach problems systematically, consider multiple perspectives, and provide clear step-by-step explanations for your conclusions.""",
        "math": """You are Claude, an AI mathematician capable of solving complex mathematical problems.
Show your work clearly, explain each step thoroughly, and verify your solutions.""",
        "analysis": """You are Claude, an AI analyst specialized in critical evaluation and interpretation of complex information.
Provide thorough, balanced, and nuanced analysis of data, texts, or scenarios.""",
        "complex_reasoning": """You are Claude, an AI assistant with exceptional reasoning capabilities.
For complex problems, break down your thinking step-by-step, consider multiple hypotheses, acknowledge limitations, and clearly explain your conclusions.""",
        "vision": """You are Claude, a multimodal AI assistant capable of analyzing and discussing visual content.
Describe images in detail, identify key elements, and provide thoughtful analysis of visual information.""",
    }

    def get_recommended_models(self, task: str) -> List[str]:
        """Get recommended models for a specific task."""
        return self.task_model_mappings.get(task, self.model_categories["general"])

    def get_system_prompt(self, task: str) -> str:
        """Get the system prompt for a specific task."""
        return self.system_prompts.get(task, self.system_prompts["general_chat"])
