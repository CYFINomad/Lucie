from typing import Dict, List, Optional, Union, Any, Tuple
from .ai_adapter.ollama_adapter import OllamaAdapter
from .ai_adapter.openai_adapter import OpenAIAdapter
from .ai_adapter.anthropic_adapter import AnthropicAdapter
from .ai_adapter.mistral_adapter import MistralAdapter
from .ai_adapter.mathgpt_adapter import MathGPTAdapter
from .response_evaluator import ResponseEvaluator
from ..config.ollama_config import OllamaConfig

# Import additional config classes
from ..config.openai_config import OpenAIConfig
from ..config.anthropic_config import AnthropicConfig
from ..config.mistral_config import MistralConfig
from ..config.mathgpt_config import MathGPTConfig
import logging
from dataclasses import dataclass, field
import inspect
from functools import wraps


@dataclass
class DefaultConfig:
    """Default configuration for providers that don't have a specific config class."""

    default_temperature: float = 0.7
    default_max_tokens: int = 1000

    # Default system prompts for different task types
    system_prompts: Dict[str, str] = field(
        default_factory=lambda: {
            "general_chat": "You are a helpful assistant. Answer the user's question clearly and accurately.",
            "creative_writing": "You are a creative writing assistant. Help the user create engaging content.",
            "code": "You are a coding assistant. Help the user write clean, efficient, and working code.",
            "math": "You are a mathematics assistant. Help the user solve math problems step-by-step.",
            "analysis": "You are an analytical assistant. Help the user analyze data and draw insights.",
        }
    )

    # Default recommended models mapping
    recommended_models: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "general_chat": ["gpt-3.5-turbo"],
            "creative_writing": ["claude-3-sonnet-20240229"],
            "code": ["gpt-4-0125-preview"],
            "math": ["mathgpt-default"],
            "analysis": ["claude-3-opus-20240229"],
        }
    )

    def get_system_prompt(self, task_type: str) -> str:
        """Get the system prompt for a specific task type."""
        return self.system_prompts.get(task_type, self.system_prompts["general_chat"])

    def get_recommended_models(self, task_type: str) -> List[str]:
        """Get recommended models for a specific task type."""
        return self.recommended_models.get(task_type, ["gpt-3.5-turbo"])


