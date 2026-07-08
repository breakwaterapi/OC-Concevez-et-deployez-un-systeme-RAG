from typing import Protocol


class VectorSearchPort(Protocol):
    @property
    def is_ready(self) -> bool: ...
    def search_parent_docs(self, query: str, k: int = 5) -> list[tuple[str, str]]: ...


class LLMPort(Protocol):
    def invoke(self, system_prompt: str, user_message: str) -> str: ...
