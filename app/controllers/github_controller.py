from fastapi import APIRouter, Request, Header, BackgroundTasks
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

    async def webhook(self, request: Request, background_tasks: BackgroundTasks, x_github_event: str = Header(None)):
        logger.info(f"Processing webhook for event '{x_github_event}'")
        
        # Parse payload
        payload = await request.json()
        
        # Delegate to the Strategy Processor Context asynchronously via BackgroundTasks
        # Never block the GitHub webhook response
        background_tasks.add_task(self.processor.process_event, x_github_event, payload)
        
        return {"status": "ok"}