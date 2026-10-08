from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Derived from this file's location, so it works from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Reading .env via an absolute path means scripts work regardless of cwd.
    # extra="ignore" lets later phases add .env keys without breaking earlier code.
    model_config = SettingsConfigDict(env_file=PROJECT_ROOT / ".env", extra="ignore")

    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    raw_dir: Path = PROJECT_ROOT / "data" / "raw"
    processed_dir: Path = PROJECT_ROOT / "data" / "processed"

    # No default: a missing key fails loudly at import instead of at the first API call.
    gemini_api_key: str
    gemini_model: str = "gemini-3.8-flash"
    embedding_model: str = "BAAI/bge-small-en-v1.5"


settings = Settings()

for _dir in (settings.data_dir, settings.raw_dir, settings.processed_dir):
    _dir.mkdir(parents=True, exist_ok=True)
