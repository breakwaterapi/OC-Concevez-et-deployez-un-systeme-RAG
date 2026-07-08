from typing import Annotated

from fastapi import APIRouter, Depends, Query

from api.bootstrap import get_documents_use_case
from api.modules.documents.schemas import ListDocumentsParams, RetrieveParams, SourceSchema
from api.modules.documents.use_cases import DocumentsUseCase

router = APIRouter(tags=["documents"])

DocumentsUseCaseDep = Annotated[DocumentsUseCase, Depends(get_documents_use_case)]


@router.get(
    "/documents",
    response_model=list[SourceSchema],
    summary="Lister les documents indexés (paginé)",
)
def list_documents(
    use_case: DocumentsUseCaseDep,
    params: Annotated[ListDocumentsParams, Query()],
) -> list[SourceSchema]:
    """Renvoie une page de documents parents (un par événement) tels qu'indexés, sans recherche
    sémantique — utile pour parcourir le corpus."""
    docs = use_case.list_documents()
    return [
        SourceSchema(uid=d.uid, text=d.text)
        for d in docs[params.offset : params.offset + params.limit]
    ]


@router.get(
    "/documents/{uid}",
    response_model=SourceSchema,
    summary="Récupérer un document par son identifiant",
    responses={404: {"description": "Aucun document ne correspond à cet identifiant."}},
)
def get_document(uid: str, use_case: DocumentsUseCaseDep) -> SourceSchema:
    doc = use_case.get_document(uid)
    return SourceSchema(uid=doc.uid, text=doc.text)


@router.get(
    "/retrieve",
    response_model=list[SourceSchema],
    summary="Recherche sémantique brute (sans génération)",
    responses={503: {"description": "Index Faiss non construit — appeler POST /rebuild d'abord."}},
)
def retrieve(
    use_case: DocumentsUseCaseDep,
    params: Annotated[RetrieveParams, Query()],
) -> list[SourceSchema]:
    """Renvoie les `k` documents parents les plus proches de la requête `q`, sans passer par le
    LLM — utile pour inspecter ce que `/ask` utiliserait comme contexte."""
    docs = use_case.retrieve(params.q, k=params.k)
    return [SourceSchema(uid=d.uid, text=d.text) for d in docs]
