from dataclasses import dataclass, field

from api.common.domain.entities import ParentDocument


@dataclass(frozen=True)
class RAGResponse:
    question: str
    answer: str
    sources: list[ParentDocument] = field(default_factory=list)
