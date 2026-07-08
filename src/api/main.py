from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from api.bootstrap import bootstrap, get_faiss_client
from api.common.exceptions import DomainError
from api.common.handlers import domain_error_handler
from api.common.logging import configure_logging
from api.modules.data.router import router as data_router
from api.modules.documents.router import router as documents_router
from api.modules.health.router import router as health_router
from api.modules.metadata.router import router as metadata_router
from api.modules.rag.router import router as rag_router

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: bootstrapping dependencies...")
    bootstrap()
    client = get_faiss_client()
    if client.is_ready:
        logger.success(
            f"FAISS index loaded: {client.n_vectors} vectors, {client.n_parent_docs} parent docs"
        )
    else:
        logger.warning("No FAISS index found — /ask will fail until /rebuild is called")
    yield
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Puls-Events RAG API",
    summary="Assistant conversationnel RAG pour les événements culturels en Île-de-France.",
    description=(
        "Recherche vectorielle (Faiss) sur des descriptions d'événements Open Agenda, combinée à "
        "une génération de réponse en langage naturel (Mistral) pour répondre à des questions sur "
        "les événements culturels à venir en Île-de-France.\n\n"
        "Avant d'utiliser `/ask`, vérifiez `GET /health` (`store_ready: true`) — si l'index n'est "
        "pas encore construit, appelez `POST /rebuild`. `GET /metadata` donne le détail du corpus "
        "actuellement indexé (région, période, tailles, modèles)."
    ),
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "rag",
            "description": "Poser une question et obtenir une réponse générée à partir des "
            "événements indexés.",
        },
        {
            "name": "data",
            "description": "Construction/reconstruction de l'index vectoriel à partir d'Open "
            "Agenda.",
        },
        {
            "name": "documents",
            "description": "Consultation directe des documents indexés, sans génération.",
        },
        {
            "name": "health",
            "description": "État de santé de l'API et de ses dépendances (Faiss, Mistral).",
        },
        {
            "name": "metadata",
            "description": "Métadonnées du corpus actuellement indexé (région, dates, tailles, "
            "modèles).",
        },
    ],
)

app.add_exception_handler(DomainError, domain_error_handler)  # pyright: ignore[reportArgumentType]

app.include_router(health_router)
app.include_router(metadata_router)
app.include_router(rag_router)
app.include_router(documents_router)
app.include_router(data_router)
