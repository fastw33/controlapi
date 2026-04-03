# app/core/config.py
from typing import Tuple

# Compatibilidad Pydantic v2 / v1
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict  # v2
    V2 = True
except Exception:  # v1 fallback
    from pydantic import BaseSettings  # type: ignore
    SettingsConfigDict = None
    V2 = False


class Settings(BaseSettings):
    # === Ajustes de archivos de justificación (NO biometría) ===
    storage_dir: str = "upload/justificaciones"
    max_upload_mb: int = 10
    allowed_mime: Tuple[str, ...] = (
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
    )

    # === Variables de tu .env ===
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "control_ingresos"
    db_user: str = "root"
    db_password: str = ""
    db_charset: str = "utf8mb4"
    time_zone: str = "-05:00"
    nixpacks_python_version: str = "3.11"

    # === Config de Pydantic Settings ===
    if V2:
        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            extra="ignore",   # ignora variables extra
        )
    else:
        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            extra = "ignore"


settings = Settings()
