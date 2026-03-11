# backend/app/config.py
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM provider: "openai" or "gemini"
    LLM_PROVIDER: str = Field("openai", env="LLM_PROVIDER")

    # Canonical API key (preferred)
    LLM_API_KEY: str | None = Field(None, env="LLM_API_KEY")

    # Provider-specific keys (optional fallback)
    OPENAI_API_KEY: str | None = Field(None, env="OPENAI_API_KEY")
    GEMINI_API_KEY: str | None = Field(None, env="GEMINI_API_KEY")

    # Model configuration
    LLM_MODEL: str | None = Field(None, env="LLM_MODEL")
    MAX_TOKENS: int = Field(4096, env="MAX_TOKENS")

    # App configuration
    HOST: str = Field("127.0.0.1", env="HOST")
    PORT: int = Field(8000, env="PORT")
    FRONTEND_URL: str | None = Field(None, env="FRONTEND_URL")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"

    def __init__(self, **data):
        super().__init__(**data)

        # Normalize provider
        if self.LLM_PROVIDER:
            self.LLM_PROVIDER = self.LLM_PROVIDER.lower()

        # API key fallback logic
        if not self.LLM_API_KEY:
            if self.OPENAI_API_KEY:
                self.LLM_API_KEY = self.OPENAI_API_KEY
            elif self.GEMINI_API_KEY:
                self.LLM_API_KEY = self.GEMINI_API_KEY


settings = Settings()
