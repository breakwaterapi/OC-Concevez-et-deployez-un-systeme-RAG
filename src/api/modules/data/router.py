from typing import Annotated

from fastapi import APIRouter, Depends
from mistralai.models import MistralError
import requests

from api.bootstrap import get_data_use_cases
from api.common.exceptions import UpstreamServiceError
from api.common.security import verify_rebuild_api_key
from api.modules.data.schemas import RebuildResponse
from api.modules.data.use_cases import DataUseCases

router = APIRouter(tags=["data"])

DataUseCasesDep = Annotated[DataUseCases, Depends(get_data_use_cases)]


@router.post(
    "/rebuild",
    response_model=RebuildResponse,
    dependencies=[Depends(verify_rebuild_api_key)],
    summary="Reconstruire l'index vectoriel depuis Open Agenda",
    responses={
        401: {"description": "Clé API manquante ou invalide (en-tête X-API-Key)."},
        503: {
            "description": (
                "Open Agenda ou Mistral a échoué pendant la reconstruction "
                "(en-tête Retry-After fourni)."
            )
        },
    },
)
def rebuild(use_cases: DataUseCasesDep) -> RebuildResponse:
    """Récupère les événements Open Agenda, les nettoie, les découpe en chunks, calcule leurs
    embeddings puis reconstruit et sauvegarde l'index Faiss. Opération protégée, coûteuse en
    appels Mistral — utilisée pour le seeding initial (voir `make up`) et pour rafraîchir le
    corpus avec de nouveaux événements."""
    try:
        events = use_cases.prepare.execute()
    except requests.RequestException as e:
        raise UpstreamServiceError("Open Agenda", str(e)) from e

    try:
        n_chunks, n_parents = use_cases.build_index.execute(events)
    except MistralError as e:
        raise UpstreamServiceError("Mistral", str(e)) from e

    return RebuildResponse(
        status="ok",
        n_chunks=n_chunks,
        n_parent_docs=n_parents,
        message=f"Index rebuilt: {n_chunks} chunks from {n_parents} events.",
    )
