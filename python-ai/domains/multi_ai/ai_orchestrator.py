from typing import Dict, List, Optional, Union
from .ai_adapter.ollama_adapter import OllamaAdapter
from ..config.ollama_config import OllamaConfig


class AIOrchestrator:
    def __init__(self):
        self.ollama_adapter = OllamaAdapter()
        self.config = OllamaConfig()

    def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of all available models across all providers."""
        return self.ollama_adapter.get_available_models()

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama."""
        return self.ollama_adapter.pull_model(model_name)

    def generate_response(
        self,
        prompt: str,
        task_type: str = "general_chat",
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Union[str, Dict]]:
        """Generate a response using the most appropriate model for the task."""
        # Get recommended models for the task
        recommended_models = self.config.get_recommended_models(task_type)

        # Use specified model if provided, otherwise use the first recommended model
        model_to_use = model_name or recommended_models[0]

        # Get system prompt for the task
        system_prompt = self.config.get_system_prompt(task_type)

        # Use default parameters if not specified
        temperature = temperature or self.config.default_temperature
        max_tokens = max_tokens or self.config.default_max_tokens

        # Generate response using Ollama
        response = self.ollama_adapter.generate_response(
            prompt=prompt,
            model_name=model_to_use,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )

        return {
            "response": response["text"],
            "metadata": {
                **response["metadata"],
                "task_type": task_type,
                "model": model_to_use,
                "provider": "ollama",
            },
        }

    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get information about a specific model."""
        return self.ollama_adapter.get_model_info(model_name)

    def delete_model(self, model_name: str) -> bool:
        """Delete a model from Ollama."""
        return self.ollama_adapter.delete_model(model_name)

    def get_recommended_models_for_task(self, task_type: str) -> List[str]:
        """Get recommended models for a specific task type."""
        return self.config.get_recommended_models(task_type)