def missing_method(default_value=None):
    """
    Decorator for handling missing methods in adapters.
    Returns the default value and logs an error if the method is called.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except (AttributeError, NotImplementedError) as e:
                # Log the error
                logging.getLogger(__name__).error(
                    f"Method {func.__name__} not implemented: {str(e)}"
                )
                return default_value
            except Exception as e:
                # Log other exceptions
                logging.getLogger(__name__).error(f"Error in {func.__name__}: {str(e)}")
                return default_value

        return wrapper

    return decorator


class AIOrchestrator:
    def __init__(self, providers: Optional[List[str]] = None):
        """
        Initialize the AI orchestrator with specified providers.

        Args:
            providers (List[str], optional): List of providers to enable.
                                           If None, all available providers are enabled.
        """
        self.logger = logging.getLogger(__name__)
        self.adapters = {}
        self.configs = {}
        self.response_evaluator = ResponseEvaluator()

        # Configure which providers to use
        available_providers = ["ollama", "openai", "anthropic", "mistral", "mathgpt"]
        providers_to_initialize = providers or available_providers

        # Initialize default config
        self.default_config = DefaultConfig()

        # Initialize requested adapters and their configs
        for provider in providers_to_initialize:
            try:
                if provider == "ollama":
                    self.adapters["ollama"] = OllamaAdapter()
                    self.configs["ollama"] = OllamaConfig()
                elif provider == "openai":
                    self.adapters["openai"] = OpenAIAdapter()
                    self.configs["openai"] = OpenAIConfig()
                elif provider == "anthropic":
                    self.adapters["anthropic"] = AnthropicAdapter()
                    self.configs["anthropic"] = AnthropicConfig()
                elif provider == "mistral":
                    self.adapters["mistral"] = MistralAdapter()
                    self.configs["mistral"] = MistralConfig()
                elif provider == "mathgpt":
                    self.adapters["mathgpt"] = MathGPTAdapter()
                    self.configs["mathgpt"] = MathGPTConfig()
                else:
                    self.logger.warning(f"Unknown provider: {provider}")
            except Exception as e:
                self.logger.error(f"Failed to initialize {provider} adapter: {str(e)}")

        if not self.adapters:
            self.logger.warning("No AI adapters were successfully initialized!")

    def get_available_models(
        self, provider: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Get list of available models, optionally filtered by provider.

        Args:
            provider (str, optional): Provider to filter models by.

        Returns:
            List[Dict[str, str]]: List of available models with metadata.
        """
        if provider:
            if provider in self.adapters:
                return self.adapters[provider].get_available_models()
            else:
                return []

        # Collect models from all providers
        all_models = []
        for provider_name, adapter in self.adapters.items():
            models = adapter.get_available_models()
            # Tag each model with its provider
            for model in models:
                model["provider"] = provider_name
            all_models.extend(models)

        return all_models

    def pull_model(self, model_name: str, provider: str = "ollama") -> bool:
        """
        Pull a model from the specified provider.

        Args:
            model_name (str): Name of the model to pull
            provider (str): Provider to pull from

        Returns:
            bool: Success status
        """
        if provider not in self.adapters:
            return False

        # Currently only Ollama supports pulling models
        if provider == "ollama":
            return self.adapters["ollama"].pull_model(model_name)

        return False

    def generate_response(
        self,
        prompt: str,
        task_type: str = "general_chat",
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        multimodal_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Union[str, Dict]]:
        """
        Generate a response using the most appropriate model for the task.

        Args:
            prompt (str): The user prompt to respond to
            task_type (str): Type of task (e.g., "general_chat", "math", "code")
            model_name (str, optional): Specific model to use
            provider (str, optional): Specific provider to use
            temperature (float, optional): Temperature for response generation
            max_tokens (int, optional): Maximum tokens in response
            system_prompt (str, optional): System prompt to use
            multimodal_data (Dict[str, Any], optional): Data for multimodal requests

        Returns:
            Dict[str, Union[str, Dict]]: Response with metadata
        """
        # Determine provider and model to use
        selected_provider, selected_model = self._select_provider_and_model(
            task_type, model_name, provider
        )

        if not selected_provider or selected_provider not in self.adapters:
            return {
                "response": "No suitable provider available for this request.",
                "metadata": {"error": "provider_not_available"},
            }

        # Get adapter for selected provider
        adapter = self.adapters[selected_provider]

        # Get system prompt if not specified
        if not system_prompt:
            system_prompt = self.configs[selected_provider].get_system_prompt(task_type)

        # Use default parameters if not specified
        temperature = temperature or self.configs[selected_provider].default_temperature
        max_tokens = max_tokens or self.configs[selected_provider].default_max_tokens

        # Generate response using selected adapter
        response = adapter.generate_response(
            prompt=prompt,
            model_name=selected_model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            multimodal_data=multimodal_data,
        )

        # Evaluate the response quality
        evaluation = self.response_evaluator.evaluate_response(
            prompt=prompt,
            response=response,
            is_creative_task=(
                task_type in ["creative_writing", "brainstorming", "ideation"]
            ),
            instructions=system_prompt,
        )

        # Add additional metadata
        response["metadata"].update(
            {
                "task_type": task_type,
                "model": selected_model,
                "provider": selected_provider,
                "quality_score": evaluation.get("overall_score", 0.0),
                "quality_category": evaluation.get("quality_category", "unknown"),
            }
        )

        return {
            "response": response["text"],
            "metadata": response["metadata"],
            "evaluation": evaluation,
        }

    def generate_multi_provider_response(
        self,
        prompt: str,
        task_type: str = "general_chat",
        providers: Optional[List[str]] = None,
        models: Optional[Dict[str, str]] = None,
        consolidation_strategy: str = "weight_by_confidence",
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate responses from multiple providers and consolidate them.

        Args:
            prompt (str): The prompt to respond to
            task_type (str): Type of task
            providers (List[str], optional): List of providers to use
            models (Dict[str, str], optional): Map of provider to model name
            consolidation_strategy (str): Strategy for consolidating responses
            system_prompt (str, optional): System prompt to use
            temperature (float, optional): Temperature for response generation
            max_tokens (int, optional): Maximum tokens in response

        Returns:
            Dict[str, Any]: Consolidated response with metadata
        """
        from .knowledge_consolidator import KnowledgeConsolidator

        # Use all available providers if none specified
        providers_to_use = providers or list(self.adapters.keys())

        # Generate responses from each provider
        responses = []
        for provider in providers_to_use:
            if provider in self.adapters:
                # Get model for this provider
                model = None
                if models and provider in models:
                    model = models[provider]

                try:
                    response = self.generate_response(
                        prompt=prompt,
                        task_type=task_type,
                        model_name=model,
                        provider=provider,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        system_prompt=system_prompt,
                    )

                    # Format for consolidator
                    responses.append(
                        {"text": response["response"], "metadata": response["metadata"]}
                    )
                except Exception as e:
                    self.logger.error(
                        f"Error generating response from {provider}: {str(e)}"
                    )

        # Consolidate responses
        if not responses:
            return {
                "response": "Failed to generate responses from any provider.",
                "metadata": {"error": "no_responses_generated"},
            }

        consolidator = KnowledgeConsolidator()
        consolidated = consolidator.consolidate_responses(
            responses=responses, strategy=consolidation_strategy
        )

        # Add additional metadata
        consolidated["metadata"]["task_type"] = task_type
        consolidated["metadata"]["providers_used"] = providers_to_use

        # Evaluate the consolidated response
        evaluation = self.response_evaluator.evaluate_response(
            prompt=prompt,
            response={"text": consolidated["text"], "metadata": {}},
            is_creative_task=(
                task_type in ["creative_writing", "brainstorming", "ideation"]
            ),
            instructions=system_prompt,
        )

        # Add evaluation metadata
        consolidated["metadata"]["quality_score"] = evaluation.get("overall_score", 0.0)
        consolidated["metadata"]["quality_category"] = evaluation.get(
            "quality_category", "unknown"
        )

        return {
            "response": consolidated["text"],
            "metadata": consolidated["metadata"],
            "evaluation": evaluation,
            "individual_responses": responses,
        }

    def get_model_info(
        self, model_name: str, provider: str = "ollama"
    ) -> Optional[Dict]:
        """
        Get information about a specific model.

        Args:
            model_name (str): Name of the model
            provider (str): Provider of the model

        Returns:
            Optional[Dict]: Model information if available
        """
        if provider not in self.adapters:
            return None

        return self.adapters[provider].get_model_info(model_name)

    def delete_model(self, model_name: str, provider: str = "ollama") -> bool:
        """
        Delete a model from a provider.

        Args:
            model_name (str): Name of the model to delete
            provider (str): Provider to delete from

        Returns:
            bool: Success status
        """
        if provider not in self.adapters:
            return False

        # Currently only Ollama supports model deletion
        if provider == "ollama":
            return self.adapters["ollama"].delete_model(model_name)

        return False

    def get_recommended_models_for_task(self, task_type: str) -> Dict[str, List[str]]:
        """
        Get recommended models for a specific task type from all providers.

        Args:
            task_type (str): Type of task

        Returns:
            Dict[str, List[str]]: Map of provider to list of recommended models
        """
        recommendations = {}

        # Get recommendations from each provider's config
        for provider, config in self.configs.items():
            if provider in self.adapters:
                try:
                    recommendations[provider] = config.get_recommended_models(task_type)
                except Exception as e:
                    self.logger.error(
                        f"Error getting recommendations for {provider}: {str(e)}"
                    )
                    # Use default recommendations if provider-specific ones fail
                    recommendations[provider] = (
                        self.default_config.get_recommended_models(task_type)
                    )

        return recommendations

    def compare_model_responses(
        self,
        prompt: str,
        models: Dict[str, List[str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """
        Generate and compare responses from multiple models.

        Args:
            prompt (str): The prompt to respond to
            models (Dict[str, List[str]]): Map of provider to list of models
            system_prompt (str, optional): System prompt to use
            temperature (float): Temperature for generation
            max_tokens (int): Maximum tokens in response

        Returns:
            Dict[str, Any]: Comparison results with rankings
        """
        responses = []

        # Generate responses from each model
        for provider, model_list in models.items():
            if provider not in self.adapters:
                continue

            for model in model_list:
                try:
                    response = self.generate_response(
                        prompt=prompt,
                        model_name=model,
                        provider=provider,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        system_prompt=system_prompt,
                    )

                    # Format for evaluator
                    responses.append(
                        {
                            "text": response["response"],
                            "metadata": {
                                "model": model,
                                "provider": provider,
                                **response["metadata"],
                            },
                        }
                    )
                except Exception as e:
                    self.logger.error(
                        f"Error generating response from {provider}/{model}: {str(e)}"
                    )

        # Compare responses
        comparison = self.response_evaluator.compare_responses(
            prompt=prompt, responses=responses, instructions=system_prompt
        )

        return comparison

    def _select_provider_and_model(
        self,
        task_type: str,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Select the most appropriate provider and model for a task.

        Args:
            task_type (str): Type of task
            model_name (str, optional): Requested model name
            provider (str, optional): Requested provider

        Returns:
            Tuple[Optional[str], Optional[str]]: (provider, model)
        """
        try:
            # If no adapters available, return None, None
            if not self.adapters:
                self.logger.warning("No adapters available for selection")
                return None, None

            # If provider and model are specified, use them
            if provider and model_name:
                if provider in self.adapters:
                    return provider, model_name
                else:
                    self.logger.warning(
                        f"Requested provider '{provider}' not available"
                    )

            # If only provider is specified, get recommended model
            if provider:
                if provider in self.adapters:
                    try:
                        # Get recommendations from this provider's config
                        if provider in self.configs:
                            recommended = self.configs[provider].get_recommended_models(
                                task_type
                            )
                            if recommended:
                                return provider, recommended[0]

                        # Fallback to default config recommendations
                        recommended = self.default_config.get_recommended_models(
                            task_type
                        )
                        if recommended:
                            return provider, recommended[0]

                        # Last resort: use any available model from this provider
                        models = self.get_available_models(provider)
                        if models:
                            return provider, models[0]["id"]
                    except Exception as e:
                        self.logger.error(
                            f"Error getting recommended model for {provider}: {str(e)}"
                        )

            # If only model is specified, find which provider has it
            if model_name:
                for prov, adapter in self.adapters.items():
                    try:
                        models = adapter.get_available_models()
                        if any(m.get("id", "") == model_name for m in models):
                            return prov, model_name
                    except Exception as e:
                        self.logger.error(
                            f"Error checking if {prov} has model {model_name}: {str(e)}"
                        )

            # Select based on task type and provider availability
            task_provider_mapping = {
                "math": "mathgpt",
                "complex_reasoning": "anthropic",
                "analysis": "anthropic",
                "code": "openai",
            }

            # Check if the recommended provider for this task type is available
            if task_type in task_provider_mapping:
                recommended_provider = task_provider_mapping[task_type]
                if recommended_provider in self.adapters:
                    # Get the recommended model from this provider
                    if recommended_provider in self.configs:
                        models = self.configs[
                            recommended_provider
                        ].get_recommended_models(task_type)
                        if models:
                            return recommended_provider, models[0]

            # Default to first available provider and its recommended model
            for prov in ["ollama", "openai", "anthropic", "mistral", "mathgpt"]:
                if prov in self.adapters and prov in self.configs:
                    try:
                        models = self.configs[prov].get_recommended_models(task_type)
                        if models:
                            return prov, models[0]
                    except Exception as e:
                        self.logger.error(
                            f"Error getting recommended model from {prov}: {str(e)}"
                        )

            # Last resort: just use the first provider and any model
            first_provider = next(iter(self.adapters.keys()))
            try:
                models = self.get_available_models(first_provider)
                if models:
                    self.logger.info(
                        f"Using first available model: {models[0]['id']} from {first_provider}"
                    )
                    return first_provider, models[0]["id"]
            except Exception as e:
                self.logger.error(
                    f"Error getting models from {first_provider}: {str(e)}"
                )

            # If we get here, we couldn't find any suitable provider or model
            self.logger.error("Could not select any suitable provider and model")
            return None, None

        except Exception as e:
            self.logger.error(f"Error in provider/model selection: {str(e)}")
            return None, None

    def validate_configurations(self) -> Dict[str, bool]:
        """
        Validate that all configurations are properly set up.

        Returns:
            Dict[str, bool]: Map of provider to validation status
        """
        validation_results = {}

        for provider, adapter in self.adapters.items():
            try:
                # Check that the adapter has necessary methods
                required_methods = ["generate_response", "get_available_models"]

                valid = all(hasattr(adapter, method) for method in required_methods)

                # Check that the config has necessary methods
                if provider in self.configs:
                    config = self.configs[provider]
                    config_methods = ["get_system_prompt", "get_recommended_models"]
                    valid = valid and all(
                        hasattr(config, method) for method in config_methods
                    )
                else:
                    valid = False

                validation_results[provider] = valid

                if not valid:
                    self.logger.warning(
                        f"Provider {provider} configuration is incomplete"
                    )
            except Exception as e:
                self.logger.error(
                    f"Error validating {provider} configuration: {str(e)}"
                )
                validation_results[provider] = False

        return validation_results
