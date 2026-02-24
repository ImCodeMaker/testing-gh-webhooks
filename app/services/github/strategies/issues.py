from typing import Any, Dict

from app.core.logger import logger
from app.services.github.strategies.base import GitHubEventStrategy
from app.services.notifications.discord import DiscordNotification


class IssuesStrategy(GitHubEventStrategy):
    """Handles GitHub Issue events."""
    
    def __init__(self):
        self.discord = DiscordNotification()
        
    async def execute(self, payload: Dict[str, Any]) -> None:
        action = payload.get("action", "unknown action")
        issue = payload.get("issue", {})
        number = issue.get("number", "unknown")
        title = issue.get("title", "No Title")
        issue_url = issue.get("html_url", "")
        author = issue.get("user", {}).get("login", "Unknown user")
        repo_name = payload.get("repository", {}).get("full_name", "Unknown Repo")
        
        logger.info(f"Processing ISSUES event: Issue #{number} was {action}: {title}")
        
        color = 15105570 if action == "opened" else 10038562 # Orange open, Red closed
        
        # Execute the Template Method
        await self.discord.send_notification(
            title=f"🐛 Issue {action.capitalize()}",
            message=f"**[{repo_name}]** Issue #{number}: {title}\nAction by: {author}",
            metadata={
                "color": color,
                "author": author,
                "url": issue_url
            }
        )
