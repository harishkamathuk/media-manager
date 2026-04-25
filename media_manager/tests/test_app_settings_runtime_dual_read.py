from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest

from media_manager.app.core.errors import AppSettingsValidationError
from media_manager.app.persistence import materialized_reads
from media_manager.app.persistence.app_settings import AppSettingsService
from media_manager.app.persistence.operator_console import (
    _video_thumbnail_cache_dir,
    _video_thumbnails_enabled,
)
from media_manager.app.persistence.planner import PlanningService
from media_manager.app.workers import benchmark_runner


def test_materialized_reads_uses_env_fallback_with_warning(session_factory, monkeypatch) -> None:
    monkeypatch.setenv("CANONICAL_READ_CACHE_ENABLED", "true")
    monkeypatch.setenv("CANONICAL_READ_CACHE_TTL_SECONDS", "45")
    calls: list[str] = []
    monkeypatch.setattr(
        materialized_reads.LOGGER,
        "warning",
        lambda message, *args, **kwargs: calls.append(str(message)),
    )

    with session_factory() as session:
        assert materialized_reads._env_cache_enabled(session) is True
        assert materialized_reads._env_cache_ttl(session) == 45.0

    assert any("using environment fallback" in line for line in calls)


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


def test_operator_console_video_thumbnail_settings_dual_read(session_factory, monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MEDIA_MANAGER_VIDEO_THUMBNAILS_ENABLED", "false")
    monkeypatch.setenv("MEDIA_MANAGER_VIDEO_THUMBNAIL_CACHE_DIR", str((tmp_path / "env-thumbs").resolve()))

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


def test_planner_metadata_batch_size_dual_read(session_factory, monkeypatch) -> None:
    planner = PlanningService(session_factory)
    monkeypatch.setenv("METADATA_UPSERT_BATCH_SIZE", "2500")

    assert planner._get_metadata_batch_size() == 2500

    AppSettingsService(session_factory).set_value(
        "metadata_upsert_batch_size",
        500,
        updated_by="tester",
        source="test",
        expected_version=0,
    )

    assert planner._get_metadata_batch_size() == 500


def test_allow_planner_mv_reads_is_not_part_of_the_app_settings_runtime_surface(session_factory) -> None:
    with pytest.raises(AppSettingsValidationError, match="Unknown app setting key"):
        AppSettingsService(session_factory).resolve_runtime_value("allow_planner_mv_reads")


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


def test_benchmark_runner_main_uses_db_first_benchmarks_enabled(
    session_factory, test_database_url: str, monkeypatch
) -> None:
    AppSettingsService(session_factory).set_value(
        "benchmarks_enabled",
        False,
        updated_by="tester",
        source="test",
        expected_version=0,
    )
    monkeypatch.setenv("DATABASE_URL", test_database_url)
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARKS_ENABLED", "true")

    monkeypatch.setattr(benchmark_runner, "run_once", lambda: pytest.fail("run_once should not be called"))
    monkeypatch.setattr(benchmark_runner, "run_forever", lambda: pytest.fail("run_forever should not be called"))

    with pytest.raises(SystemExit, match="Benchmarks are disabled"):
        benchmark_runner.main()


def test_benchmark_runner_main_warns_and_falls_back_to_env_benchmarks_enabled(
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
    monkeypatch.setattr(
        benchmark_runner.LOGGER,
        "warning",
        lambda message, *args, **kwargs: calls.append(str(message)),
    )

    run_calls: list[str] = []
    monkeypatch.setattr(benchmark_runner, "run_once", lambda: run_calls.append("once") or False)
    monkeypatch.setattr(benchmark_runner, "run_forever", lambda: run_calls.append("forever"))

    benchmark_runner.main()

    assert run_calls == ["once"]
    assert any("using environment fallback" in line for line in calls)


def test_benchmark_runner_main_warns_and_falls_back_to_env_worker_mode(
    session_factory, test_database_url: str, monkeypatch
) -> None:
    monkeypatch.setenv("DATABASE_URL", test_database_url)
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARKS_ENABLED", "true")
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARK_WORKER_MODE", "once")
    calls: list[str] = []
    monkeypatch.setattr(
        benchmark_runner.LOGGER,
        "warning",
        lambda message, *args, **kwargs: calls.append(str(message)),
    )

    run_calls: list[str] = []
    monkeypatch.setattr(benchmark_runner, "run_once", lambda: run_calls.append("once") or False)
    monkeypatch.setattr(benchmark_runner, "run_forever", lambda: run_calls.append("forever"))

    benchmark_runner.main()

    assert run_calls == ["once"]
    assert any("using environment fallback" in line for line in calls)


def test_benchmark_runner_run_once_uses_db_first_stale_after(
    session_factory, test_database_url: str, monkeypatch
) -> None:
    AppSettingsService(session_factory).set_value(
        "benchmark_stale_after_seconds",
        12.5,
        updated_by="tester",
        source="test",
        expected_version=0,
    )
    monkeypatch.setenv("DATABASE_URL", test_database_url)
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARK_STALE_AFTER_SECONDS", "900")

    observed: dict[str, timedelta] = {}

    class DummyBenchmarkRunStore:
        def __init__(self, session_factory) -> None:
            self._session_factory = session_factory

        def abandon_stale_running(self, *, stale_after: timedelta):
            observed["stale_after"] = stale_after
            return []

        def claim_next(self):
            return None

    class DummyOperationRunService:
        def __init__(self, session_factory) -> None:
            self._session_factory = session_factory

    monkeypatch.setattr(benchmark_runner, "BenchmarkRunStore", DummyBenchmarkRunStore)
    monkeypatch.setattr(benchmark_runner, "OperationRunService", DummyOperationRunService)

    assert benchmark_runner.run_once() is False
    assert observed["stale_after"] == timedelta(seconds=12.5)


def test_benchmark_runner_run_once_warns_and_falls_back_to_env_stale_after(
    session_factory, test_database_url: str, monkeypatch
) -> None:
    monkeypatch.setenv("DATABASE_URL", test_database_url)
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARK_STALE_AFTER_SECONDS", "17.0")
    calls: list[str] = []
    monkeypatch.setattr(
        benchmark_runner.LOGGER,
        "warning",
        lambda message, *args, **kwargs: calls.append(str(message)),
    )

    observed: dict[str, timedelta] = {}

    class DummyBenchmarkRunStore:
        def __init__(self, session_factory) -> None:
            self._session_factory = session_factory

        def abandon_stale_running(self, *, stale_after: timedelta):
            observed["stale_after"] = stale_after
            return []

        def claim_next(self):
            return None

    class DummyOperationRunService:
        def __init__(self, session_factory) -> None:
            self._session_factory = session_factory

    monkeypatch.setattr(benchmark_runner, "BenchmarkRunStore", DummyBenchmarkRunStore)
    monkeypatch.setattr(benchmark_runner, "OperationRunService", DummyOperationRunService)

    assert benchmark_runner.run_once() is False
    assert observed["stale_after"] == timedelta(seconds=17.0)
    assert any("using environment fallback" in line for line in calls)


def test_benchmark_max_items_is_not_part_of_the_app_settings_runtime_surface(session_factory) -> None:
    with pytest.raises(AppSettingsValidationError, match="Unknown app setting key"):
        AppSettingsService(session_factory).resolve_runtime_value("benchmark_max_items")


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
