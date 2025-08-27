from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    gptunnel_api_key: str
    gptunnel_base_url: str = "https://gptunnel.ru/v1"
    port: int = 8000
    host: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
