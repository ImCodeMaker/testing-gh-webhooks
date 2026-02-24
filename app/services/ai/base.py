from abc import ABC, abstractmethod

class AIProvider(ABC):
    """Abstract base class for all AI code review providers."""

    @abstractmethod
    async def review_code(self, diff: str, context: dict) -> str:
        """
        Analyze the pull request diff and return a markdown-formatted review.
        
        Args:
            diff (str): The git patch/diff string for the file or chunks of files.
            context (dict): Additional context such as repo name, PR title, filename.
            
        Returns:
            str: The PR review comment or feedback.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the AI provider API is reachable and configured properly.
        
        Returns:
            bool: True if healthy, False otherwise.
        """
        pass
