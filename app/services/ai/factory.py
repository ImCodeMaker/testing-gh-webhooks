from app.core.settings import settings
from app.core.logger import logger
from app.services.ai.base import AIProvider

_provider_instance: AIProvider | None = None

def get_ai_provider() -> AIProvider:
    """
    Factory function to instantiate and return the configured AI Provider.
    Raises ValueError on startup if the requested AI_PROVIDER is unsupported.
    It returns a singleton instance.
    """
    global _provider_instance
    if _provider_instance is not None:
        return _provider_instance

    provider_name = settings.AI_PROVIDER.lower()
    
    match provider_name:
        case "anthropic":
            from app.services.ai.anthropic import AnthropicProvider
            _provider_instance = AnthropicProvider()
        case "openai":
            from app.services.ai.openai import OpenAIProvider
            _provider_instance = OpenAIProvider()
        case "gemini":
            from app.services.ai.gemini import GeminiProvider
            _provider_instance = GeminiProvider()
        case "groq":
            from app.services.ai.groq import GroqProvider
            _provider_instance = GroqProvider()
        case "ollama":
            from app.services.ai.ollama import OllamaProvider
            _provider_instance = OllamaProvider()
        case _:
            raise ValueError(f"Unsupported AI_PROVIDER configured: '{provider_name}'. Must be one of: anthropic, openai, gemini, groq, ollama.")
            
    logger.info(f"Initialized AI Provider: {provider_name.capitalize()}")
    return _provider_instance
