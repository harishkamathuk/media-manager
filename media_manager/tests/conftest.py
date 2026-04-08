from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from media_manager.app.core.config import load_environment
from media_manager.app.persistence.base import create_session_factory
from media_manager.app.persistence.runs import RunService

PUBLIC_TABLES_TO_TRUNCATE = (
    "media_metadata",
    "metadata_codes",
    "planned_actions",
    "apply_audit_items",
    "apply_audit_runs",
    "canonical_recompute_items",
    "canonical_recompute_runs",
    "canonical_assignments",
    "tag_enrichment_items",
    "tag_enrichment_runs",
    "benchmark_runs",
    "app_settings_history",
    "app_settings",
    "integrity_quarantine_records",
    "integrity_check_runs",
    "integrity_review_decisions",
    "integrity_signals",
    "integrity_checks",
    "operation_runs",
    "media_file",
    "canonical_tags",
    "tags",
    "operator_policy_settings",
    "file_instances",
    "file_contents",
    "failure_events",
    "files",
    "content_objects",
    "runs",
)

LEGACY_3NF_TABLES_TO_TRUNCATE = (
    "canonical_candidate",
    "deletion_audit_candidate_instance",
    "deletion_audit_candidate",
    "deletion_audit_run",
    "duplicate_evidence",
    "action_event",
    "media_attributes",
    "file_instance",
    "content_identity",
    "scan_batch",
    "import_failure_events",
    "import_runs",
)

LEGACY_RAW_TABLES_TO_TRUNCATE = (
    "_tmp_deletion_audit_import",
    "deletion_audit_candidate_files",
    "deletion_audit_candidates",
    "deletion_audit_runs",
    "duplicate_candidates",
    "_file_actions_old",
    "file_actions",
    "files",
    "scans",
)


@pytest.fixture(scope="session")
def test_database_url() -> str:
    load_environment()
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        raise RuntimeError("TEST_DATABASE_URL must be set to a PostgreSQL database URL.")
    if "postgresql" not in url:
        raise RuntimeError("TEST_DATABASE_URL must point to PostgreSQL.")
    return url


@pytest.fixture(scope="session")
def db_engine(test_database_url: str) -> Iterator[Engine]:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", test_database_url)

    original_database_url = os.getenv("DATABASE_URL")
    os.environ["DATABASE_URL"] = test_database_url
    try:
        command.upgrade(cfg, "head")
    finally:
        if original_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = original_database_url
    engine = create_engine(test_database_url, future=True)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def truncatable_tables(db_engine: Engine) -> dict[str | None, tuple[str, ...]]:
    inspector = inspect(db_engine)

    public_tables = set(inspector.get_table_names())
    legacy_3nf_tables = set(inspector.get_table_names(schema="legacy_3nf"))
    legacy_raw_tables = set(inspector.get_table_names(schema="legacy_raw"))

    return {
        None: tuple(table for table in PUBLIC_TABLES_TO_TRUNCATE if table in public_tables),
        "legacy_3nf": tuple(table for table in LEGACY_3NF_TABLES_TO_TRUNCATE if table in legacy_3nf_tables),
        "legacy_raw": tuple(table for table in LEGACY_RAW_TABLES_TO_TRUNCATE if table in legacy_raw_tables),
    }


def _truncate_tables(conn, tables: tuple[str, ...], *, schema: str | None = None) -> None:
    if not tables:
        return

    if schema is None:
        qualified_tables = ", ".join(tables)
    else:
        qualified_tables = ", ".join(f"{schema}.{table}" for table in tables)

    conn.execute(text(f"TRUNCATE TABLE {qualified_tables} RESTART IDENTITY CASCADE"))


@pytest.fixture(autouse=True)
def clean_tables(db_engine: Engine, truncatable_tables: dict[str | None, tuple[str, ...]]) -> None:
    with db_engine.begin() as conn:
        _truncate_tables(conn, truncatable_tables[None])
        _truncate_tables(conn, truncatable_tables["legacy_3nf"], schema="legacy_3nf")
        _truncate_tables(conn, truncatable_tables["legacy_raw"], schema="legacy_raw")


@pytest.fixture(autouse=True)
def storage_roots_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MEDIA_CANONICAL_STORAGE_PATH", str(tmp_path.resolve()))
    monkeypatch.setenv("MEDIA_DUPLICATE_STORAGE_PATH", str((tmp_path / "Duplicates").resolve()))


@pytest.fixture
def session_factory(db_engine: Engine) -> sessionmaker:
    return create_session_factory(db_engine)


@pytest.fixture
def run_service(session_factory: sessionmaker) -> RunService:
    return RunService(session_factory)