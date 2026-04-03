from __future__ import annotations

import logging
from pathlib import Path

import pytest

from media_manager.app.persistence.app_settings import AppSettingsService
from media_manager.app.persistence import materialized_reads
from media_manager.app.persistence.operator_console import _video_thumbnail_cache_dir, _video_thumbnails_enabled
from media_manager.app.persistence.planner import PlanningService
from media_manager.app.workers import benchmark_runner


def test_materialized_reads_uses_env_fallback_with_warning(session_factory, caplog, monkeypatch) -> None:
    monkeypatch.setenv("CANONICAL_READ_CACHE_ENABLED", "true")
    monkeypatch.setenv("CANONICAL_READ_CACHE_TTL_SECONDS", "45")

    with session_factory() as session, caplog.at_level(logging.WARNING):
        assert materialized_reads._env_cache_enabled(session) is True
        assert materialized_reads._env_cache_ttl(session) == 45.0

    assert "using environment fallback" in caplog.text


def test_materialized_reads_prefers_db_settings(session_factory, monkeypatch) -> None:
    service = AppSettingsService(session_factory)
    service.set_value("canonical_read_cache_enabled", False, updated_by="tester", source="test", expected_version=0)
    service.set_value(
        "canonical_read_cache_ttl_seconds",
        12.5,
        updated_by="tester",
        source="test",
        expected_version=0,
    )
    monkeypatch.setenv("CANONICAL_READ_CACHE_ENABLED", "true")
    monkeypatch.setenv("CANONICAL_READ_CACHE_TTL_SECONDS", "45")

    with session_factory() as session:
        assert materialized_reads._env_cache_enabled(session) is False
        assert materialized_reads._env_cache_ttl(session) == 12.5


def test_operator_console_video_thumbnail_settings_dual_read(session_factory, caplog, monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MEDIA_MANAGER_VIDEO_THUMBNAILS_ENABLED", "false")
    monkeypatch.setenv("MEDIA_MANAGER_VIDEO_THUMBNAIL_CACHE_DIR", str((tmp_path / "env-thumbs").resolve()))

    with caplog.at_level(logging.WARNING):
        assert _video_thumbnails_enabled(session_factory) is False
        assert _video_thumbnail_cache_dir(session_factory) == (tmp_path / "env-thumbs").resolve()

    service = AppSettingsService(session_factory)
    service.set_value("video_thumbnails_enabled", True, updated_by="tester", source="test", expected_version=0)
    service.set_value(
        "video_thumbnail_cache_dir",
        str((tmp_path / "db-thumbs").resolve()),
        updated_by="tester",
        source="test",
        expected_version=0,
    )

    assert _video_thumbnails_enabled(session_factory) is True
    assert _video_thumbnail_cache_dir(session_factory) == (tmp_path / "db-thumbs").resolve()


def test_planner_metadata_batch_size_dual_read(session_factory, caplog, monkeypatch) -> None:
    planner = PlanningService(session_factory)
    monkeypatch.setenv("METADATA_UPSERT_BATCH_SIZE", "2500")

    with caplog.at_level(logging.WARNING):
        assert planner._get_metadata_batch_size() == 2500

    AppSettingsService(session_factory).set_value(
        "metadata_upsert_batch_size",
        500,
        updated_by="tester",
        source="test",
        expected_version=0,
    )

    assert planner._get_metadata_batch_size() == 500


def test_benchmark_runner_main_uses_db_first_worker_mode(
    session_factory, test_database_url: str, monkeypatch
) -> None:
    AppSettingsService(session_factory).set_value(
        "benchmark_worker_mode",
        "once",
        updated_by="tester",
        source="test",
        expected_version=0,
    )
    monkeypatch.setenv("DATABASE_URL", test_database_url)
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARKS_ENABLED", "true")

    calls: list[str] = []
    monkeypatch.setattr(benchmark_runner, "run_once", lambda: calls.append("once") or False)
    monkeypatch.setattr(benchmark_runner, "run_forever", lambda: calls.append("forever"))

    benchmark_runner.main()

    assert calls == ["once"]


def test_benchmark_runner_main_warns_and_falls_back_to_env_worker_mode(
    session_factory, test_database_url: str, monkeypatch, caplog
) -> None:
    monkeypatch.setenv("DATABASE_URL", test_database_url)
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARKS_ENABLED", "true")
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARK_WORKER_MODE", "once")

    calls: list[str] = []
    monkeypatch.setattr(benchmark_runner, "run_once", lambda: calls.append("once") or False)
    monkeypatch.setattr(benchmark_runner, "run_forever", lambda: calls.append("forever"))

    with caplog.at_level(logging.WARNING):
        benchmark_runner.main()

    assert calls == ["once"]
    assert "using environment fallback" in caplog.text


def test_benchmark_runner_run_forever_uses_db_first_poll_interval(
    session_factory, test_database_url: str, monkeypatch
) -> None:
    AppSettingsService(session_factory).set_value(
        "benchmark_poll_interval_seconds",
        7.5,
        updated_by="tester",
        source="test",
        expected_version=0,
    )
    monkeypatch.setenv("DATABASE_URL", test_database_url)

    sleeps: list[float] = []
    monkeypatch.setattr(benchmark_runner, "run_once", lambda: False)

    def _sleep(seconds: float) -> None:
        sleeps.append(seconds)
        raise RuntimeError("stop-loop")

    monkeypatch.setattr(benchmark_runner.time, "sleep", _sleep)

    with pytest.raises(RuntimeError, match="stop-loop"):
        benchmark_runner.run_forever()

    assert sleeps == [7.5]
