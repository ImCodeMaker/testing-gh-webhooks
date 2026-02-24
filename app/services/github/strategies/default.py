from typing import Any, Dict

from app.core.logger import logger
from app.services.github.strategies.base import GitHubEventStrategy


class DefaultStrategy(GitHubEventStrategy):
    """Fallback handler for unmapped GitHub events."""
    
    async def execute(self, payload: Dict[str, Any]) -> None:
        logger.info(f"Processing unmapped GitHub event. Payload keys: {list(payload.keys())}")
        # Optionally track unmapped events or just ignore them smoothly
