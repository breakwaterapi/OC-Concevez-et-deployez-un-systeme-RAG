from unittest.mock import MagicMock

from api.infra.openagenda import client as client_module
from api.infra.openagenda.client import OpenAgendaClient


def _response(results: list[dict], total_count: int) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"results": results, "total_count": total_count}
    return resp


# --- build_where_clause ---


def test_build_where_clause():
    clause = OpenAgendaClient.build_where_clause(
        region="Île-de-France",
        date_from="2025-06-01T00:00:00Z",
        date_to="2026-06-01T00:00:00Z",
    )

    assert 'location_region = "Île-de-France"' in clause
    assert 'firstdate_begin >= "2025-06-01T00:00:00Z"' in clause
    assert 'lastdate_begin <= "2026-06-01T00:00:00Z"' in clause


# --- fetch_events ---


def test_fetch_events_single_page(monkeypatch):
    events = [{"uid": "1"}, {"uid": "2"}]
    get = MagicMock(return_value=_response(events, total_count=2))
    monkeypatch.setattr(client_module.requests, "get", get)
    monkeypatch.setattr(client_module.time, "sleep", MagicMock())

    result = OpenAgendaClient(base_url="https://example.test").fetch_events(
        where_clause="region=x", max_records=200
    )

    assert result == events
    get.assert_called_once()


def test_fetch_events_paginates_across_multiple_pages(monkeypatch):
    page_1 = [{"uid": "1"}, {"uid": "2"}]
    page_2 = [{"uid": "3"}]
    get = MagicMock(
        side_effect=[
            _response(page_1, total_count=3),
            _response(page_2, total_count=3),
        ]
    )
    monkeypatch.setattr(client_module.requests, "get", get)
    monkeypatch.setattr(client_module.time, "sleep", MagicMock())

    result = OpenAgendaClient(base_url="https://example.test", page_size=2).fetch_events(
        where_clause="region=x", max_records=200
    )

    assert result == page_1 + page_2
    assert get.call_count == 2
    second_call_params = get.call_args_list[1].kwargs["params"]
    assert second_call_params["offset"] == 2


def test_fetch_events_stops_once_max_records_reached(monkeypatch):
    page_1 = [{"uid": "1"}, {"uid": "2"}]
    page_2 = [{"uid": "3"}, {"uid": "4"}]
    get = MagicMock(
        side_effect=[
            _response(page_1, total_count=10),
            _response(page_2, total_count=10),
        ]
    )
    monkeypatch.setattr(client_module.requests, "get", get)
    monkeypatch.setattr(client_module.time, "sleep", MagicMock())

    result = OpenAgendaClient(base_url="https://example.test", page_size=2).fetch_events(
        where_clause="region=x", max_records=3
    )

    assert result == page_1 + page_2
    assert get.call_count == 2


def test_fetch_events_stops_on_empty_batch(monkeypatch):
    get = MagicMock(return_value=_response([], total_count=0))
    monkeypatch.setattr(client_module.requests, "get", get)
    monkeypatch.setattr(client_module.time, "sleep", MagicMock())

    result = OpenAgendaClient(base_url="https://example.test").fetch_events(
        where_clause="region=x", max_records=200
    )

    assert result == []
    get.assert_called_once()
