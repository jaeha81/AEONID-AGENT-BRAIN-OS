from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DEFAULT_DATABASE_URL = f"sqlite:///{(ROOT_DIR / 'aeonid.db').as_posix()}"


class Settings(BaseSettings):
    gemini_api_key: str = ""
    database_url: str = DEFAULT_DATABASE_URL
    obsidian_vault_path: str = str(ROOT_DIR / "EONID-BRAIN")
    upload_dir: str = str(BASE_DIR / "uploads")

    model_config = SettingsConfigDict(
        env_file=(
            ROOT_DIR / ".env",
            ROOT_DIR / ".env.local",
            BASE_DIR / ".env",
            BASE_DIR / ".env.local",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
