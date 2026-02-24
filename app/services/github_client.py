import httpx
from typing import List, Dict, Any, Optional
import asyncio

from app.core.logger import logger
from app.models.github import PRFile
from app.services.github_auth import GitHubAppAuth

class GitHubClient:
    """
    Client for interacting with the GitHub REST API.
    Handles rate-limiting retries (429) automatically.
    Uses dynamic GitHub App Installation Tokens for authentication.
    """
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.auth_service = GitHubAppAuth()
        self.base_headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _request(self, method: str, url: str, owner: str, repo: str, **kwargs) -> httpx.Response:
        """Helper to centralize HTTP calls, token injection, and retry logic."""
        
        # 1. Fetch Installation access token dynamically for this specific repository
        try:
            installation_token = await self.auth_service.get_installation_token(owner, repo)
        except Exception as e:
            logger.error(f"Failed to fetch installation token: {str(e)}")
            raise

        headers = self.base_headers.copy()
        headers["Authorization"] = f"Bearer {installation_token}"
        
        # Allow override of headers from kwargs
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
            
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(method, url, headers=headers, **kwargs)
                    
                    if response.status_code == 429:
                        retry_after = int(response.headers.get("Retry-After", 5))
                        logger.warning(f"GitHub API Rate Limit Exceeded (429). Retrying in {retry_after}s...")
                        await asyncio.sleep(retry_after)
                        continue
                        
                    response.raise_for_status()
                    return response
            except httpx.HTTPStatusError as e:
                logger.error(f"GitHub API Error: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                logger.error(f"GitHub API Network Error: {str(e)}")
                raise
                
        raise Exception("Max retries exceeded for GitHub API.")

    async def get_pr_files(self, owner: str, repo: str, pull_number: int) -> List[PRFile]:
        """Fetch the list of changed files for a pull request."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/files?per_page=100"
        
        response = await self._request("GET", url, owner=owner, repo=repo)
        data = response.json()
        
        return [PRFile(**file_data) for file_data in data]

    async def post_pr_review(self, owner: str, repo: str, pull_number: int, review_body: str, event: str = "COMMENT") -> None:
        """Post a review comment to the Pull Request with an explicit verdict."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
        payload = {
            "body": review_body,
            "event": event
        }
        
        await self._request("POST", url, owner=owner, repo=repo, json=payload)
        logger.info(f"Successfully posted PR review ({event}) to {owner}/{repo}#{pull_number} using GitHub App token")

    async def create_commit_status(self, owner: str, repo: str, sha: str, state: str, description: str, context: str) -> None:
        """
        Create a commit status (pending, success, error, failure)
        This shows up as the green checkmark or yellow dot on the PR.
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/statuses/{sha}"
        payload = {
            "state": state,
            "description": description[:140], # GitHub limits description to 140 chars
            "context": context
        }
        
        try:
            await self._request("POST", url, owner=owner, repo=repo, json=payload)
            logger.info(f"Successfully set commit {sha} status to {state} ({context})")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                logger.warning(
                    f"Skipping commit status for {sha}: GitHub App lacks 'Commit statuses' (Read & write) permissions. "
                    "Please update permissions in GitHub App settings."
                )
            else:
                logger.error(f"Failed to set commit status {sha}: {str(e)}")
                # We don't raise here because we don't want to fail the entire AI review pipeline just for a missing status dot
