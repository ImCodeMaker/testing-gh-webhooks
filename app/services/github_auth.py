import time
import jwt
import httpx
from typing import Dict, Any, Optional

from app.core.settings import settings
from app.core.logger import logger

class GitHubAppAuth:
    """
    Handles authentication as a GitHub App using JWTs and generating temporary
    Installation Access Tokens.
    """
    def __init__(self):
        self.app_id = settings.GITHUB_APP_ID
        self.private_key = settings.GITHUB_PRIVATE_KEY
        self.base_url = "https://api.github.com"
        
        # Simple memory cache mapping "owner/repo" -> {"token": str, "expires_at": float}
        # In a highly distributed env, use Redis. For standard API usage, memory is often fine.
        self._installation_tokens: Dict[str, Dict[str, Any]] = {}
        
    def _generate_jwt(self) -> str:
        """Sign a new JWT for the GitHub App. Valid for 10 minutes."""
        if not self.app_id or not self.private_key:
            raise ValueError("GITHUB_APP_ID and GITHUB_PRIVATE_KEY must be configured to use GitHub App Auth.")
            
        now = int(time.time())
        # The JWT must be generated with expiration up to 10 minutes in the future
        payload = {
            "iat": now - 60, # Issued at time, 60 seconds in the past to account for clock drift
            "exp": now + (10 * 60), # JWT expiration time (10 minutes max)
            "iss": self.app_id # GitHub App ID
        }
        
        # Replace literal \n in string from dotenv with actual newlines
        formatted_key = self.private_key.replace("\\n", "\n")
        
        encoded_jwt = jwt.encode(payload, formatted_key, algorithm="RS256")
        return encoded_jwt

    async def _get_app_installation_id(self, owner: str, repo: str) -> Optional[int]:
        """Fetch the internal Installation ID for a specific repository."""
        jwt_token = self._generate_jwt()
        
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        url = f"{self.base_url}/repos/{owner}/{repo}/installation"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 404:
                logger.error(f"GitHub App is not installed on repository: {owner}/{repo}")
                return None
                
            response.raise_for_status()
            data = response.json()
            return data.get("id")

    async def get_installation_token(self, owner: str, repo: str) -> str:
        """
        Get an installation access token for the given repository.
        Returns from cache if still valid, otherwise fetches a new one.
        """
        cache_key = f"{owner}/{repo}"
        cached = self._installation_tokens.get(cache_key)
        
        # Use cached token if it has more than 5 minutes of validity remaining
        if cached and cached["expires_at"] > (time.time() + 300):
            return cached["token"]
            
        # Fetch actual installation ID first
        installation_id = await self._get_app_installation_id(owner, repo)
        if not installation_id:
            raise Exception(f"Cannot obtain installation token because GitHub app is not installed on {owner}/{repo}")
            
        # Generate short-term JWT to authenticate as the App to request an installation token
        jwt_token = self._generate_jwt()
        
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        
        url = f"{self.base_url}/app/installations/{installation_id}/access_tokens"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            token = token_data.get("token")
            # GitHub returns expires_at as ISO 8601, but we just set expiration assuming 1 hr default
            expires_at = time.time() + 3500 # rough 1 hour expiration buffer
            
            self._installation_tokens[cache_key] = {
                "token": token,
                "expires_at": expires_at
            }
            logger.info(f"Generated new GitHub Installation Token for {owner}/{repo}")
            
            return token
