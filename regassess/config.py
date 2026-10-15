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
    # Synthetic internal policy corpus and its planted-gap ground truth (committed).
    internal_dir: Path = PROJECT_ROOT / "data" / "internal"
    # Generated gap registers.
    output_dir: Path = PROJECT_ROOT / "data" / "output"
    # On-disk cache of successful LLM responses.
    cache_dir: Path = PROJECT_ROOT / "data" / "cache"

    # No default: a missing key fails loudly at import instead of at the first API call.
    gemini_api_key: str
    gemini_model: str = "gemini-3.8-flash"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    # bge's instruction for queries. Prepended to queries only, never to passages.
    # Set QUERY_PREFIX= (empty) in .env to switch it off for an A/B run. Changing it
    # invalidates every recorded eval run, so run files store it.
    query_prefix: str = "Represent this sentence for searching relevant passages: "
    # Embed each nested-clause chunk with its parent's heading prepended (the `context`
    # field). OFF by default: measured on the naive baseline it cost 3 points of
    # recall@10. Turning it on needs build_index.py and a fresh baseline run.
    parent_context: bool = False
    # Hybrid retrieval. rrf_k=60 is the literature default and is NOT tuned against the
    # gold set. Each list (vector, BM25) is cut to rrf_candidates before fusion, so the
    # fused ranking does not depend on the harness's --depth.
    rrf_k: int = 60
    rrf_candidates: int = 50

    # Postgres + pgvector. Defaults match docker-compose.yml; the password has no
    # default so credentials only ever come from .env.
    postgres_user: str = "regassess"
    postgres_password: str
    postgres_db: str = "regassess"
    postgres_host: str = "localhost"
    postgres_port: int = 5433

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()

for _dir in (settings.data_dir, settings.raw_dir, settings.processed_dir, settings.output_dir, settings.cache_dir):
    _dir.mkdir(parents=True, exist_ok=True)
