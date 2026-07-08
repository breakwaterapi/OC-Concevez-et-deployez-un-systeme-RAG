from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from api.bootstrap import bootstrap, get_faiss_client
from api.common.exceptions import DomainError
from api.common.handlers import domain_error_handler
from api.common.logging import configure_logging
from api.modules.data.router import router as data_router
from api.modules.health.router import router as health_router
from api.modules.metadata.router import router as metadata_router

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
    version="0.1.0",
    lifespan=lifespan,
)

app.add_exception_handler(DomainError, domain_error_handler)  # pyright: ignore[reportArgumentType]

app.include_router(health_router)
app.include_router(metadata_router)
app.include_router(data_router)
