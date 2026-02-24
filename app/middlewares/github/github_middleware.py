import hashlib
import hmac

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.settings import settings
from app.core.logger import logger


class GitHubWebhookMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only validate requests hitting the github webhook route
        if not request.url.path.endswith("/github/webhook"):
            return await call_next(request)

        # 1. Must have the signature header
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            logger.warning("Rejected webhook request: Missing X-Hub-Signature-256 header")
            return JSONResponse(status_code=401, content={"detail": "Missing signature header"})

        # 2. Must have the GitHub event header
        event = request.headers.get("X-GitHub-Event")
        if not event:
            logger.warning("Rejected webhook request: Missing X-GitHub-Event header")
            return JSONResponse(status_code=400, content={"detail": "Missing X-GitHub-Event header"})

        # 3. Read the raw body and validate the HMAC signature
        body = await request.body()

        expected_signature = "sha256=" + hmac.new(
            key=settings.SECRET_KEY.encode(),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        # 4. Use compare_digest to prevent timing attacks
        if not hmac.compare_digest(expected_signature, signature):
            logger.error(f"Rejected webhook request: Invalid signature for event '{event}'")
            return JSONResponse(status_code=401, content={"detail": "Invalid signature"})

        logger.info(f"Successfully validated GitHub webhook signature for event '{event}'")
        return await call_next(request)