class DomainError(Exception):
    """Base for domain errors raised by use cases. Subclasses set `status_code`; a single
    handler (see handlers.py) maps any DomainError to the right HTTP response — no per-exception
    handler/registration needed."""

    status_code: int = 400
    retry_after: int | None = None


class IndexNotReadyError(DomainError):
    status_code = 503

    def __init__(self) -> None:
        super().__init__("FAISS index not built yet — call /rebuild first.")


class UpstreamServiceError(DomainError):
    """Raised when an external dependency (Open Agenda, Mistral) fails during /rebuild. 503
    rather than 502: we're not a gateway/proxy, just a service temporarily unable to complete
    the request because of an external dependency — and 503 is the code that carries
    `Retry-After`, which fits a transient failure the caller should retry."""

    status_code = 503
    retry_after = 60

    def __init__(self, service: str, reason: str) -> None:
        super().__init__(f"{service} request failed during index rebuild: {reason}")
