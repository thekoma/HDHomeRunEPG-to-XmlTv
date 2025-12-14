import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    hdhomerun_host: str = "hdhomerun.local"
    epg_days: int = 4
    epg_hours: int = 2
    output_filename: str = "epg.xml"
    debug_mode: str = "on"
    cache_db_path: str = "epg_cache.db"
    cache_ttl_seconds: int = 86400  # 24 Hours
    cache_enabled: bool = True

    class Config:
        env_prefix = "HDHOMERUN_"
        env_file = ".env"

settings = Settings()
