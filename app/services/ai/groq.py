from typing import Dict, Any
from groq import AsyncGroq

from app.core.settings import settings
from app.core.logger import logger
from app.services.ai.base import AIProvider
from app.services.ai.prompt import REVIEW_PROMPT_TEMPLATE
from app.services.ai.base import AIProvider

class GroqProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            logger.warning("GROQ_API_KEY is not set but GroqProvider was instantiated.")
            
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = settings.AI_MODEL or "llama-3.1-70b-versatile"
        
    async def review_code(self, diff: str, context: Dict[str, Any]) -> str:
        prompt = self._build_prompt(diff, context)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a senior backend engineer performing a thorough code review. Focus on identifying bugs, security issues, performance bottlenecks, code smells, and missing error handling. Keep feedback concise, actionable, and formatted in markdown. No fluff, just real professional comments."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=4096
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Groq API Error: {str(e)}")
            return f"Error analyzing code with Groq: {str(e)}"

    async def health_check(self) -> bool:
        return bool(self.api_key)

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
