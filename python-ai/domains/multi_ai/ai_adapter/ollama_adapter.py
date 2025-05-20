from typing import Dict, List, Optional, Union
import requests
import json
from abc import ABC, abstractmethod


class OllamaModel:
    def __init__(self, name: str, description: str, category: str):
        self.name = name
        self.description = description
        self.category = category


class OllamaAdapter(ABC):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.available_models = self._initialize_models()

    def _initialize_models(self) -> Dict[str, OllamaModel]:
        """Initialize the available Ollama models with their metadata."""
        return {
            # General purpose models
            "llama3:8b": OllamaModel(
                "llama3:8b", "Llama 3 8B - Balanced performance/resources", "general"
            ),
            "llama3:70b": OllamaModel(
                "llama3:70b",
                "Llama 3 70B - High performance (requires high RAM)",
                "general",
            ),
            "mistral:7b": OllamaModel(
                "mistral:7b", "Mistral 7B - Efficient and performant", "general"
            ),
            "mixtral:8x7b": OllamaModel(
                "mixtral:8x7b", "Mixtral 8x7B - High performance MoE model", "general"
            ),
            "gemma:7b": OllamaModel("gemma:7b", "Google's Gemma 7B model", "general"),
            # Specialized models
            "codellama:13b": OllamaModel(
                "codellama:13b", "Excellent for programming tasks", "specialized"
            ),
            "codegemma:7b": OllamaModel(
                "codegemma:7b", "Google's code-specialized model", "specialized"
            ),
            "wizardcoder:13b": OllamaModel(
                "wizardcoder:13b", "Specialized in code generation", "specialized"
            ),
            "vicuna:13b": OllamaModel(
                "vicuna:13b", "Good for dialogue and instructions", "specialized"
            ),
            "orca-mini:13b": OllamaModel(
                "orca-mini:13b",
                "Lightweight but capable for general tasks",
                "specialized",
            ),
            "wizard:13b": OllamaModel(
                "wizard:13b", "Good for detailed and reasoned responses", "specialized"
            ),
            # Lightweight models
            "tinyllama:1.1b": OllamaModel(
                "tinyllama:1.1b",
                "Very small model, fast but limited capabilities",
                "lightweight",
            ),
            "phi3:mini": OllamaModel(
                "phi3:mini",
                "Microsoft's Phi-3 Mini - Excellent size/performance ratio",
                "lightweight",
            ),
            "qwen:0.5b": OllamaModel(
                "qwen:0.5b",
                "Small Qwen model, very efficient for its size",
                "lightweight",
            ),
            # Multilingual models
            "nous-hermes:7b": OllamaModel(
                "nous-hermes:7b", "Good multilingual support", "multilingual"
            ),
            "aya:8b": OllamaModel(
                "aya:8b", "Performant multilingual model", "multilingual"
            ),
            "dolphin-mixtral:8x7b": OllamaModel(
                "dolphin-mixtral:8x7b",
                "Mixtral variant optimized for multitasking",
                "multilingual",
            ),
        }

    def get_available_models(self) -> List[Dict[str, str]]:
        """Get list of available models with their metadata."""
        return [
            {
                "name": model.name,
                "description": model.description,
                "category": model.category,
            }
            for model in self.available_models.values()
        ]

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama."""
        try:
            response = requests.post(
                f"{self.base_url}/api/pull", json={"name": model_name}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error pulling model {model_name}: {str(e)}")
            return False

    def generate_response(
        self,
        prompt: str,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Union[str, Dict]]:
        """Generate a response using the specified model."""
        try:
            payload = {
                "model": model_name,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False,
            }

            if max_tokens:
                payload["max_tokens"] = max_tokens

            if system_prompt:
                payload["system"] = system_prompt

            response = requests.post(f"{self.base_url}/api/generate", json=payload)

            if response.status_code == 200:
                result = response.json()
                return {
                    "text": result.get("response", ""),
                    "metadata": {
                        "model": model_name,
                        "tokens": result.get("total_tokens", 0),
                        "prompt_tokens": result.get("prompt_eval_count", 0),
                        "completion_tokens": result.get("eval_count", 0),
                    },
                }
            else:
                return {
                    "text": f"Error: {response.status_code} - {response.text}",
                    "metadata": {"error": True},
                }

        except Exception as e:
            return {
                "text": f"Error generating response: {str(e)}",
                "metadata": {"error": True},
            }

    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get information about a specific model."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                for model in models:
                    if model.get("name") == model_name:
                        return model
            return None
        except Exception as e:
            print(f"Error getting model info: {str(e)}")
            return None

    def delete_model(self, model_name: str) -> bool:
        """Delete a model from Ollama."""
        try:
            response = requests.delete(
                f"{self.base_url}/api/delete", json={"name": model_name}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error deleting model {model_name}: {str(e)}")
            return False
