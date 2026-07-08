import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = PROJECT_ROOT / "data/raw"
DATA_PROCESSED = PROJECT_ROOT / "data/processed"
DATA_INTERIM = PROJECT_ROOT / "data/interim"
FAISS_INDEX_PATH = PROJECT_ROOT / "models/faiss_index"

# Snapshot figé du corpus utilisé pour l'évaluation RAGAS (notebook 06), indépendant de
# `models/faiss_index` — qui, lui, sera reconstruit avec une couverture d'événements plus large
# (OPENAGENDA_MAX_RECORDS) pour la démo. Garder ce snapshot stable évite que les scores
# d'évaluation ne bougent au gré des reconstructions de l'index de production.
EVAL_DATA_DIR = PROJECT_ROOT / "data/evaluation"
EVAL_FAISS_INDEX_PATH = EVAL_DATA_DIR / "eval_faiss_index"

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_EMBED_MODEL = "mistral-embed"
MISTRAL_CHAT_MODEL = "mistral-small-latest"
MISTRAL_TEMPERATURE = 0.3

OPENAGENDA_BASE_URL = (
    "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets"
    "/evenements-publics-openagenda/records"
)
OPENAGENDA_REGION = "Île-de-France"
REFERENCE_DATE = "2026-06-07"
