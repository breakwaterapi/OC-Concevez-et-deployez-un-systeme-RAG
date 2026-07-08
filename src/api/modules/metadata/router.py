from typing import Annotated

from fastapi import APIRouter, Depends

from api.bootstrap import get_metadata_use_cases
from api.modules.metadata.schemas import MetadataResponse
from api.modules.metadata.use_cases import MetadataUseCases

router = APIRouter(tags=["metadata"])

MetadataUseCasesDep = Annotated[MetadataUseCases, Depends(get_metadata_use_cases)]


@router.get(
    "/metadata",
    response_model=MetadataResponse,
    summary="Métadonnées du corpus actuellement indexé",
)
def metadata(use_cases: MetadataUseCasesDep) -> MetadataResponse:
    """Renvoie la région, la période couverte, la taille du corpus (événements/chunks) et les
    modèles Mistral utilisés pour l'index actuellement chargé — indépendant de l'état `is_ready`
    de l'index (voir `GET /health` pour ça)."""
    result = use_cases.get()
    return MetadataResponse(
        region=result.region,
        date_from=result.date_from,
        date_to=result.date_to,
        n_events=result.n_events,
        n_chunks=result.n_chunks,
        embed_model=result.embed_model,
        chat_model=result.chat_model,
    )
