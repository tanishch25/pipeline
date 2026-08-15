from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    PAGE_SPEED_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    ANALYZER_LLM_MODEL: str = "groq/llama3-8b-8192"
    PITCHER_LLM_MODEL: str = "ollama/llama3.1"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/leads.db"
    
    # Retry and timeout settings
    HTTP_TIMEOUT_SECONDS: int = 15
    PLAYWRIGHT_TIMEOUT_MS: int = 30000
    LITELLM_MAX_RETRIES: int = 3

    # Mail Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    IMAP_HOST: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    
    # Customization
    PORTFOLIO_LINK: str = "https://your-portfolio.com"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

import os
settings = Settings()

# Set env vars for litellm
if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
    os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY

if settings.GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY
