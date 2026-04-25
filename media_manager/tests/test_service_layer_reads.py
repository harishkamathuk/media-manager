from __future__ import annotations

from dataclasses import dataclass

import pytest

import media_manager.app.service_layer.reads as reads_module
from media_manager.app.persistence.app_settings import AppSettingsService
from media_manager.app.service_layer.reads import ReadServices


@dataclass
class _FakeCache:
    invalidations: list[tuple[str, ...]]

    def get(self, _key: str):  # type: ignore[no-untyped-def]
        return None

    def set(self, _key: str, _payload, ttl_s: int) -> None:  # type: ignore[no-untyped-def]
        _ = ttl_s


def test_duplicate_bin_items_reuses_reclaim_archive_page(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeOperatorConsoleReadService:
        def __init__(self, _session_factory) -> None:
            pass

        def get_duplicate_reclaim_archive_page(self, *, page: int, limit: int):  # type: ignore[no-untyped-def]
            assert page == 2
            assert limit == 5
            return type("Page", (), {"to_dict": lambda self: {"page": 2, "limit": 5, "items": [{"item_status": "ARCHIVED"}]}})()

    monkeypatch.setattr(reads_module, "OperatorConsoleReadService", _FakeOperatorConsoleReadService)

    services = ReadServices(session_factory=object(), cache=_FakeCache(invalidations=[]))  # type: ignore[arg-type]

    payload = services.duplicate_bin_items(page=2, limit=5)

    assert payload["page"] == 2
    assert payload["limit"] == 5
    assert payload["items"][0]["item_status"] == "ARCHIVED"


def test_canonical_reuses_gallery_page_with_file_type(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeOperatorConsoleReadService:
        def __init__(self, _session_factory) -> None:
            pass

        def get_canonical_gallery(self, **kwargs):  # type: ignore[no-untyped-def]
            assert kwargs["page"] == 1
            assert kwargs["limit"] == 10
            assert kwargs["tags"] == ("travel",)
            assert kwargs["sort_by"] == "created_at"
            assert kwargs["sort_order"] == "desc"
            assert kwargs["file_type"] == "image"
            assert kwargs["source"] is None
            assert kwargs["min_confidence"] is None
            return type("Page", (), {"to_dict": lambda self: {"page": 1, "limit": 10, "total_count": 1, "total_pages": 1, "items": []}})()

    monkeypatch.setattr(reads_module, "OperatorConsoleReadService", _FakeOperatorConsoleReadService)

    services = ReadServices(session_factory=object(), cache=_FakeCache(invalidations=[]))  # type: ignore[arg-type]

    payload = services.canonical(
        page=1,
        limit=10,
        tags=("travel",),
        sort_by="created_at",
        sort_order="desc",
        file_type="image",
        source=None,
        min_confidence=None,
    )

    assert payload["total_count"] == 1


def test_admin_app_settings_returns_persisted_non_sensitive_metadata(session_factory) -> None:
    AppSettingsService(session_factory).set_value(
        "video_thumbnails_enabled",
        True,
        updated_by="tester",
        source="test",
        expected_version=0,
    )
    services = ReadServices(session_factory=session_factory, cache=_FakeCache(invalidations=[]))

    payload = services.admin_app_settings()
    item = next(entry for entry in payload["items"] if entry["key"] == "video_thumbnails_enabled")

    assert item["db_present"] is True
    assert item["runtime_dual_read_enabled"] is True
    assert item["effective_source"] == "db"
    assert item["updated_by"] == "tester"
    assert item["version"] == 1
    assert item["source"] == "test"
    assert item["value_json"] == {"value": True}


def test_admin_app_settings_dual_read_key_without_db_row_uses_env_fallback(session_factory) -> None:
    services = ReadServices(session_factory=session_factory, cache=_FakeCache(invalidations=[]))

    payload = services.admin_app_settings()
    item = next(entry for entry in payload["items"] if entry["key"] == "benchmark_worker_mode")

    assert item["runtime_dual_read_enabled"] is True
    assert item["db_present"] is False
    assert item["effective_source"] == "env_fallback"
    assert item["updated_at"] is None
    assert item["updated_by"] is None
    assert item["version"] is None
    assert item["source"] is None


def test_admin_app_settings_non_dual_read_key_is_conservative(session_factory) -> None:
    services = ReadServices(session_factory=session_factory, cache=_FakeCache(invalidations=[]))

    payload = services.admin_app_settings()
    item = next(entry for entry in payload["items"] if entry["key"] == "directory_picker_enabled")

    assert item["db_present"] is False
    assert item["runtime_dual_read_enabled"] is False
    assert item["effective_source"] is None


def test_admin_app_settings_omits_catalog_keys_removed_from_durable_surface(session_factory) -> None:
    services = ReadServices(session_factory=session_factory, cache=_FakeCache(invalidations=[]))

    payload = services.admin_app_settings()

    assert not any(entry["key"] == "benchmark_max_items" for entry in payload["items"])
    assert not any(entry["key"] == "allow_planner_mv_reads" for entry in payload["items"])


def test_admin_app_settings_sensitive_value_is_redacted(session_factory) -> None:
    AppSettingsService(session_factory).set_value(
        "db_reset_challenge_word",
        "media-manager",
        updated_by="tester",
        source="test",
        expected_version=0,
    )
    services = ReadServices(session_factory=session_factory, cache=_FakeCache(invalidations=[]))

    payload = services.admin_app_settings()
    item = next(entry for entry in payload["items"] if entry["key"] == "db_reset_challenge_word")

    assert item["db_present"] is True
    assert item["runtime_dual_read_enabled"] is False
    assert item["effective_source"] is None
    assert item["value_redacted"] is True
    assert "value_json" not in item
