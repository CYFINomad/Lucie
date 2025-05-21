from typing import Dict, List, Optional, Union
import requests
import json
from abc import ABC, abstractmethod


class MistralModel:
    def __init__(self, name: str, description: str, category: str):
        self.name = name
        self.description = description
        self.category = category


class MistralAdapter:
    def __init__(self, api_key: str, base_url: str = "https://api.mistral.ai/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.available_models = self._initialize_models()

    def _initialize_models(self) -> Dict[str, MistralModel]:
        """Initialize the available Mistral AI models with their metadata."""
        return {
            "mistral-tiny": MistralModel(
                "mistral-tiny",
                "Fast and cost-effective model for simple tasks",
                "lightweight",
            ),
            "mistral-small": MistralModel(
                "mistral-small", "Balanced model for general purpose use", "general"
            ),
            "mistral-medium": MistralModel(
                "mistral-medium",
                "High-performance model for complex reasoning",
                "general",
            ),
            "mistral-large": MistralModel(
                "mistral-large",
                "Most powerful Mistral model for advanced tasks",
                "advanced",
            ),
            "open-mixtral-8x7b": MistralModel(
                "open-mixtral-8x7b", "Open-source Mixtral 8x7B model", "general"
            ),
            "open-mistral-7b": MistralModel(
                "open-mistral-7b", "Open-source Mistral 7B model", "general"
            ),
            "mistral-embed": MistralModel(
                "mistral-embed",
                "Text embedding model for vector representations",
                "embedding",
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

    def generate_response(
        self,
        prompt: str,
        model_name: str = "mistral-medium",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Union[str, Dict]]:
        """Generate a response using the specified Mistral AI model."""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            payload = {
                "model": model_name,
                "messages": [],
                "temperature": temperature,
            }

            # Add system prompt if provided
            if system_prompt:
                payload["messages"].append({"role": "system", "content": system_prompt})

            # Add user message
            payload["messages"].append({"role": "user", "content": prompt})

            # Add max tokens if specified
            if max_tokens:
                payload["max_tokens"] = max_tokens

            response = requests.post(
                f"{self.base_url}/chat/completions", headers=headers, json=payload
            )

            if response.status_code == 200:
                result = response.json()
                content = (
                    result.get("choices", [{}])[0].get("message", {}).get("content", "")
                )
                usage = result.get("usage", {})

                return {
                    "text": content,
                    "metadata": {
                        "model": model_name,
                        "tokens": usage.get("total_tokens", 0),
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
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

    def generate_embeddings(
        self, texts: List[str], model_name: str = "mistral-embed"
    ) -> Dict[str, Union[List[List[float]], Dict]]:
        """Generate embeddings for a list of texts."""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            payload = {
                "model": model_name,
                "input": texts,
            }

            response = requests.post(
                f"{self.base_url}/embeddings", headers=headers, json=payload
            )

            if response.status_code == 200:
                result = response.json()
                embeddings = [
                    item.get("embedding", []) for item in result.get("data", [])
                ]
                usage = result.get("usage", {})

                return {
                    "embeddings": embeddings,
                    "metadata": {
                        "model": model_name,
                        "tokens": usage.get("total_tokens", 0),
                    },
                }
            else:
                return {
                    "embeddings": [],
                    "metadata": {
                        "error": True,
                        "message": f"Error: {response.status_code} - {response.text}",
                    },
                }

        except Exception as e:
            return {
                "embeddings": [],
                "metadata": {
                    "error": True,
                    "message": f"Error generating embeddings: {str(e)}",
                },
            }

    def get_model_info(self, model_name: str) -> Optional[Dict]:
        """Get information about a specific model."""
        if model_name in self.available_models:
            model = self.available_models[model_name]
            return {
                "name": model.name,
                "description": model.description,
                "category": model.category,
            }
        return None
