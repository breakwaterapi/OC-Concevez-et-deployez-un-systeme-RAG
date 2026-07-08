from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Event:
    uid: str
    title: str
    description_clean: str
    keywords: list[str]
    conditions: str | None
    date_display: str
    firstdate_begin: datetime | None
    lastdate_begin: datetime | None
    location_name: str
    location_address: str
    location_city: str
    location_department: str | None
    location_region: str


@dataclass(frozen=True)
class Chunk:
    uid: str
    chunk_id: int
    text: str
    n_tokens: int
    metadata: dict[str, str | None] = field(default_factory=dict)
