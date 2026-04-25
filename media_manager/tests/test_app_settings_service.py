from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from media_manager.app.core.errors import (
    AppSettingsValidationError,
    AppSettingsVersionConflictError,
)
from media_manager.app.persistence.app_settings import _CATALOG, AppSettingsService
from media_manager.app.persistence.models import AppSetting, AppSettingHistory


def test_set_value_validates_canonical_policy_enum(session_factory) -> None:
    service = AppSettingsService(session_factory)

    created = service.set_value(
        "canonical_policy",
        "EXIF_FILENAME_FALLBACK",
        updated_by="tester",
        source="test",
        expected_version=0,
    )

    assert created.value == "EXIF_FILENAME_FALLBACK"


def test_set_value_rejects_invalid_benchmark_worker_mode(session_factory) -> None:
    service = AppSettingsService(session_factory)

    with pytest.raises(AppSettingsValidationError):
        service.set_value(
            "benchmark_worker_mode",
            "sometimes",
            updated_by="tester",
            source="test",
            expected_version=0,
        )


def test_set_value_clamps_metadata_batch_size(session_factory) -> None:
    service = AppSettingsService(session_factory)

    created = service.set_value(
        "metadata_upsert_batch_size",
        60_000,
        updated_by="tester",
        source="test",
        expected_version=0,
    )

    assert created.value == 50_000


def test_set_value_rejects_non_positive_cache_ttl(session_factory) -> None:
    service = AppSettingsService(session_factory)

    with pytest.raises(AppSettingsValidationError):
        service.set_value(
            "canonical_read_cache_ttl_seconds",
            0.0,
            updated_by="tester",
            source="test",
            expected_version=0,
        )


def test_set_value_rejects_boolean_for_numeric_settings(session_factory) -> None:
    service = AppSettingsService(session_factory)

    with pytest.raises(AppSettingsValidationError):
        service.set_value(
            "canonical_read_cache_ttl_seconds",
            True,
            updated_by="tester",
            source="test",
            expected_version=0,
        )

    with pytest.raises(AppSettingsValidationError):
        service.set_value(
            "metadata_upsert_batch_size",
            False,
            updated_by="tester",
            source="test",
            expected_version=0,
        )


def test_set_value_uses_optimistic_concurrency(session_factory) -> None:
    service = AppSettingsService(session_factory)

    created = service.set_value(
        "video_thumbnails_enabled",
        True,
        updated_by="tester",
        source="test",
        expected_version=0,
    )

    updated = service.set_value(
        "video_thumbnails_enabled",
        False,
        updated_by="tester",
        source="test",
        expected_version=created.version,
    )

    assert updated.value is False
    assert updated.version == created.version + 1

    with pytest.raises(AppSettingsVersionConflictError):
        service.set_value(
            "video_thumbnails_enabled",
            True,
            updated_by="tester",
            source="test",
            expected_version=created.version,
        )


def test_sensitive_history_payloads_are_redacted(session_factory) -> None:
    service = AppSettingsService(session_factory)

    created = service.set_value(
        "db_reset_challenge_word",
        "media-manager",
        updated_by="tester",
        source="test",
        expected_version=0,
    )
    service.set_value(
        "db_reset_challenge_word",
        "rotated-secret",
        updated_by="tester",
        source="test",
        expected_version=created.version,
    )

    with session_factory() as session:
        history = (
            session.query(AppSettingHistory)
            .filter(AppSettingHistory.key == "db_reset_challenge_word")
            .order_by(AppSettingHistory.id.asc())
            .all()
        )

    assert len(history) == 2
    assert history[0].old_value_json is None
    assert history[0].new_value_json == {"value": "<REDACTED>"}
    assert history[1].old_value_json == {"value": "<REDACTED>"}
    assert history[1].new_value_json == {"value": "<REDACTED>"}


def test_set_value_translates_concurrent_create_conflict(session_factory, monkeypatch) -> None:
    service = AppSettingsService(session_factory)
    original_flush = Session.flush
    triggered = {"value": False}

    def flaky_flush(self, *args, **kwargs):
        if not triggered["value"]:
            for obj in self.new:
                if isinstance(obj, AppSetting) and obj.key == "video_thumbnails_enabled":
                    triggered["value"] = True
                    raise IntegrityError("insert", params=None, orig=RuntimeError("duplicate key"))
        return original_flush(self, *args, **kwargs)

    monkeypatch.setattr(Session, "flush", flaky_flush)

    with pytest.raises(AppSettingsVersionConflictError):
        service.set_value(
            "video_thumbnails_enabled",
            True,
            updated_by="tester",
            source="test",
            expected_version=0,
        )


