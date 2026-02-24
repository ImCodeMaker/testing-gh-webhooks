from typing import Any, Dict, Optional

from app.core.logger import logger
from app.services.github.strategies.base import GitHubEventStrategy
from app.services.github.strategies.push import PushStrategy
from app.services.github.strategies.pull_request import PullRequestStrategy
from app.services.github.strategies.issues import IssuesStrategy
from app.services.github.strategies.default import DefaultStrategy


class GitHubEventProcessor:
    """
    Context class for the Strategy Pattern.
    Routes GitHub webhook events to the appropriate Strategy implementation.
    """
    
    def __init__(self):
        # Initialize and register the supported strategies
        self._strategies: Dict[str, GitHubEventStrategy] = {
            "push": PushStrategy(),
            "pull_request": PullRequestStrategy(),
            "issues": IssuesStrategy(),
        }
        
        # Fallback behaviour for unmapped events
        self._default_strategy = DefaultStrategy()

    def _get_strategy(self, event_type: str) -> GitHubEventStrategy:
        """Retrieves the matching strategy or returns the default fallback."""
        return self._strategies.get(event_type, self._default_strategy)

    async def process_event(self, event_type: Optional[str], payload: Dict[str, Any]) -> None:
        """
        Executes the appropriate strategy based on the event_type provided in the headers.
        
        Args:
            event_type: Value of the 'X-GitHub-Event' header
            payload: JSON body payload of the webhook request.
        """
        
        event_name = event_type.lower() if event_type else "unknown"
        strategy = self._get_strategy(event_name)
        
        logger.debug(f"Routing event '{event_name}' to {strategy.__class__.__name__}")
        
        # Execute the defined strategy
        await strategy.execute(payload)
