from unittest.mock import MagicMock

import pytest

from api.common.domain.entities import ParentDocument
from api.modules.data.entities import Chunk, Event
from api.modules.data.use_cases import (
    BuildIndexUseCase,
    PrepareDataUseCase,
    _build_date_display,
    _raw_to_events,
)


def _raw(**kwargs):
    base = {
        "uid": "uid-001",
        "title_fr": "Exposition",
        "description_fr": "Une belle exposition.",
        "longdescription_fr": None,
        "keywords_fr": ["art", "culture"],
        "conditions_fr": None,
        "firstdate_begin": "2025-07-01T10:00:00Z",
        "lastdate_begin": "2025-07-31T20:00:00Z",
        "location_name": "Musée d'Art",
        "location_address": "1 rue de la Paix",
        "location_city": "Paris",
        "location_department": "75",
        "location_region": "Île-de-France",
    }
    return {**base, **kwargs}


def _event(**kwargs):
    base = {
        "uid": "ev-001",
        "title": "Concert",
        "description_clean": "Un beau concert.",
        "keywords": ["musique"],
        "conditions": None,
        "date_display": "Le 1 juillet 2025 à 20:00",
        "firstdate_begin": None,
        "lastdate_begin": None,
        "location_name": "Salle Pleyel",
        "location_address": "252 rue du Faubourg Saint-Honoré",
        "location_city": "Paris",
        "location_department": "75",
        "location_region": "Île-de-France",
    }
    return Event(**{**base, **kwargs})


@pytest.fixture
def mock_cleaner():
    mock = MagicMock()
    mock.html_to_text.return_value = ""
    return mock


# --- _raw_to_events ---


def test_raw_to_events_basic(mock_cleaner):
    events = _raw_to_events([_raw()], mock_cleaner)

    assert len(events) == 1
    assert events[0].uid == "uid-001"
    assert events[0].title == "Exposition"
    assert events[0].description_clean == "Une belle exposition."


def test_raw_to_events_deduplication(mock_cleaner):
    events = _raw_to_events([_raw(), _raw()], mock_cleaner)

    assert len(events) == 1


def test_raw_to_events_filters_no_description(mock_cleaner):
    events = _raw_to_events([_raw(description_fr="", longdescription_fr=None)], mock_cleaner)

    assert len(events) == 0


def test_raw_to_events_filters_no_uid(mock_cleaner):
    events = _raw_to_events([_raw(uid="")], mock_cleaner)

    assert len(events) == 0


def test_raw_to_events_long_description_preferred(mock_cleaner):
    mock_cleaner.html_to_text.return_value = "Description longue nettoyée."

    events = _raw_to_events([_raw(longdescription_fr="<p>Long</p>")], mock_cleaner)

    assert events[0].description_clean == "Description longue nettoyée."


def test_raw_to_events_keywords_list(mock_cleaner):
    events = _raw_to_events([_raw(keywords_fr=["jazz", "live"])], mock_cleaner)

    assert events[0].keywords == ["jazz", "live"]


def test_raw_to_events_keywords_non_list(mock_cleaner):
    events = _raw_to_events([_raw(keywords_fr=None)], mock_cleaner)

    assert events[0].keywords == []


def test_raw_to_events_skips_record_when_cleaner_raises(mock_cleaner):
    mock_cleaner.html_to_text.side_effect = [RuntimeError("bad html"), ""]

    events = _raw_to_events(
        [_raw(uid="bad-record"), _raw(uid="good-record")],
        mock_cleaner,
    )

    assert len(events) == 1
    assert events[0].uid == "good-record"


# --- _build_date_display ---


def test_build_date_display_same_day():
    display = _build_date_display(
        {"firstdate_begin": "2025-07-01T10:00:00Z", "lastdate_begin": "2025-07-01T20:00:00Z"}
    )

    assert display == "Le 1 juillet 2025 à 10:00"


def test_build_date_display_date_range():
    display = _build_date_display(
        {"firstdate_begin": "2025-07-01T10:00:00Z", "lastdate_begin": "2025-07-31T20:00:00Z"}
    )

    assert display == "Du 1 juillet 2025 à 10:00 au 31 juillet 2025 à 20:00"


def test_build_date_display_missing_lastdate_uses_first_only():
    display = _build_date_display({"firstdate_begin": "2025-09-20T12:30:00Z"})

    assert display == "Le 20 septembre 2025 à 12:30"


def test_build_date_display_missing_firstdate_returns_empty():
    assert _build_date_display({"lastdate_begin": "2025-07-01T10:00:00Z"}) == ""
    assert _build_date_display({}) == ""


def test_build_date_display_malformed_firstdate_returns_empty():
    assert _build_date_display({"firstdate_begin": "not-a-date"}) == ""


def test_build_date_display_malformed_lastdate_falls_back_to_first():
    display = _build_date_display(
        {"firstdate_begin": "2025-09-20T12:30:00Z", "lastdate_begin": "not-a-date"}
    )

    assert display == "Le 20 septembre 2025 à 12:30"


# --- PrepareDataUseCase ---


def test_prepare_execute_calls_fetcher(mock_cleaner):
    mock_fetcher = MagicMock()
    mock_fetcher.fetch_events.return_value = [_raw()]

    use_case = PrepareDataUseCase(
        fetcher=mock_fetcher,
        cleaner=mock_cleaner,
        where_clause="location_region = 'IDF'",
        max_records=100,
    )

    events = use_case.execute()

    mock_fetcher.fetch_events.assert_called_once_with("location_region = 'IDF'", max_records=100)
    assert len(events) == 1


# --- BuildIndexUseCase ---


def test_build_index_execute():
    event = _event()
    chunks = [
        Chunk(uid="ev-001", chunk_id=0, text="Chunk 1", n_tokens=5, metadata={"uid": "ev-001"})
    ]
    parent_docs = [ParentDocument(uid="ev-001", text="Full text")]
    embeddings = [[0.1, 0.2, 0.3]]

    mock_chunker = MagicMock()
    mock_chunker.chunk_events.return_value = (chunks, parent_docs)

    mock_embedder = MagicMock()
    mock_embedder.embed_texts.return_value = embeddings

    mock_builder = MagicMock()

    use_case = BuildIndexUseCase(
        chunker=mock_chunker,
        embedder=mock_embedder,
        index_builder=mock_builder,
        index_path="/tmp/test_index",
    )

    n_chunks, n_parents = use_case.execute([event])

    assert n_chunks == 1
    assert n_parents == 1
    mock_chunker.chunk_events.assert_called_once_with([event])
    mock_embedder.embed_texts.assert_called_once_with(["Chunk 1"])
    mock_builder.build_and_save.assert_called_once_with(
        chunks, parent_docs, embeddings, "/tmp/test_index"
    )


def test_build_index_execute_raises_on_zero_events():
    use_case = BuildIndexUseCase(
        chunker=MagicMock(),
        embedder=MagicMock(),
        index_builder=MagicMock(),
        index_path="/tmp/test_index",
    )

    with pytest.raises(ValueError, match="No events to index"):
        use_case.execute([])
