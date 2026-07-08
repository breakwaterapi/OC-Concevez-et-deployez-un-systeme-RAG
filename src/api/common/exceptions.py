class DomainError(Exception):
    """Base for domain errors raised by use cases. Subclasses set `status_code`; a single
    handler (see handlers.py) maps any DomainError to the right HTTP response — no per-exception
    handler/registration needed."""

    status_code: int = 400


class IndexNotReadyError(DomainError):
    status_code = 503

    def __init__(self) -> None:
        super().__init__("FAISS index not built yet — call /rebuild first.")
