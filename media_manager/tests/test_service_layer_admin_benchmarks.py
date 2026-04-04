from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from media_manager.app.persistence.app_settings import AppSettingsService
from media_manager.app.persistence.admin_benchmarks import BenchmarkExecutionResult
from media_manager.app.core.errors import AppSettingsValidationError, AppSettingsVersionConflictError
from media_manager.app.persistence.models import (
    AppSettingHistory,
    BenchmarkRun,
    BenchmarkRunStatus,
    OperationRun,
    OperationRunStatus,
    OperationRunType,
)
from media_manager.app.service_layer.admin import AdminServices
from media_manager.app.service_layer.errors import ServiceLayerException
from media_manager.app.workers import benchmark_runner


def test_benchmark_queue_creates_durable_benchmark_and_operation_run(session_factory, monkeypatch) -> None:
    monkeypatch.setenv("MEDIA_MANAGER_ENV", "test")
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARKS_ENABLED", "true")
    service = AdminServices(session_factory=session_factory)

    result = service.benchmark_metadata_queue(items=100, batch_size=25, challenge_word="media-manager")

    assert result["queued"] is True
    operation_run_id = result["operation_run_id"]
    with session_factory() as session:
        parsed = UUID(str(operation_run_id))
        op_run = session.scalar(select(OperationRun).where(OperationRun.id == parsed))
        bench_run = session.scalar(select(BenchmarkRun).where(BenchmarkRun.operation_run_id == parsed))
        assert op_run is not None
        assert op_run.operation_type == OperationRunType.BENCHMARK_METADATA
        assert op_run.status == OperationRunStatus.STARTED
        assert bench_run is not None
        assert bench_run.status == BenchmarkRunStatus.QUEUED
        assert bench_run.parameters["items"] == 100


def test_benchmark_queue_requires_enabled_flag_and_challenge(session_factory, monkeypatch) -> None:
    monkeypatch.setenv("MEDIA_MANAGER_ENV", "test")
    monkeypatch.delenv("MEDIA_MANAGER_BENCHMARKS_ENABLED", raising=False)
    service = AdminServices(session_factory=session_factory)
    try:
        service.benchmark_discovery_queue(items=100, challenge_word="media-manager")
        assert False, "expected disabled-feature error"
    except ServiceLayerException as exc:
        assert exc.http_status == 403

    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARKS_ENABLED", "true")
    try:
        service.benchmark_discovery_queue(items=100, challenge_word="wrong")
        assert False, "expected challenge validation error"
    except ServiceLayerException as exc:
        assert exc.http_status == 400


def test_benchmark_cancel_marks_queued_operation_run_failed(session_factory, monkeypatch) -> None:
    monkeypatch.setenv("MEDIA_MANAGER_ENV", "test")
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARKS_ENABLED", "true")
    service = AdminServices(session_factory=session_factory)
    queued = service.benchmark_discovery_queue(items=50, challenge_word="media-manager")

    cancelled = service.benchmark_run_cancel(operation_run_id=queued["operation_run_id"])

    assert cancelled["status"] == "CANCEL_REQUESTED"
    with session_factory() as session:
        op_run = session.scalar(select(OperationRun).where(OperationRun.id == UUID(str(queued["operation_run_id"]))))
        assert op_run is not None
        assert op_run.status == OperationRunStatus.FAILED


def test_benchmark_worker_processes_queued_job(test_database_url: str, session_factory, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", test_database_url)
    monkeypatch.setenv("MEDIA_MANAGER_ENV", "test")
    monkeypatch.setenv("MEDIA_MANAGER_BENCHMARKS_ENABLED", "true")
    service = AdminServices(session_factory=session_factory)
    queued = service.benchmark_metadata_queue(items=25, batch_size=5, challenge_word="media-manager")

    def _fake_metadata(*args, **kwargs):  # type: ignore[no-untyped-def]
        return BenchmarkExecutionResult(
            summary={"throughput_files_per_s": 123.4},
            report={"results": [{"scenario": "metadata"}]},
            cleanup_status="COMPLETED",
            cleanup_error=None,
        )

    monkeypatch.setattr(benchmark_runner, "run_metadata_benchmark", _fake_metadata)

    assert benchmark_runner.run_once() is True

    with session_factory() as session:
        parsed = UUID(str(queued["operation_run_id"]))
        op_run = session.scalar(select(OperationRun).where(OperationRun.id == parsed))
        bench_run = session.scalar(select(BenchmarkRun).where(BenchmarkRun.operation_run_id == parsed))
        assert op_run is not None
        assert op_run.status == OperationRunStatus.COMPLETED
        assert bench_run is not None
        assert bench_run.status == BenchmarkRunStatus.COMPLETED
        assert bench_run.summary_payload["throughput_files_per_s"] == 123.4


def test_update_app_setting_updates_allowlisted_runtime_key(session_factory) -> None:
    service = AdminServices(session_factory=session_factory)
    AppSettingsService(session_factory).set_value(
        "video_thumbnails_enabled",
        True,
        updated_by="bootstrap",
        source="bootstrap",
        expected_version=0,
    )

    result = service.update_app_setting(key="video_thumbnails_enabled", value=False, version=1)

    assert result["key"] == "video_thumbnails_enabled"
    assert result["value_json"] == {"value": False}
    assert result["updated_by"] == "operator_console:admin"
    assert result["source"] == "admin_ui"
    assert result["version"] == 2

    with session_factory() as session:
        history = session.scalars(
            select(AppSettingHistory)
            .where(AppSettingHistory.key == "video_thumbnails_enabled")
            .order_by(AppSettingHistory.id.asc())
        ).all()

    assert len(history) == 2
    assert history[-1].reason == "allowlisted_admin_update"


def test_update_app_setting_rejects_non_allowlisted_key(session_factory) -> None:
    service = AdminServices(session_factory=session_factory)

    try:
        service.update_app_setting(key="directory_picker_enabled", value=True, version=0)
        assert False, "expected validation error"
    except ServiceLayerException as exc:
        assert exc.http_status == 400
        assert "not editable in this slice" in exc.message


def test_update_app_setting_preserves_validation_and_version_conflict(session_factory) -> None:
    service = AdminServices(session_factory=session_factory)
    created = AppSettingsService(session_factory).set_value(
        "canonical_read_cache_ttl_seconds",
        30.0,
        updated_by="bootstrap",
        source="bootstrap",
        expected_version=0,
    )

    try:
        service.update_app_setting(key="canonical_read_cache_ttl_seconds", value=0, version=created.version)
        assert False, "expected validation error"
    except AppSettingsValidationError:
        pass

    try:
        service.update_app_setting(key="canonical_read_cache_ttl_seconds", value=45.0, version=created.version - 1)
        assert False, "expected version conflict"
    except AppSettingsVersionConflictError:
        pass
