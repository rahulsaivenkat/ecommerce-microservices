from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    REDIS_URL: str
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "placeholder@gmail.com"
    SMTP_PASSWORD: str = "placeholder"
    TWILIO_ACCOUNT_SID: str = "placeholder"
    TWILIO_AUTH_TOKEN: str = "placeholder"
    TWILIO_PHONE_NUMBER: str = "+10000000000"
    ADMIN_EMAIL: str = "admin@example.com"
    SERVICE_NAME: str = "notify"

@lru_cache
def get_settings() -> Settings:
    return Settings()