from typing import Protocol


class StoreCheckerPort(Protocol):
    @property
    def is_ready(self) -> bool: ...
    @property
    def n_vectors(self) -> int: ...


class ModelCheckerPort(Protocol):
    def is_ready(self) -> bool: ...
