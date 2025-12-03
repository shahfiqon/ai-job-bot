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
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT token signing",
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Algorithm for JWT token signing",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=10080,
        description="Access token expiration time in minutes (default: 7 days)",
    )
    OPENAI_API_KEY: str | None = Field(
        default=None,
        description="OpenAI API key for resume tailoring",
    )
    ANTHROPIC_API_KEY: str | None = Field(
        default=None,
        description="Anthropic/Claude API key for resume tailoring",
    )
    RESUME_LLM_PROVIDER: str = Field(
        default="claude",
        description="LLM provider for resume tailoring ('claude' or 'openai')",
    )
    RESUME_LLM_MODEL: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="LLM model name for resume tailoring",
    )
    RESUME_LLM_TEMPERATURE: float = Field(
        default=0.3,
        description="Temperature setting for resume tailoring LLM (default: 0.3)",
    )
    RESUME_PDF_STORAGE_DIR: str = Field(
        default="/tmp/resume_pdfs",
        description="Directory to store generated resume PDFs",
    )
    JSONRESUME_THEME_PATH: str = Field(
        default="/home/shadeform/jsonresume-theme-caffine",
        description="Path to the jsonresume-theme-caffine Node.js project",
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
