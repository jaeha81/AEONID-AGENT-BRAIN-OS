from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    anthropic_api_key: str
    database_url: str = "sqlite:///./aeonid.db"
    obsidian_vault_path: str = str(Path(__file__).parent.parent / "EONID-BRAIN")
    upload_dir: str = str(Path(__file__).parent / "uploads")

    class Config:
        env_file = ".env"

settings = Settings()
