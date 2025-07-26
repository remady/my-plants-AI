"""Custom middleware for tracking metrics and other cross-cutting concerns."""

import time
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    db_connections,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking HTTP request metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track metrics for each request.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response: The response from the application
        """
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time

            # Record metrics
            http_requests_total.labels(method=request.method, endpoint=request.url.path, status=status_code).inc()
            http_request_duration_seconds.labels(method=request.method, endpoint=request.url.path).observe(duration)

        return response

class LimitFileSizeMiddleware(BaseHTTPMiddleware):
    """Middleware to limit uploaded to the server file size."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Set the maximum upload file to 500MB."""
        max_size = 1024 * 1024 * 512  # 500MB
        
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > max_size:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "File too large"}
                )
        
        response = await call_next(request)
        return response
