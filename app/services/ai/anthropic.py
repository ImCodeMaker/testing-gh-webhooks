import os
from typing import Dict, Any
from anthropic import AsyncAnthropic

from app.core.settings import settings
from app.core.logger import logger
from app.services.ai.base import AIProvider
from app.services.ai.prompt import REVIEW_PROMPT_TEMPLATE
from app.services.ai.base import AIProvider

class AnthropicProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY is not set but AnthropicProvider was instantiated.")
            
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.model = settings.AI_MODEL or "claude-3-5-sonnet-20241022"
        
    async def review_code(self, diff: str, context: Dict[str, Any]) -> str:
        prompt = self._build_prompt(diff, context)
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.2,
                system="You are a senior backend engineer performing a thorough code review. Focus on identifying bugs, security issues, performance bottlenecks, code smells, and missing error handling. Keep feedback concise, actionable, and formatted in markdown. No fluff, just real professional comments.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API Error: {str(e)}")
            return f"Error analyzing code with Anthropic: {str(e)}"

    async def health_check(self) -> bool:
        if not self.api_key:
            return False
        return True
            
    def _build_prompt(self, diff: str, context: Dict[str, Any]) -> str:
        repo = context.get('repo', 'Unknown')
        title = context.get('title', 'Unknown Title')
        filename = context.get('filename', 'Unknown File')
        
        return REVIEW_PROMPT_TEMPLATE.format(
            repo=repo,
            title=title,
            filename=filename,
            diff=diff
        )
