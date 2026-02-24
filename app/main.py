from fastapi import FastAPI
from dotenv import load_dotenv

from contextlib import asynccontextmanager

from app.api import api_router
from app.core.logger import logger
from app.middlewares.github.github_middleware import GitHubWebhookMiddleware
from app.middlewares.request_logging_middleware import RequestLoggingMiddleware

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Chief Webhooks service")
    yield
    logger.info("Shutting down Chief Webhooks service")

app = FastAPI(lifespan=lifespan)

# Register middleware
app.add_middleware(GitHubWebhookMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Register all API routes
app.include_router(api_router)
