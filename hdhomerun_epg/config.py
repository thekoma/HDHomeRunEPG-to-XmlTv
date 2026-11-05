from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "hdhomerun.local"
    epg_days: int = 4
    # guide.php returns 4 hours per call, so larger chunks would leave gaps.
    epg_hours: int = 4
    output_filename: str = "epg.xml"
    debug_mode: str = "on"
    cache_db_path: str = "database/epg_cache.db"
    cache_ttl_seconds: int = 86400  # 24 Hours
    cache_enabled: bool = True

    class Config:
        env_prefix = "HDHOMERUN_"
        env_file = ".env"


settings = Settings()
