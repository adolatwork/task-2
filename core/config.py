import os

from typing import Optional

from pydantic_core import Url
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    """
    Application settings
    """
    SVC_NAME: str = 'Currency Conversion API'
    SVC_HOST: str = '0.0.0.0'
    SVC_PORT: int = 8000
    SVC_DEBUG: bool = False
    SVC_RELOAD: bool = False
    
    STATIC_URL: str = '/static/'
    STATIC_ROOT: str = f"{BASE_DIR}/static"

    LOG_LEVEL: str = "INFO"
    
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_USERNAME: Optional[str] = None
    REDIS_TIMEOUT: int = 5
    REDIS_SSL: bool = False
    
    CACHE_TTL_SECONDS: int = 30 * 60  # 30 daqiqa
    
    EXCHANGE_RATES_API: Url
    EXCHANGE_RATES_API_KEY: str
    EXCHANGE_RATES_TIMEOUT: int = 10
    
    FIXER_API: Optional[Url] = None
    FIXER_API_KEY: Optional[str] = None
    
    CORS_ORIGINS: list = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["*"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    @property
    def redis_dsn(self) -> Optional[str]:
        """Redis DSN yaratish"""
        if not self.REDIS_HOST:
            return None

        protocol = "rediss" if self.REDIS_SSL else "redis"

        if self.REDIS_USERNAME and self.REDIS_PASSWORD:
            return f"{protocol}://{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        elif self.REDIS_PASSWORD:
            return f"{protocol}://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        else:
            return f"{protocol}://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=False,
        case_sensitive=False,
        extra="ignore"
    )

settings = Settings()
