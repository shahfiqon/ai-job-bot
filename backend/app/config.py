from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/jobbot",
        description="PostgreSQL connection string",
    )
    PROXYCURL_API_KEY: str = Field(
        description="Proxycurl API key for company enrichment (required for CLI scrape command)",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("PROXYCURL_API_KEY")
    @classmethod
    def validate_proxycurl_key(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError(
                "PROXYCURL_API_KEY is required. Grab one from https://nubela.co/proxycurl"
            )
        return value


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
