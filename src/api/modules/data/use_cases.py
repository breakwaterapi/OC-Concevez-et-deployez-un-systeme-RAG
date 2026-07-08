from dataclasses import dataclass
from datetime import datetime

from loguru import logger
import pandas as pd

from api.modules.data.entities import Event
from api.modules.data.ports import (
    ChunkerPort,
    EmbedderPort,
    EventFetcherPort,
    IndexBuilderPort,
    TextCleanerPort,
)

MONTHS_FR = {
    1: "janvier",
    2: "février",
    3: "mars",
    4: "avril",
    5: "mai",
    6: "juin",
    7: "juillet",
    8: "août",
    9: "septembre",
    10: "octobre",
    11: "novembre",
    12: "décembre",
}


def _build_date_display(row: dict) -> str:
    def fmt(dt):
        return f"{dt.day} {MONTHS_FR[dt.month]} {dt.year} à {dt.strftime('%H:%M')}"

    first_raw = row.get("firstdate_begin")
    if not first_raw:
        return ""
    try:
        first = pd.to_datetime(first_raw, utc=True)
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse firstdate_begin={first_raw!r}: {e}")
        return ""

    last_raw = row.get("lastdate_begin")
    if not last_raw:
        return f"Le {fmt(first)}"
    try:
        last = pd.to_datetime(last_raw, utc=True)
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse lastdate_begin={last_raw!r}: {e}")
        return f"Le {fmt(first)}"

    if first.date() == last.date():
        return f"Le {fmt(first)}"
    return f"Du {fmt(first)} au {fmt(last)}"


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    try:
        return pd.to_datetime(value, utc=True).to_pydatetime()
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse date {value!r}: {e}")
        return None


def _raw_to_events(records: list[dict], cleaner: TextCleanerPort) -> list[Event]:
    seen_uids: set[str] = set()
    events: list[Event] = []

    for raw in records:
        uid = str(raw.get("uid", "")).strip()
        if not uid or uid in seen_uids:
            continue
        seen_uids.add(uid)

        try:
            long_desc = cleaner.html_to_text(raw.get("longdescription_fr"))
        except Exception as e:
            logger.warning(f"Skipping record uid={uid}: html_to_text failed: {e}")
            continue
        short_desc = str(raw.get("description_fr") or "").strip()
        description = long_desc if long_desc else short_desc
        if not description:
            continue

        keywords_raw = raw.get("keywords_fr")
        keywords = keywords_raw if isinstance(keywords_raw, list) else []

        events.append(
            Event(
                uid=uid,
                title=str(raw.get("title_fr") or "").strip(),
                description_clean=description,
                keywords=keywords,
                conditions=raw.get("conditions_fr"),
                date_display=_build_date_display(raw),
                firstdate_begin=_parse_dt(raw.get("firstdate_begin")),
                lastdate_begin=_parse_dt(raw.get("lastdate_begin")),
                location_name=str(raw.get("location_name") or "").strip(),
                location_address=str(raw.get("location_address") or "").strip(),
                location_city=str(raw.get("location_city") or "").strip(),
                location_department=raw.get("location_department"),
                location_region=str(raw.get("location_region") or "").strip(),
            )
        )

    logger.info(
        f"Converted {len(records)} raw records → {len(events)} events (deduped + filtered)"
    )
    return events


@dataclass
class PrepareDataUseCase:
    fetcher: EventFetcherPort
    cleaner: TextCleanerPort
    where_clause: str
    max_records: int = 1_000

    def execute(self) -> list[Event]:
        raw = self.fetcher.fetch_events(self.where_clause, max_records=self.max_records)
        return _raw_to_events(raw, self.cleaner)


@dataclass
class BuildIndexUseCase:
    chunker: ChunkerPort
    embedder: EmbedderPort
    index_builder: IndexBuilderPort
    index_path: str

    def execute(self, events: list[Event]) -> tuple[int, int]:
        if not events:
            raise ValueError(
                "No events to index — check the fetch date range/region/where_clause."
            )

        chunks, parent_docs = self.chunker.chunk_events(events)
        logger.info(f"Embedding {len(chunks)} chunks...")
        embeddings = self.embedder.embed_texts([c.text for c in chunks])
        logger.info("Building Faiss index...")
        self.index_builder.build_and_save(chunks, parent_docs, embeddings, self.index_path)
        return len(chunks), len(parent_docs)


@dataclass
class DataUseCases:
    prepare: PrepareDataUseCase
    build_index: BuildIndexUseCase
