from typing import Dict, List
from dataclasses import dataclass


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI integration."""

    base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-3.5-turbo"

    # Default parameters for model generation
    default_temperature: float = 0.7
    default_max_tokens: int = 1000

    # Model categories and their recommended use cases
    model_categories: Dict[str, List[str]] = {
        "general": [
            "gpt-3.5-turbo",
            "gpt-4-turbo-preview",
            "gpt-4o",
        ],
        "specialized": [
            "gpt-4-vision-preview",
            "gpt-4-0125-preview",
            "gpt-4-1106-preview",
        ],
        "lightweight": ["gpt-3.5-turbo"],
        "vision": ["gpt-4-vision-preview"],
        "embedding": ["text-embedding-3-small", "text-embedding-3-large"],
    }

    # Recommended model combinations for different tasks
    task_model_mappings: Dict[str, List[str]] = {
        "code_generation": ["gpt-4-turbo-preview", "gpt-4o", "gpt-4-0125-preview"],
        "general_chat": ["gpt-3.5-turbo", "gpt-4o"],
        "creative_writing": ["gpt-4-turbo-preview", "gpt-4o"],
        "reasoning": ["gpt-4-0125-preview", "gpt-4o", "gpt-4-turbo-preview"],
        "math": ["gpt-4-0125-preview", "gpt-4o"],
        "analysis": ["gpt-4-0125-preview", "gpt-4o"],
        "vision": ["gpt-4-vision-preview"],
    }

    # System prompts for different tasks
    system_prompts: Dict[str, str] = {
        "code_generation": """You are an expert programmer and software engineer. Provide clear, efficient, and well-documented code solutions.
Focus on best practices, error handling, and code optimization. Use the most appropriate design patterns and follow language-specific conventions.""",
        "general_chat": """You are a helpful, friendly, and knowledgeable AI assistant.
Provide accurate, informative, and engaging responses while maintaining a natural conversation style.""",
        "creative_writing": """You are a creative writing assistant with expertise in storytelling, narrative structure, and engaging prose.
Help develop compelling characters, intricate plots, and vivid descriptions that captivate readers.""",
        "reasoning": """You are a logical and analytical AI assistant specializing in critical thinking and problem-solving.
Break down complex problems, provide step-by-step reasoning, and arrive at well-justified conclusions.""",
        "math": """You are a mathematics expert capable of solving complex mathematical problems.
Present solutions step-by-step with clear explanations of each stage in the calculation or proof.""",
        "analysis": """You are an analytical assistant specialized in data interpretation and critical analysis.
Extract meaningful insights, identify patterns, and provide comprehensive evaluations of complex information.""",
        "vision": """You are a multimodal assistant capable of understanding and discussing visual information.
Describe images accurately, identify relevant details, and provide context-appropriate analysis of visual content.""",
    }

    def get_recommended_models(self, task: str) -> List[str]:
        """Get recommended models for a specific task."""
        return self.task_model_mappings.get(task, self.model_categories["general"])

    def get_system_prompt(self, task: str) -> str:
        """Get the system prompt for a specific task."""
        return self.system_prompts.get(task, self.system_prompts["general_chat"])
