from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from media_manager.app.canonical.policies import ShortestPathPolicy
from media_manager.app.persistence.base import create_db_engine, create_session_factory
from media_manager.app.persistence.canonicalization import append_assignment
from media_manager.app.persistence.ingest import IngestService
from media_manager.app.persistence.materialized_reads import benchmark_planner_lookup, refresh_materialized_view
from media_manager.app.persistence.models import FileContent, FileInstance


def _write_file(path: Path, payload: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _seed_library(tmp_path: Path, session_factory) -> None:
    ingest = IngestService(session_factory)
    root = tmp_path / "library"
    for idx in range(1, 12):
        _write_file(root / "set" / f"image_{idx:02d}.jpg", f"payload-{idx}".encode())
    ingest.ingest_path(root)
    with session_factory.begin() as session:
        content_ids = session.scalars(select(FileContent.content_id).order_by(FileContent.content_id.asc())).all()
        for content_id in content_ids:
            canonical_instance_id = session.scalar(
                select(FileInstance.file_instance_id)
                .where(FileInstance.content_id == content_id)
                .order_by(FileInstance.absolute_path.asc(), FileInstance.file_instance_id.asc())
            )
            assert canonical_instance_id is not None
            append_assignment(
                session,
                content_id=content_id,
                canonical_instance_id=canonical_instance_id,
                policy_name=ShortestPathPolicy.name,
                policy_version="v1",
            )


def test_benchmark_sampling_and_order_are_deterministic(
    tmp_path: Path,
    test_database_url: str,
    session_factory,
    monkeypatch,
) -> None:
    monkeypatch.setenv("DATABASE_URL", test_database_url)
    _seed_library(tmp_path, session_factory)

    engine = create_db_engine(test_database_url)
    refresh_materialized_view(engine, concurrently=False)

    first = benchmark_planner_lookup(
        create_session_factory(engine),
        sample_size=5,
        repeats=5,
        use_cache=False,
        seed=123,
    )
    second = benchmark_planner_lookup(
        create_session_factory(engine),
        sample_size=5,
        repeats=5,
        use_cache=False,
        seed=123,
    )

    assert first.sampled_content_ids == second.sampled_content_ids
    assert first.query_order_pattern == second.query_order_pattern
    assert len(first.query_order_pattern) == 5
    assert first.base_mean_ms >= 0
    assert first.mv_mean_ms >= 0
