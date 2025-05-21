# Multi-AI Domain

The `multi_ai` domain provides a unified interface for working with multiple AI providers and models. It allows for flexible interaction with different LLM providers, evaluating and comparing responses, and consolidating knowledge from multiple sources.

## Architecture

The domain consists of the following components:

### AI Adapters
Located in the `ai_adapter/` directory, these provide consistent interfaces to different AI providers:

- `ollama_adapter.py` - Interface to Ollama's local models
- `openai_adapter.py` - Interface to OpenAI models (GPT-3.5, GPT-4, etc.)
- `anthropic_adapter.py` - Interface to Anthropic Claude models
- `mistral_adapter.py` - Interface to Mistral AI models
- `mathgpt_adapter.py` - Interface to specialized math models

### Core Components

- `ai_orchestrator.py` - Main entry point that coordinates between different providers and models
- `knowledge_consolidator.py` - Combines outputs from multiple models to create more comprehensive responses
- `response_evaluator.py` - Evaluates the quality of AI responses based on various metrics

## Configuration

Provider-specific configurations are defined in the `config/` directory:

- `ollama_config.py` - Configuration for Ollama
- `openai_config.py` - Configuration for OpenAI
- `anthropic_config.py` - Configuration for Anthropic
- `mistral_config.py` - Configuration for Mistral AI
- `mathgpt_config.py` - Configuration for MathGPT

## Key Features

1. **Multi-provider support**: Interact with multiple AI providers through a unified interface
2. **Intelligent model selection**: Automatically choose the best model for specific tasks
3. **Response evaluation**: Assess the quality of responses using metrics like relevance, coherence, and factuality
4. **Knowledge consolidation**: Combine insights from multiple models to create more comprehensive responses
5. **Response comparison**: Compare outputs from different models to identify the best response
6. **Error resilience**: Graceful handling of provider failures and missing methods

## Usage Examples

### Basic Usage

```python
from domains.multi_ai.ai_orchestrator import AIOrchestrator

# Initialize with specific providers
orchestrator = AIOrchestrator(providers=["openai", "anthropic"])

# Generate a response using the most appropriate model
response = orchestrator.generate_response(
    prompt="Explain the concept of neural networks",
    task_type="general_chat"
)

print(response["response"])  # The AI's response
print(response["metadata"])  # Metadata including model, provider, etc.
print(response["evaluation"]["overall_score"])  # Quality score
```

### Using Multiple Providers

```python
# Generate responses from multiple providers and consolidate them
consolidated_response = orchestrator.generate_multi_provider_response(
    prompt="What are the key considerations for sustainable urban planning?",
    task_type="analysis",
    providers=["openai", "anthropic", "mistral"],
    consolidation_strategy="weight_by_confidence"
)

print(consolidated_response["response"])  # Consolidated response
print(consolidated_response["metadata"]["providers_used"])  # Providers used
print(consolidated_response["individual_responses"])  # Individual responses
```

### Comparing Model Responses

```python
# Compare responses from different models
comparison = orchestrator.compare_model_responses(
    prompt="Solve this differential equation: dy/dx = 2xy",
    models={
        "openai": ["gpt-4-0125-preview"],
        "anthropic": ["claude-3-opus-20240229"],
        "mathgpt": ["mathgpt-expert"]
    }
)

# Get the best response
best_response = comparison["ranked_evaluations"][0]["response"]["text"]
print(f"Best model: {comparison['best_model']}")
print(f"Best score: {comparison['best_score']}")
```

## Environment Variables

The following environment variables should be set for API access:

```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
MISTRAL_API_KEY=your_mistral_key
MATHGPT_API_KEY=your_mathgpt_key
```

## Error Handling

The domain includes robust error handling to manage provider failures, missing methods, and other issues. The `missing_method` decorator is used to gracefully handle missing functionality in adapters. 