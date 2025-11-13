from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/jobbot",
        description="PostgreSQL connection string",
    )
    PROXYCURL_API_KEY: str | None = Field(
        default=None,
        description="Proxycurl API key for company enrichment (required for CLI scrape command)",
    )
    OLLAMA_SERVER_URL: str = Field(
        default="http://localhost:11434",
        description="Ollama server URL for LLM-based job description parsing",
    )
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        description="Comma-separated list of allowed origins for CORS",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

def get_settings() -> Settings:
    return Settings()


settings = get_settings()
