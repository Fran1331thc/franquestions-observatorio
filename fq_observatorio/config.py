from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="FQ_", extra="ignore")

    env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./franquestions.db"
    api_url: str = "http://localhost:8000"
    access_tier: str = "owner"
    preferences_path: str = "./fq_preferences.json"
    bccr_name: str = ""
    bccr_email: str = ""
    bccr_token: str = ""
    bccr_base_url: str = (
        "https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/"
        "wsindicadoreseconomicos.asmx/ObtenerIndicadoresEconomicosXML"
    )
    inec_data_url: str = ""
    http_timeout_seconds: float = 30.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
