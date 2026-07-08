from api.common.exceptions import DomainError


class DocumentNotFoundError(DomainError):
    status_code = 404

    def __init__(self, uid: str) -> None:
        self.uid = uid
        super().__init__(f"Document '{uid}' not found.")
