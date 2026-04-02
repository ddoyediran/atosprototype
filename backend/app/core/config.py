# Configuration Settings
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OPENAI Configuration
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.3

    # Pubmed Configuration
    PUBMED_EMAIL: str = "myemail.personal@example.com"
    PUBMED_TOOL: str = "capmed_sci_research_agent"
    PUBMED_MAX_RESULTS: int = 20

    # Application Settings
    APP_NAME: str = "CapMed-Sci"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    CORS_ALLOW_CREDENTIALS: bool = True

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Context Management
    MAX_CONTEXT_TOKENS: int = 120000
    MAX_CONVERSATION_TURNS: int = 5

    # Paper Full-text Configuration
    FULL_TEXT_PAPER_LIMIT: int = 10
    FULL_TEXT_TRUNCATION_CHARS: int = 10000

    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
settings = Settings()