from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "API Gateway"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str
    REDIS_URL: str
    TARGET_SERVICE_URL: str = "https://httpbin.org"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
