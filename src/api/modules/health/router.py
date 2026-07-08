from typing import Annotated

from fastapi import APIRouter, Depends

from api.bootstrap import get_health_use_cases
from api.modules.health.schemas import HealthResponse
from api.modules.health.use_cases import HealthUseCases

router = APIRouter(tags=["health"])

HealthUseCasesDep = Annotated[HealthUseCases, Depends(get_health_use_cases)]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="État de santé de l'API et de ses dépendances",
)
def health(use_cases: HealthUseCasesDep) -> HealthResponse:
    """Toujours 200 — le statut dégradé (`store_ready`/`model_ready` à `false`) se lit dans le
    corps de la réponse plutôt que via le code HTTP, pour distinguer "API up mais index absent"
    d'une vraie panne."""
    result = use_cases.check()
    return HealthResponse(
        status=result.status,
        store_ready=result.store_ready,
        model_ready=result.model_ready,
        index_size=result.index_size,
    )
