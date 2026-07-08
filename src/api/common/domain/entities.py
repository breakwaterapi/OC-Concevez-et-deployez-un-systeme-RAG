from dataclasses import dataclass


@dataclass(frozen=True)
class ParentDocument:
    uid: str
    text: str
