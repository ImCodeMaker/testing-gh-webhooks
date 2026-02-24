from abc import ABC, abstractmethod
from typing import Any, Dict


class GitHubEventStrategy(ABC):
    """
    Abstract base class defining the Strategy interface for handling
    various GitHub webhook events.
    """
    
    @abstractmethod
    async def execute(self, payload: Dict[str, Any]) -> None:
        """
        Executes the business logic for the specific GitHub event.
        
        Args:
            payload (Dict[str, Any]): The parsed JSON body of the webhook.
        """
        pass
