from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from api.bootstrap import bootstrap
from api.common.exceptions import DomainError
from api.common.handlers import domain_error_handler
from api.common.logging import configure_logging

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup: bootstrapping dependencies...")
    bootstrap()
    yield
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Puls-Events RAG API",
    summary="Assistant conversationnel RAG pour les événements culturels en Île-de-France.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_exception_handler(DomainError, domain_error_handler)  # pyright: ignore[reportArgumentType]
