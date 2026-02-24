from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    SECRET_KEY: str
    API_VERSION: str = os.getenv("API_VERSION", "v1")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Discord Bot Configuration
    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_CHANNEL_ID: str = os.getenv("DISCORD_CHANNEL_ID", "")
    
    # AI Code Review System Configuration
    GITHUB_APP_ID: str | None = os.getenv("GITHUB_APP_ID")
    GITHUB_PRIVATE_KEY: str | None = os.getenv("GITHUB_PRIVATE_KEY")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "anthropic")
    AI_MODEL: str | None = os.getenv("AI_MODEL")
    
    # Provider API keys
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()