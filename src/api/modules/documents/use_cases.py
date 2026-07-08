from dataclasses import dataclass

from api.common.domain.entities import ParentDocument
from api.common.exceptions import IndexNotReadyError
from api.modules.documents.exceptions import DocumentNotFoundError
from api.modules.documents.ports import DocumentStorePort


@dataclass
class DocumentsUseCase:
    store: DocumentStorePort
    default_k: int = 5

    def list_documents(self) -> list[ParentDocument]:
        return [ParentDocument(uid=uid, text=text) for uid, text in self.store.list_parent_docs()]

    def get_document(self, uid: str) -> ParentDocument:
        text = self.store.get_parent_doc(uid)
        if text is None:
            raise DocumentNotFoundError(uid)
        return ParentDocument(uid=uid, text=text)

    def retrieve(self, query: str, k: int | None = None) -> list[ParentDocument]:
        if not self.store.is_ready:
            raise IndexNotReadyError()

        return [
            ParentDocument(uid=uid, text=text)
            for uid, text in self.store.search_parent_docs(query, k=k or self.default_k)
        ]
