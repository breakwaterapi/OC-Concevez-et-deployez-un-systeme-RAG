from collections.abc import Callable
from dataclasses import dataclass, field
import json
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from loguru import logger


class _LangChainEmbeddingsAdapter(Embeddings):
    def __init__(self, embed_fn, query_fn):
        self._embed_fn = embed_fn
        self._query_fn = query_fn

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed_fn(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._query_fn(text)


@dataclass
class FAISSClient:
    embed_texts_fn: Callable[[list[str]], list[list[float]]]
    embed_query_fn: Callable[[str], list[float]]
    _lc_embeddings: _LangChainEmbeddingsAdapter = field(init=False, repr=False)
    _vectorstore: FAISS | None = field(init=False, default=None, repr=False)
    _parent_docs: dict[str, str] = field(init=False, default_factory=dict, repr=False)

    def __post_init__(self):
        self._lc_embeddings = _LangChainEmbeddingsAdapter(self.embed_texts_fn, self.embed_query_fn)

    @property
    def is_ready(self) -> bool:
        return self._vectorstore is not None

    @property
    def n_vectors(self) -> int:
        if self._vectorstore is None:
            return 0
        return self._vectorstore.index.ntotal

    @property
    def n_parent_docs(self) -> int:
        return len(self._parent_docs)

    def get_parent_doc(self, uid: str) -> str | None:
        return self._parent_docs.get(uid)

    def list_parent_docs(self) -> list[tuple[str, str]]:
        return list(self._parent_docs.items())

    def build(
        self,
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
        parent_docs: dict[str, str],
    ) -> None:
        text_embedding_pairs = list(zip(texts, embeddings))
        new_vs = FAISS.from_embeddings(
            text_embeddings=text_embedding_pairs,
            embedding=self._lc_embeddings,
            metadatas=metadatas,
        )
        self._vectorstore = new_vs
        self._parent_docs = parent_docs
        logger.info(
            f"FAISS index built: {self.n_vectors} vectors, {self.n_parent_docs} parent docs"
        )

    def search(self, query: str, k: int = 5) -> list[Document]:
        if self._vectorstore is None:
            raise RuntimeError("Index not loaded.")
        return self._vectorstore.similarity_search(query, k=k)

    def search_parent_docs(self, query: str, k: int = 5) -> list[tuple[str, str]]:
        """Search chunks, dedupe hits by parent uid, and resolve each to its parent doc text."""
        results = self.search(query, k=k)
        seen_uids: set[str] = set()
        parents: list[tuple[str, str]] = []
        for doc in results:
            uid = doc.metadata.get("uid")
            if uid and uid not in seen_uids:
                seen_uids.add(uid)
                text = self.get_parent_doc(uid)
                if text:
                    parents.append((uid, text))
        return parents

    def save(self, path: str) -> None:
        if self._vectorstore is None:
            raise RuntimeError("No index to save.")
        Path(path).mkdir(parents=True, exist_ok=True)
        self._vectorstore.save_local(path)
        (Path(path) / "parent_docs.json").write_text(
            json.dumps(self._parent_docs, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        logger.info(f"FAISS index saved to {path}")

    def load(self, path: str) -> None:
        if not (Path(path) / "index.faiss").exists():
            raise FileNotFoundError(f"No FAISS index at {path}")
        new_vs = FAISS.load_local(path, self._lc_embeddings, allow_dangerous_deserialization=True)
        parent_docs: dict[str, str] = {}
        parent_file = Path(path) / "parent_docs.json"
        if parent_file.exists():
            parent_docs = json.loads(parent_file.read_text(encoding="utf-8"))
        self._vectorstore = new_vs
        self._parent_docs = parent_docs
        logger.info(
            f"FAISS index loaded: {self.n_vectors} vectors, {self.n_parent_docs} parent docs"
        )
