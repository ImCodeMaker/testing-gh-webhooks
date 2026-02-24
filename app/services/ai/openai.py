from typing import Dict, Any
from openai import AsyncOpenAI

from app.core.settings import settings
from app.core.logger import logger
from app.services.ai.base import AIProvider

class OpenAIProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if not self.api_key:
            logger.warning("OPENAI_API_KEY is not set but OpenAIProvider was instantiated.")
            
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = settings.AI_MODEL or "gpt-4o"
        
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
            logger.error(f"OpenAI API Error: {str(e)}")
            return f"Error analyzing code with OpenAI: {str(e)}"

    async def health_check(self) -> bool:
        return bool(self.api_key)
            
    def _build_prompt(self, diff: str, context: Dict[str, Any]) -> str:
        repo = context.get('repo', 'Unknown')
        title = context.get('title', 'Unknown Title')
        filename = context.get('filename', 'Unknown File')
        
        return f"""
Please review the following code changes for the file `{filename}` in repository `{repo}`.
Pull Request Title: {title}

Diff:
```diff
{diff}
```

Provide explicit feedback on the additions and modifications. If everything looks good, briefly state that. 
Highlight lines roughly if possible and be constructive.
"""
