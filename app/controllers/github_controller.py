from fastapi import APIRouter, Request, Header
from app.core.logger import logger
from app.services.github.processor import GitHubEventProcessor


class GithubController:
    def __init__(self):
        self.router = APIRouter(prefix="/github", tags=["Github"])
        self._register_routes()
        # Initialize the event processor Context once
        self.processor = GitHubEventProcessor()

    def _register_routes(self):
        self.router.add_api_route(
            "/",
            self.get,
            methods=["GET"]
        )

        self.router.add_api_route(
            "/webhook",
            self.webhook,
            methods=["POST"]
        )

    async def get(self):
        logger.debug("Health check 'Hello World' endpoint called")
        return {"message": "Hello World"}

    async def webhook(self, request: Request, x_github_event: str = Header(None)):
        logger.info(f"Processing webhook for event '{x_github_event}'")
        
        # Parse payload
        payload = await request.json()
        
        # For PULL_REQUEST events, offload to the Celery queue (guaranteed delivery, ordered, retries)
        if x_github_event in ["pull_request", "pull_request_review"]:
            from app.tasks.review import process_pull_request_review
            process_pull_request_review.delay(payload)
        else:
            # Fallback for generic unmapped events running locally in background
            logger.info("Routing generic unmapped event to local event loop.")
            import asyncio
            asyncio.create_task(self.processor.process_event(x_github_event, payload))
            
        return {"status": "ok"}