def test_bootstrap_from_env_parses_current_runtime_values(session_factory, monkeypatch, tmp_path: Path) -> None:
    service = AppSettingsService(session_factory)

    monkeypatch.setenv("MEDIA_REQUIRED_CODES", "OWNER,CONTEXT,TAKEN_DT")
    monkeypatch.setenv("MEDIA_CANONICAL_STORAGE_PATH", str((tmp_path / "canonical").resolve()))
    monkeypatch.setenv("MEDIA_DUPLICATE_STORAGE_PATH", str((tmp_path / "duplicates").resolve()))
    monkeypatch.setenv("MEDIA_MANAGER_TAG_NORMALIZATION_REMOVE_PUNCTUATION", "0")
    monkeypatch.setenv("MEDIA_CANONICAL_POLICY", "FIRST_SEEN")
    monkeypatch.setenv("MEDIA_PREFERRED_ROOTS", "")
    monkeypatch.setenv("CANONICAL_READ_CACHE_ENABLED", "1")
    monkeypatch.setenv("CANONICAL_READ_CACHE_TTL_SECONDS", "30")
    monkeypatch.setenv("METADATA_UPSERT_BATCH_SIZE", "1000")
    monkeypatch.setenv("MEDIA_MANAGER_ALLOW_PLANNER_MV_READS", "false")
    monkeypatch.setenv("MEDIA_MANAGER_DIRECTORY_PICKER_ENABLED", "true")
    monkeypatch.setenv(
        "MEDIA_MANAGER_DIRECTORY_PICKER_ROOTS",
        "/tmp/a,/tmp/b,/tmp/c",
    )
    monkeypatch.setenv("MEDIA_MANAGER_VIDEO_THUMBNAILS_ENABLED", "true")
    monkeypatch.setenv("MEDIA_MANAGER_VIDEO_THUMBNAIL_CACHE_DIR", str((tmp_path / "thumbs").resolve()))
    monkeypatch.setenv("MEDIA_MANAGER_DB_RESET_INCLUDE_DYNAMIC", "false")
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARKS_ENABLED", "true")
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARK_POLL_INTERVAL_SECONDS", "2.0")
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARK_STALE_AFTER_SECONDS", "900")
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARK_WORKER_MODE", "forever")
    monkeypatch.setenv("MEDIA_MANAGER_DB_RESET_CHALLENGE_WORD", "media-manager")

    result = service.bootstrap_from_env()

    assert set(result.inserted_keys) == set(_CATALOG)
    assert result.skipped_keys == ()
    assert service.get_setting("required_metadata_codes").value == ["OWNER", "CONTEXT", "TAKEN_DT"]
    assert service.get_setting("preferred_roots").value == []
    assert service.get_setting("directory_picker_roots").value == ["/tmp/a", "/tmp/b", "/tmp/c"]
    assert service.get_setting("canonical_read_cache_enabled").value is True
    assert service.get_setting("canonical_read_cache_ttl_seconds").value == 30.0
    assert service.get_setting("video_thumbnail_cache_dir").value == str((tmp_path / "thumbs").resolve())

    with session_factory() as session:
        history = (
            session.query(AppSettingHistory)
            .filter(AppSettingHistory.key == "db_reset_challenge_word")
            .one()
        )

    assert history.new_value_json == {"value": "<REDACTED>"}


def test_bootstrap_is_idempotent_and_skips_existing_rows(session_factory, monkeypatch, tmp_path: Path) -> None:
    service = AppSettingsService(session_factory)
    monkeypatch.setenv("MEDIA_CANONICAL_STORAGE_PATH", str((tmp_path / "canonical").resolve()))
    monkeypatch.setenv("MEDIA_DUPLICATE_STORAGE_PATH", str((tmp_path / "duplicates").resolve()))

    first = service.bootstrap_from_env()
    second = service.bootstrap_from_env()

    assert len(first.inserted_keys) == len(_CATALOG)
    assert second.inserted_keys == ()
    assert set(second.skipped_keys) == set(_CATALOG)


def test_bootstrap_rejects_invalid_enum(session_factory, monkeypatch, tmp_path: Path) -> None:
    service = AppSettingsService(session_factory)
    monkeypatch.setenv("MEDIA_CANONICAL_STORAGE_PATH", str((tmp_path / "canonical").resolve()))
    monkeypatch.setenv("MEDIA_DUPLICATE_STORAGE_PATH", str((tmp_path / "duplicates").resolve()))
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARK_WORKER_MODE", "invalid")

    with pytest.raises(AppSettingsValidationError):
        service.bootstrap_from_env()
