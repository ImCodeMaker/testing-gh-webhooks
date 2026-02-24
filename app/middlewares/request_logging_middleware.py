import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import request_id_ctx_var, logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        # Determine the request ID (check headers first, fallback to generating one)
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Set the context variable so the logger picks it up
        token = request_id_ctx_var.set(request_id)

        try:
            logger.info(f"Incoming request: {request.method} {request.url.path}")
            response = await call_next(request)
            
            logger.info(f"Request completed with status {response.status_code}")
            return response
        finally:
            # Reset the context variable to prevent leakage between requests
            request_id_ctx_var.reset(token)
