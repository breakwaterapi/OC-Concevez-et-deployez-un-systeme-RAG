from typing import Protocol

from api.common.domain.entities import ParentDocument
from api.modules.data.entities import Chunk, Event


class EventFetcherPort(Protocol):
    def fetch_events(self, where_clause: str, max_records: int = 1_000) -> list[dict]: ...


class TextCleanerPort(Protocol):
    def html_to_text(self, html: str | None) -> str: ...


class ChunkerPort(Protocol):
    def chunk_events(self, events: list[Event]) -> tuple[list[Chunk], list[ParentDocument]]: ...


class EmbedderPort(Protocol):
    def embed_texts(self, texts: list[str]) -> list[list[float]]: ...


class IndexBuilderPort(Protocol):
    def build_and_save(
        self,
        chunks: list[Chunk],
        parent_docs: list[ParentDocument],
        embeddings: list[list[float]],
        path: str,
    ) -> None: ...
