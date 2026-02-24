import google.generativeai as genai
from typing import Dict, Any

from app.core.settings import settings
from app.core.logger import logger
from app.services.ai.base import AIProvider

class GeminiProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set but GeminiProvider was instantiated.")
            
        genai.configure(api_key=self.api_key)
        self.model_name = settings.AI_MODEL or "gemini-2.5-pro"
        
        # We instantiate it directly
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction="You are a senior backend engineer performing a thorough code review. Focus on identifying bugs, security issues, performance bottlenecks, code smells, and missing error handling. Keep feedback concise, actionable, and formatted in markdown. No fluff, just real professional comments."
        )

    async def review_code(self, diff: str, context: Dict[str, Any]) -> str:
        prompt = self._build_prompt(diff, context)
        
        try:
            # Use async generation wrapper since standard generativeai sdk might be sync depending on the method
            # For purely async, SDK has generate_content_async since v0.5.0
            response = await self.model.generate_content_async(
                contents=prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=4096,
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API Error: {str(e)}")
            return f"Error analyzing code with Gemini: {str(e)}"

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
