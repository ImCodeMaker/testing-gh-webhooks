import os
from typing import Dict, Any
from anthropic import AsyncAnthropic

from app.core.settings import settings
from app.core.logger import logger
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
                system="You are a senior backend engineer performing a thorough code review. Structure your reply as follows:\n\n**Summary** — One short paragraph on overall assessment and whether the PR is approved or needs changes.\n\n**Critical** (if any) — Bugs, security issues, or blockers. For each: brief description, then a code block showing the current code, then a code block showing the recommended fix. Use fenced code blocks with a language tag on the opening line (e.g.on or for Python,avascript or for JS). Always include the language tag so the message renders with syntax highlighting.\n\n**Warnings** — Performance issues, missing validation, logging/observability, rate limiting, etc. Bullet list; add a small code snippet in a tagged code block only when it helps.\n\n**Suggestions** (non-blocking) — Style, constants, types, tests. Again use tagged code blocks (e.g.) for any code examples.\n\n**Verdict** — One line: e.g. \"Approve\", \"Approve with minor notes\", or \"Changes requested\".\n\nKeep feedback concise and actionable. No fluff. For every code block use the format: opening line (e.g.), then your code, then closing ```. This ensures syntax highlighting works when the review is posted to Discord.",
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
