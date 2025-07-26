"""Prometheus metrics configuration for the application.

This module sets up and configures Prometheus metrics for monitoring the application.
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from starlette_prometheus import metrics, PrometheusMiddleware

# Request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

# Database metrics
db_connections = Gauge("db_connections", "Number of active database connections")


# LLM tokens
llm_total_tokens_used = Gauge(
    "llm_total_tokens",
    "Total number of tokens used",
    ["session_id", "model"],
)

llm_input_tokens_used = Gauge(
    "llm_input_tokens",
    "Number of input tokens used",
    ["session_id", "model"],
)

llm_output_tokens_used = Gauge(
    "llm_output_tokens",
    "Number of output tokens used",
    ["session_id", "model"],
)

llm_total_cost = Gauge(
    "llm_total_cost",
    "Total cost for tokens used",
    ["session_id", "model"],
)


# LLM tools
llm_tool_calls = Gauge(
    "llm_tool_calls",
    "Total calls of available tools",
    ["tool_name", "session_id", "model"],
)

llm_tool_call_duration_seconds = Histogram(
    "llm_tool_call_duration_seconds",
    "Time spent processing tool inference",
    ["tool_name", "session_id", "model"],
    buckets=(0.1, 0.3, 0.5, 1.0, 2.0, 5.0)
)

# LLM timings
llm_inference_duration_seconds = Histogram(
    "llm_inference_duration_seconds",
    "Time spent processing LLM inference",
    ["model"],
    buckets=[0.1, 0.3, 0.5, 1.0, 2.0, 5.0, 10, 15],
)


llm_stream_duration_seconds = Histogram(
    "llm_stream_duration_seconds",
    "Time spent processing LLM stream inference",
    ["model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 20.0],
)


llm_response_duration = Histogram(
    "llm_response_duration_seconds", "Time spent on LLM requests", ["session_id", "model"]
)


def setup_metrics(app):
    """Set up Prometheus metrics middleware and endpoints.

    Args:
        app: FastAPI application instance
    """
    # Add Prometheus middleware
    app.add_middleware(PrometheusMiddleware)

    # Add metrics endpoint
    app.add_route("/metrics", metrics)
