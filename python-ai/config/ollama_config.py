from typing import Dict, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OllamaConfig:
    """Configuration for Ollama integration."""

    base_url: str = "http://localhost:11434"
    default_model: str = "mistral:7b"  # Default model to use
    model_cache_dir: Path = Path.home() / ".ollama" / "models"

    # Default parameters for model generation
    default_temperature: float = 0.7
    default_max_tokens: int = 2048

    # Model categories and their recommended use cases
    model_categories: Dict[str, List[str]] = {
        "general": [
            "llama3:8b",
            "llama3:70b",
            "mistral:7b",
            "mixtral:8x7b",
            "gemma:7b",
        ],
        "specialized": [
            "codellama:13b",
            "codegemma:7b",
            "wizardcoder:13b",
            "vicuna:13b",
            "orca-mini:13b",
            "wizard:13b",
        ],
        "lightweight": ["tinyllama:1.1b", "phi3:mini", "qwen:0.5b"],
        "multilingual": ["nous-hermes:7b", "aya:8b", "dolphin-mixtral:8x7b"],
    }

    # Recommended model combinations for different tasks
    task_model_mappings: Dict[str, List[str]] = {
        "code_generation": ["codellama:13b", "codegemma:7b", "wizardcoder:13b"],
        "general_chat": ["mistral:7b", "llama3:8b", "gemma:7b"],
        "multilingual": ["nous-hermes:7b", "aya:8b", "dolphin-mixtral:8x7b"],
        "reasoning": ["mixtral:8x7b", "llama3:70b", "wizard:13b"],
        "lightweight": ["phi3:mini", "tinyllama:1.1b", "qwen:0.5b"],
    }

    # System prompts for different tasks
    system_prompts: Dict[str, str] = {
        "code_generation": """You are an expert programmer. Provide clear, efficient, and well-documented code solutions.
Focus on best practices, error handling, and code optimization.""",
        "general_chat": """You are a helpful, friendly, and knowledgeable AI assistant.
Provide accurate, informative, and engaging responses while maintaining a natural conversation style.""",
        "multilingual": """You are a multilingual AI assistant capable of understanding and responding in multiple languages.
Maintain cultural sensitivity and provide accurate translations when needed.""",
        "reasoning": """You are a logical and analytical AI assistant.
Break down complex problems, provide step-by-step reasoning, and arrive at well-justified conclusions.""",
        "lightweight": """You are an efficient AI assistant optimized for quick responses.
Provide concise and accurate information while maintaining good performance on resource-constrained systems.""",
    }

    @classmethod
    def get_recommended_models(cls, task: str) -> List[str]:
        """Get recommended models for a specific task."""
        return cls.task_model_mappings.get(task, cls.model_categories["general"])

    @classmethod
    def get_system_prompt(cls, task: str) -> str:
        """Get the system prompt for a specific task."""
        return cls.system_prompts.get(task, cls.system_prompts["general_chat"])
