import httpx
from typing import Any, Dict

from app.core.logger import logger
from app.core.settings import settings
from app.services.notifications.template import NotificationTemplate


class DiscordNotification(NotificationTemplate):
    """
    Concrete implementation of the NotificationTemplate for Discord Bots.
    Sends messages as a verified Discord Application using a Bot Token.
    """

    def _is_enabled(self) -> bool:
        # Service is only enabled if BOTH the bot token and channel ID exist
        return bool(settings.DISCORD_BOT_TOKEN and settings.DISCORD_CHANNEL_ID)

    def _format_payload(self, title: str, message: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Formats the data into Discord's specific Embed JSON structure for bots."""
        
        color = metadata.get("color", 3447003) 
        
        embed = {
            "title": title,
            "description": message,
            "color": color,
        }
        
        if "author" in metadata:
            embed["author"] = {"name": metadata["author"]}
            
        if "url" in metadata:
            embed["url"] = metadata["url"]

        # Note: 'username' and 'avatar_url' are not allowed when sending as a Bot, 
        # they are tied to the App credentials themselves.
        return {
            "embeds": [embed]
        }

    async def _dispatch(self, payload: Dict[str, Any]) -> bool:
        """Uses HTTPX to send the formatted JSON to the Discord Channel Messages API."""
        
        # Discord Bot API endpoint for sending a message to a specific channel
        api_url = f"https://discord.com/api/v10/channels/{settings.DISCORD_CHANNEL_ID}/messages"
        
        headers = {
            "Authorization": f"Bot {settings.DISCORD_BOT_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url=api_url,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                
                # Discord returns 200 OK with the created message object on success
                if response.status_code == 200:
                    return True
                    
                logger.error(f"Discord API returned {response.status_code}: {response.text}")
                return False
                
        except httpx.RequestError as e:
            logger.error(f"Network error while reaching Discord API: {str(e)}")
            return False

    def _pre_send_hook(self, payload: Dict[str, Any]) -> None:
        """Override the optional hook to log the exact data being sent to Discord."""
        logger.debug(f"Preparing to send Discord Bot payload: {payload['embeds'][0]['title']}")
