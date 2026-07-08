from dataclasses import dataclass

from api.modules.metadata.ports import IndexInfoPort


@dataclass(frozen=True)
class IndexMetadata:
    region: str
    date_from: str
    date_to: str
    n_events: int
    n_chunks: int
    embed_model: str
    chat_model: str


@dataclass
class MetadataUseCases:
    index_info: IndexInfoPort
    region: str
    date_from: str
    date_to: str
    embed_model: str
    chat_model: str

    def get(self) -> IndexMetadata:
        return IndexMetadata(
            region=self.region,
            date_from=self.date_from,
            date_to=self.date_to,
            n_events=self.index_info.n_parent_docs,
            n_chunks=self.index_info.n_vectors,
            embed_model=self.embed_model,
            chat_model=self.chat_model,
        )
