from dataclasses import dataclass

from loguru import logger

from api.common.domain.entities import ParentDocument
from api.infra.faiss.store import FAISSClient
from api.infra.preprocessing.chunker import TextChunker
from api.modules.data.entities import Chunk, Event
from api.modules.data.ports import ChunkerPort, IndexBuilderPort


def _build_parent_text(event: Event) -> str:
    parts = [f"# {event.title}"]
    parts.append(f"\n**Date** : {event.date_display}")
    parts.append(f"**Lieu** : {event.location_name}, {event.location_city}")
    if event.location_address:
        parts.append(f"**Adresse** : {event.location_address}")
    if event.keywords:
        parts.append(f"**Mots-clés** : {', '.join(event.keywords)}")
    if event.conditions:
        parts.append(f"**Conditions** : {event.conditions}")
    parts.append(f"\n{event.description_clean}")
    return "\n".join(parts)


def _build_chunk_header(event: Event) -> str:
    header = f"Titre : {event.title}"
    if event.keywords:
        header += f"\nMots-clés : {', '.join(event.keywords)}"
    return header


@dataclass
class LangChainChunkerAdapter(ChunkerPort):
    text_chunker: TextChunker

    def chunk_events(self, events: list[Event]) -> tuple[list[Chunk], list[ParentDocument]]:
        all_chunks: list[Chunk] = []
        parent_docs: list[ParentDocument] = []

        for event in events:
            parent_docs.append(ParentDocument(uid=event.uid, text=_build_parent_text(event)))

            header = _build_chunk_header(event)
            header_tokens = self.text_chunker.count_tokens(f"{header}\n\n")
            description = event.description_clean.strip() or event.title
            fragments = self.text_chunker.split_text(description, reserved_tokens=header_tokens)

            for i, fragment in enumerate(fragments):
                chunk_text = f"{header}\n\n{fragment}"
                n_tokens = self.text_chunker.count_tokens(chunk_text)
                metadata: dict[str, str | None] = {
                    "uid": event.uid,
                    "chunk_id": str(i),
                    "title": event.title,
                    "date_display": event.date_display,
                    "location_name": event.location_name,
                    "location_city": event.location_city,
                    "location_address": event.location_address or None,
                    "location_region": event.location_region,
                    "keywords": ", ".join(event.keywords) if event.keywords else None,
                }
                all_chunks.append(
                    Chunk(
                        uid=event.uid,
                        chunk_id=i,
                        text=chunk_text,
                        n_tokens=n_tokens,
                        metadata=metadata,
                    )
                )

        logger.info(
            f"Chunked {len(events)} events → {len(all_chunks)} chunks, "
            f"{len(parent_docs)} parent docs"
        )
        return all_chunks, parent_docs


@dataclass
class FAISSIndexBuilderAdapter(IndexBuilderPort):
    faiss_client: FAISSClient

    def build_and_save(
        self,
        chunks: list[Chunk],
        parent_docs: list[ParentDocument],
        embeddings: list[list[float]],
        path: str,
    ) -> None:
        texts = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]
        parent_data = {doc.uid: doc.text for doc in parent_docs}

        self.faiss_client.build(texts, embeddings, metadatas, parent_data)
        self.faiss_client.save(path)
