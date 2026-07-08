from api.common.exceptions import DomainError


class EmptyQuestionError(DomainError):
    status_code = 400

    def __init__(self) -> None:
        super().__init__("Question cannot be empty.")
