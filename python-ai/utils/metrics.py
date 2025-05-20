from prometheus_client import Counter, Histogram, Gauge, Summary
import time
from functools import wraps
from typing import Callable, Any

# API Metrics
api_request_count = Counter(
    "api_request_total",
    "Total number of API requests",
    ["method", "endpoint", "status"],
)

api_request_latency = Histogram(
    "api_request_duration_seconds",
    "API request latency in seconds",
    ["method", "endpoint"],
)

# AI Model Metrics
model_inference_count = Counter(
    "model_inference_total",
    "Total number of model inferences",
    ["model_name", "status"],
)

model_inference_latency = Histogram(
    "model_inference_duration_seconds",
    "Model inference latency in seconds",
    ["model_name"],
)

# System Metrics
memory_usage = Gauge("memory_usage_bytes", "Memory usage in bytes")

cpu_usage = Gauge("cpu_usage_percent", "CPU usage percentage")

# Custom Metrics
active_conversations = Gauge("active_conversations", "Number of active conversations")

knowledge_base_size = Gauge(
    "knowledge_base_size", "Size of the knowledge base in entries"
)


def track_api_metrics(method: str, endpoint: str):
    """
    Decorator to track API metrics.

    Args:
        method (str): HTTP method
        endpoint (str): API endpoint
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                response = await func(*args, **kwargs)
                status = "success"
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                api_request_count.labels(
                    method=method, endpoint=endpoint, status=status
                ).inc()
                api_request_latency.labels(method=method, endpoint=endpoint).observe(
                    duration
                )
            return response

        return wrapper

    return decorator


def track_model_metrics(model_name: str):
    """
    Decorator to track model inference metrics.

    Args:
        model_name (str): Name of the AI model
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                response = await func(*args, **kwargs)
                status = "success"
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                model_inference_count.labels(model_name=model_name, status=status).inc()
                model_inference_latency.labels(model_name=model_name).observe(duration)
            return response

        return wrapper

    return decorator


def update_system_metrics():
    """
    Update system metrics (memory and CPU usage).
    This should be called periodically.
    """
    import psutil

    # Update memory usage
    process = psutil.Process()
    memory_usage.set(process.memory_info().rss)

    # Update CPU usage
    cpu_usage.set(psutil.cpu_percent())


def update_custom_metrics(conversation_count: int, kb_size: int):
    """
    Update custom metrics.

    Args:
        conversation_count (int): Number of active conversations
        kb_size (int): Size of the knowledge base
    """
    active_conversations.set(conversation_count)
    knowledge_base_size.set(kb_size)
