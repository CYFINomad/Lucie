from typing import Dict, List, Optional, Union
import requests
import json
from abc import ABC, abstractmethod


class AnthropicModel:
    def __init__(self, name: str, description: str, category: str):
        self.name = name
        self.description = description
        self.category = category


class AnthropicAdapter:
    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.api_version = "2023-06-01"  # Anthropic API version
        self.available_models = self._initialize_models()

    def _initialize_models(self) -> Dict[str, AnthropicModel]:
        """Initialize the available Anthropic Claude models with their metadata."""
        return {
            "claude-3-opus-20240229": AnthropicModel(
                "claude-3-opus-20240229",
                "Most powerful model for highly complex tasks",
                "advanced",
            ),
            "claude-3-sonnet-20240229": AnthropicModel(
                "claude-3-sonnet-20240229",
                "Balanced model for general purpose use",
                "general",
            ),
            "claude-3-haiku-20240307": AnthropicModel(
                "claude-3-haiku-20240307",
                "Fast and cost-effective model for simpler tasks",
                "lightweight",
            ),
            "claude-2.1": AnthropicModel(
                "claude-2.1", "High-capability model with improved reasoning", "general"
            ),
            "claude-2.0": AnthropicModel(
                "claude-2.0", "Previous generation advanced model", "general"
            ),
            "claude-instant-1.2": AnthropicModel(
                "claude-instant-1.2",
                "Fast and efficient model for basic tasks",
                "lightweight",
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
        model_name: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
        max_tokens: Optional[int] = 1024,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Union[str, Dict]]:
        """Generate a response using the specified Anthropic Claude model."""
        try:
            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": self.api_key,
                "anthropic-version": self.api_version,
            }

            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt

            response = requests.post(
                f"{self.base_url}/v1/messages", headers=headers, json=payload
            )

            if response.status_code == 200:
                result = response.json()
                content = ""

                for content_block in result.get("content", []):
                    if content_block.get("type") == "text":
                        content += content_block.get("text", "")

                usage = result.get("usage", {})

                return {
                    "text": content,
                    "metadata": {
                        "model": model_name,
                        "tokens": usage.get("input_tokens", 0)
                        + usage.get("output_tokens", 0),
                        "prompt_tokens": usage.get("input_tokens", 0),
                        "completion_tokens": usage.get("output_tokens", 0),
                        "id": result.get("id", ""),
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

    def generate_multipart_response(
        self,
        text_prompt: str,
        image_urls: List[str] = None,
        model_name: str = "claude-3-sonnet-20240229",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Union[str, Dict]]:
        """Generate a response with multimodal inputs (text and images)."""
        try:
            if not image_urls:
                # If no images, use standard text generation
                return self.generate_response(
                    prompt=text_prompt,
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt,
                )

            headers = {
                "Content-Type": "application/json",
                "X-Api-Key": self.api_key,
                "anthropic-version": self.api_version,
            }

            # Construct the multipart message
            message_content = []

            # Add text content
            if text_prompt:
                message_content.append({"type": "text", "text": text_prompt})

            # Add image content
            for image_url in image_urls:
                message_content.append(
                    {"type": "image", "source": {"type": "url", "url": image_url}}
                )

            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": message_content}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            # Add system prompt if provided
            if system_prompt:
                payload["system"] = system_prompt

            response = requests.post(
                f"{self.base_url}/v1/messages", headers=headers, json=payload
            )

            if response.status_code == 200:
                result = response.json()
                content = ""

                for content_block in result.get("content", []):
                    if content_block.get("type") == "text":
                        content += content_block.get("text", "")

                usage = result.get("usage", {})

                return {
                    "text": content,
                    "metadata": {
                        "model": model_name,
                        "tokens": usage.get("input_tokens", 0)
                        + usage.get("output_tokens", 0),
                        "prompt_tokens": usage.get("input_tokens", 0),
                        "completion_tokens": usage.get("output_tokens", 0),
                        "id": result.get("id", ""),
                    },
                }
            else:
                return {
                    "text": f"Error: {response.status_code} - {response.text}",
                    "metadata": {"error": True},
                }

        except Exception as e:
            return {
                "text": f"Error generating multipart response: {str(e)}",
                "metadata": {"error": True},
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
