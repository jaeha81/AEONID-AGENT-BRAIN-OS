from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    gemini_api_key: str
    database_url: str = "sqlite:///./aeonid.db"
    obsidian_vault_path: str = str(Path(__file__).parent.parent / "EONID-BRAIN")
    upload_dir: str = str(Path(__file__).parent / "uploads")

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
