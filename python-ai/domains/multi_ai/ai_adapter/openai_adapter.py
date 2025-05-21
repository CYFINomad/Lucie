from typing import Dict, List, Optional, Union
import requests
import json
from abc import ABC, abstractmethod


class OpenAIModel:
    def __init__(self, name: str, description: str, category: str):
        self.name = name
        self.description = description
        self.category = category


class OpenAIAdapter:
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.available_models = self._initialize_models()

    def _initialize_models(self) -> Dict[str, OpenAIModel]:
        """Initialize the available OpenAI models with their metadata."""
        return {
            # GPT-4 Models
            "gpt-4o": OpenAIModel(
                "gpt-4o",
                "Latest multimodal model with optimal performance and capabilities",
                "advanced",
            ),
            "gpt-4o-mini": OpenAIModel(
                "gpt-4o-mini",
                "More affordable version of GPT-4o with good performance",
                "general",
            ),
            "gpt-4-turbo": OpenAIModel(
                "gpt-4-turbo",
                "Optimized version of GPT-4 for cost-effectiveness",
                "advanced",
            ),
            "gpt-4": OpenAIModel(
                "gpt-4",
                "Original GPT-4 model with strong reasoning capabilities",
                "advanced",
            ),
            "gpt-4-vision-preview": OpenAIModel(
                "gpt-4-vision-preview",
                "GPT-4 with vision capabilities for image understanding",
                "multimodal",
            ),
            # GPT-3.5 Models
            "gpt-3.5-turbo": OpenAIModel(
                "gpt-3.5-turbo",
                "Fast and cost-effective model, good for most tasks",
                "general",
            ),
            "gpt-3.5-turbo-instruct": OpenAIModel(
                "gpt-3.5-turbo-instruct",
                "Optimized for following specific instructions",
                "general",
            ),
            # Function calling optimized models
            "gpt-4-turbo-preview": OpenAIModel(
                "gpt-4-turbo-preview",
                "Optimized for function calling and tool use",
                "specialized",
            ),
            # Embedding models
            "text-embedding-3-small": OpenAIModel(
                "text-embedding-3-small",
                "Efficient embedding model for vector representations",
                "embedding",
            ),
            "text-embedding-3-large": OpenAIModel(
                "text-embedding-3-large",
                "High-dimension embedding model for detailed vector representations",
                "embedding",
            ),
            "text-embedding-ada-002": OpenAIModel(
                "text-embedding-ada-002",
                "Legacy embedding model for backward compatibility",
                "embedding",
            ),
            # Moderation models
            "text-moderation-latest": OpenAIModel(
                "text-moderation-latest",
                "Latest model for content moderation",
                "moderation",
            ),
            # Audio models
            "whisper-1": OpenAIModel(
                "whisper-1", "Speech-to-text transcription model", "audio"
            ),
            "tts-1": OpenAIModel(
                "tts-1", "Text-to-speech model for generating audio", "audio"
            ),
            "tts-1-hd": OpenAIModel(
                "tts-1-hd", "High-definition text-to-speech model", "audio"
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

    def list_models(self) -> List[Dict]:
        """Get the complete list of models from OpenAI API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            response = requests.get(f"{self.base_url}/models", headers=headers)

            if response.status_code == 200:
                return response.json().get("data", [])
            else:
                print(f"Error listing models: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            print(f"Error listing models: {str(e)}")
            return []

    def generate_response(
        self,
        prompt: str,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Union[str, Dict]]:
        """Generate a response using the specified OpenAI model."""
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
        self, texts: List[str], model_name: str = "text-embedding-3-small"
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

    def moderate_content(self, content: str) -> Dict[str, Union[bool, Dict]]:
        """Check if content violates OpenAI's content policy."""
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            payload = {
                "input": content,
            }

            response = requests.post(
                f"{self.base_url}/moderations", headers=headers, json=payload
            )

            if response.status_code == 200:
                result = response.json()
                moderation_result = result.get("results", [{}])[0]

                return {
                    "flagged": moderation_result.get("flagged", False),
                    "categories": moderation_result.get("categories", {}),
                    "category_scores": moderation_result.get("category_scores", {}),
                    "metadata": {
                        "model": result.get("model", "text-moderation-latest"),
                    },
                }
            else:
                return {
                    "flagged": False,
                    "metadata": {
                        "error": True,
                        "message": f"Error: {response.status_code} - {response.text}",
                    },
                }

        except Exception as e:
            return {
                "flagged": False,
                "metadata": {
                    "error": True,
                    "message": f"Error in content moderation: {str(e)}",
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

        # If not in our predefined list, try to get it from the API
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            response = requests.get(
                f"{self.base_url}/models/{model_name}", headers=headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception as e:
            print(f"Error getting model info: {str(e)}")
            return None
