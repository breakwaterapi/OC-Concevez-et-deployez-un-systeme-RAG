from datetime import datetime, timedelta
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # API Keys
    mistral_api_key: str = ""
    rebuild_api_key: str = ""

    # OpenAgenda
    openagenda_base_url: str = (
        "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets"
        "/evenements-publics-openagenda/records"
    )
    openagenda_region: str = "Île-de-France"
    reference_date: str = "2026-06-01"

    # Mistral models
    mistral_embed_model: str = "mistral-embed"
    mistral_chat_model: str = "mistral-small-latest"
    mistral_temperature: float = 0.3

    # Chunking
    chunk_max_tokens: int = 256
    chunk_overlap_tokens: int = 20

    # OpenAgenda fetch limit
    openagenda_max_records: int = 500

    # Retrieval
    retrieval_k: int = 5

    # Paths
    project_root: Path = Path(__file__).resolve().parents[3]
    data_raw_dir: Path = project_root / "data/raw"
    data_processed_dir: Path = project_root / "data/processed"
    data_interim_dir: Path = project_root / "data/interim"
    faiss_index_path: Path = project_root / "models/faiss_index"

    @property
    def src_path(self) -> Path:
        return self.project_root / "src"

    @property
    def date_from(self) -> str:
        ref = datetime.strptime(self.reference_date, "%Y-%m-%d")
        return (ref - timedelta(days=365)).strftime("%Y-%m-%dT00:00:00Z")

    @property
    def date_to(self) -> str:
        ref = datetime.strptime(self.reference_date, "%Y-%m-%d")
        return (ref + timedelta(days=365)).strftime("%Y-%m-%dT00:00:00Z")


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
    return _settings
