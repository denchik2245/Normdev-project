from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Site Audit Service"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    debug: bool = True
    database_url: str = "sqlite:///./site_audit.db"
    reports_dir: str = "reports"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()