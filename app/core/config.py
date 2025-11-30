from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: str

    PROJECT_NAME: str = "Finance Tracker"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()