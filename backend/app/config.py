import os
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM core strategy: "hybrid", "local", or "remote"
    LLM_PROVIDER: str = Field("hybrid", env="LLM_PROVIDER")

    # 🏢 Fireworks AI AMD-Hardware Configuration
    FIREWORKS_API_KEY: str | None = Field(None, env="FIREWORKS_API_KEY")
    # Restricted hackathon AMD endpoint identifier string
    FIREWORKS_MODEL: str = Field("accounts/fireworks/models/llama-v3p1-8b-instruct", env="FIREWORKS_MODEL")
    
    # 💻 Local CPU Inference Configuration (Standardized Container Pathing)
    LOCAL_MODEL_PATH: str = Field("models/qwen2.5-0.5b-instruct-q4_k_m.gguf", env="LOCAL_MODEL_PATH")
    LOCAL_MODEL_TYPE: str = Field("gguf", env="LOCAL_MODEL_TYPE")
    ROUTER_OVERHEAD_THRESHOLD_MS: float = Field(2.0, env="ROUTER_OVERHEAD_THRESHOLD_MS")

    # Legacy / Canonical key management for backwards compatibility
    LLM_API_KEY: str | None = Field(None, env="LLM_API_KEY")
    GEMINI_API_KEY: str | None = Field(None, env="GEMINI_API_KEY")

    # Token constraints & Optimization parameters
    LLM_MODEL: str | None = Field(None, env="LLM_MODEL")
    MAX_TOKENS: int = Field(4096, env="MAX_TOKENS")
    COMPRESSION_MIN_THRESHOLD: float = 0.20
    COMPRESSION_MAX_THRESHOLD: float = 0.35

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

        # Normalization
        if self.LLM_PROVIDER:
            self.LLM_PROVIDER = self.LLM_PROVIDER.lower()

        # Consolidate API Key Hierarchy for the Remote Gateway
        if not self.FIREWORKS_API_KEY and self.LLM_API_KEY:
            self.FIREWORKS_API_KEY = self.LLM_API_KEY
        elif self.FIREWORKS_API_KEY:
            self.LLM_API_KEY = self.FIREWORKS_API_KEY


settings = Settings()