from typing import Protocol


class IndexInfoPort(Protocol):
    @property
    def n_vectors(self) -> int: ...
    @property
    def n_parent_docs(self) -> int: ...
