from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str
    REDIS_URL: str = "redis://redis:6379"
    SERVICE_NAME: str = "gateway"

    # Service URLs
    AUTH_SERVICE_URL: str = "http://auth:8001"
    PRODUCTS_SERVICE_URL: str = "http://products:8002"
    ORDERS_SERVICE_URL: str = "http://orders:8003"
    PAYMENT_SERVICE_URL: str = "http://payment:8004"
    NOTIFY_SERVICE_URL: str = "http://notify:8005"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
