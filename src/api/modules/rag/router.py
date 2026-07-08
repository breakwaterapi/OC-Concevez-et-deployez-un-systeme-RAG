from typing import Annotated

from fastapi import APIRouter, Depends

from api.bootstrap import get_rag_use_case
from api.modules.rag.schemas import AskRequest, AskResponse, SourceRefSchema
from api.modules.rag.use_cases import AskQuestionUseCase

router = APIRouter(tags=["rag"])

RagUseCasesDep = Annotated[AskQuestionUseCase, Depends(get_rag_use_case)]


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Poser une question sur les événements indexés",
    responses={
        400: {"description": "Question vide ou composée uniquement d'espaces."},
        503: {"description": "Index Faiss non construit — appeler POST /rebuild d'abord."},
    },
)
def ask(body: AskRequest, use_case: RagUseCasesDep) -> AskResponse:
    """Recherche les événements les plus pertinents (top-k) puis génère une réponse en langage
    naturel avec leurs identifiants comme sources."""
    result = use_case.execute(question=body.question)
    return AskResponse(
        question=result.question,
        answer=result.answer,
        sources=[SourceRefSchema(uid=s.uid) for s in result.sources],
    )
