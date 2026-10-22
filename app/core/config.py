from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "HelpDesk API"
    app_version: str = "0.1.0"

    database_host: str = "127.0.0.1"
    database_port: int = 5432
    database_name: str = "helpdesk_db"
    database_user: str = "helpdesk_app"
    database_password: SecretStr | None = None

    jwt_secret_key: SecretStr = Field(min_length=32)
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,
    )
    jwt_algorithm: str = "HS256"

    @property
    def database_url(self) -> URL:
        if (
            self.database_password is None
            or not self.database_password.get_secret_value()
        ):
            raise ValueError(
                "Configure DATABASE_PASSWORD no arquivo .env."
            )

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.database_user,
            password=self.database_password.get_secret_value(),
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()