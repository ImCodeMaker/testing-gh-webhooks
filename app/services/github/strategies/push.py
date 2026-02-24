from typing import Any, Dict

from app.core.logger import logger
from app.services.github.strategies.base import GitHubEventStrategy
from app.services.notifications.discord import DiscordNotification


class PushStrategy(GitHubEventStrategy):
    """Handles GitHub Push events."""
    
    def __init__(self):
        self.discord = DiscordNotification()
    
    async def execute(self, payload: Dict[str, Any]) -> None:
        ref = payload.get("ref", "unknown branch")
        pusher = payload.get("pusher", {}).get("name", "Unknown user")
        repo_name = payload.get("repository", {}).get("full_name", "Unknown Repo")
        commits = payload.get("commits", [])
        
        logger.info(f"Processing PUSH event: Push to {ref} by {pusher}")
        
        # Build the Discord message
        title = f"🚀 New Push to {repo_name}"
        message = f"**{pusher}** pushed {len(commits)} commits to `{ref}`.\n\n"
        
        for commit in commits[:3]: # Show max 3 commits
            message += f"• `{commit.get('id', '')[:7]}` {commit.get('message', 'No commit message')}\n"
            
        if len(commits) > 3:
            message += f"...and {len(commits) - 3} more commits."
            
        # Execute the Template Method!
        await self.discord.send_notification(
            title=title, 
            message=message, 
            metadata={
                "color": 3066993, # A nice GitHub-esque green
                "author": pusher,
            }
        )
