from abc import ABC, abstractmethod
from typing import Any, Dict

from app.core.logger import logger


class NotificationTemplate(ABC):
    """
    Abstract Base Class defining the Template Method for sending notifications.
    It establishes the skeletal algorithm that all notification services must follow.
    """

    async def send_notification(self, title: str, message: str, metadata: Dict[str, Any] = None) -> bool:
        """
        The Template Method. 
        Defines the exact sequence of steps to format and send a notification.
        This method should generally not be overridden by subclasses.
        """
        if not self._is_enabled():
            logger.debug(f"Skipping notification for {self.__class__.__name__}: Service is disabled")
            return False

        try:
            # Step 1: Format the specific payload required by the provider
            payload = self._format_payload(title, message, metadata or {})
            
            # Hook: Allow subclasses to run pre-validation or enrichment
            self._pre_send_hook(payload)
            
            # Step 2: Actually send the data across the wire
            success = await self._dispatch(payload)
            
            if success:
                logger.debug(f"Successfully dispatched notification via {self.__class__.__name__}")
            else:
                logger.error(f"Failed to dispatch notification via {self.__class__.__name__}")
                
            return success

        except Exception as e:
            logger.error(f"Exception while sending notification via {self.__class__.__name__}: {str(e)}", exc_info=True)
            return False

    # --- Abstract Steps (Subclasses MUST implement these) ---

    @abstractmethod
    def _is_enabled(self) -> bool:
        """Check if the service is properly configured and enabled."""
        pass

    @abstractmethod
    def _format_payload(self, title: str, message: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Convert the raw title/message into the provider's specific payload structure."""
        pass

    @abstractmethod
    async def _dispatch(self, payload: Dict[str, Any]) -> bool:
        """Execute the actual network request to send the notification."""
        pass

    # --- Hooks (Subclasses CAN override these, but don't have to) ---

    def _pre_send_hook(self, payload: Dict[str, Any]) -> None:
        """
        Optional Hook step executed right before '_dispatch'. 
        Can be used to log the payload, transform data, or run assertions.
        """
        pass
