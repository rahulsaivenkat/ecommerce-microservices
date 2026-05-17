from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    PRODUCTS_SERVICE_URL: str = "http://products:8002"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    SERVICE_NAME: str = "orders"

@lru_cache
def get_settings() -> Settings:
    return Settings()