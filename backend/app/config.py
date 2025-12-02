from dotenv import load_dotenv
load_dotenv()  # force load .env before Settings

from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    LLM_PROVIDER: str | None = Field(None, env="LLM_PROVIDER")
    LLM_API_KEY: str | None = Field(None, env="GEMINI_API_KEY")
    LLM_MODEL: str | None = Field(None, env="LLM_MODEL")

    MAX_TOKENS: int | None = 4096

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()