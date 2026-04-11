from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import select

from media_manager.app.persistence.apply import ApplyService
from media_manager.app.persistence.models import (
    DuplicateBinState,
    DuplicateReclaimItem,
    DuplicateReclaimItemStatus,
    DuplicateReclaimRecord,
    DuplicateReclaimStatus,
    FailureEvent,
    FileContent,
    FileInstance,
    FileInstanceStatus,
    IntegrityCheck,
    IntegrityCheckRun,
    IntegrityQuarantineRecord,
    IntegrityQuarantineStatus,
    PlannedAction,
    Run,
    RunStateDB,
)
from media_manager.app.persistence.phase3_actions import Phase3ActionService


def _add_content(session, content_id: UUID, sha256_hash: str, at: datetime) -> None:
    session.add(
        FileContent(
            content_id=content_id,
            sha256_hash=sha256_hash,
            first_seen_at=at,
        )
    )


def _add_instance(
    session,
    *,
    file_instance_id: UUID,
    content_id: UUID,
    absolute_path: str,
    first_seen_at: datetime,
    status: str = FileInstanceStatus.ACTIVE.value,
) -> None:
    session.add(
        FileInstance(
            file_instance_id=file_instance_id,
            content_id=content_id,
            absolute_path=absolute_path,
            filesystem_id="fs-1",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            status=status,
        )
    )


def test_purge_duplicate_reclaim_sets_bin_state_purged(
    session_factory,
    monkeypatch,
    tmp_path: Path,
) -> None:
    """After purge apply, DuplicateReclaimItem.bin_state must be PURGED."""
    reclaim_root = tmp_path / "reclaim-root"
    recycle_root = tmp_path / "recycle-bin-root"
    monkeypatch.setenv("MEDIA_MANAGER_RECLAIM_ROOT", str(reclaim_root))
    monkeypatch.setenv("MEDIA_MANAGER_RECYCLE_BIN_ROOT", str(recycle_root))
    service = Phase3ActionService(session_factory)
    base = datetime(2026, 4, 10, 10, 0, tzinfo=UTC)
    monkeypatch.setattr(
        "media_manager.app.persistence.phase3_actions._utcnow",
        lambda: base + timedelta(days=8),
    )
    content_id = UUID("a135b1ed-4dc6-4a0d-88d5-81726006507c")
    canonical_instance = UUID("a135b1ed-4dc6-4a0d-88d5-817260065071")
    duplicate_instance = UUID("a135b1ed-4dc6-4a0d-88d5-817260065072")

    recycle_path = (
        recycle_root / "duplicates" / str(content_id) / f"{duplicate_instance}-copy.jpg"
    )
    recycle_path.parent.mkdir(parents=True, exist_ok=True)
    recycle_path.write_bytes(b"copy-data")

    with session_factory.begin() as session:
        _add_content(session, content_id, "hash-purge-bin-state", base)
        session.flush()
        _add_instance(
            session,
            file_instance_id=canonical_instance,
            content_id=content_id,
            absolute_path=str(tmp_path / "library" / "main.jpg"),
            first_seen_at=base,
        )
        _add_instance(
            session,
            file_instance_id=duplicate_instance,
            content_id=content_id,
            absolute_path=str(recycle_path),
            first_seen_at=base + timedelta(seconds=1),
        )
        session.add(
            DuplicateReclaimRecord(
                content_id=content_id,
                reclaim_status=DuplicateReclaimStatus.SCHEDULED_FOR_DELETE.value,
                reviewed_at=base,
                reviewed_by="tester",
                restored_at=None,
                created_at=base,
                updated_at=base,
            )
        )
        session.add(
            DuplicateReclaimItem(
                file_instance_id=duplicate_instance,
                content_id=content_id,
                original_path=str(tmp_path / "library" / "copy.jpg"),
                archive_path=str(recycle_path),
                planned_bin_path=None,
                bin_path=str(recycle_path),
                item_status=DuplicateReclaimItemStatus.RECYCLED.value,
                reclaimed_at=base,
                bin_entered_at=base,
                expires_at=base + timedelta(days=7),
                restore_expires_at=base + timedelta(days=7),
                bin_state=DuplicateBinState.IN_BIN.value,
                recycle_path=str(recycle_path),
                recycled_at=base,
                purge_after_at=base + timedelta(days=7),
                purged_at=None,
                restored_at=None,
                created_at=base,
                updated_at=base,
            )
        )

    result = service.purge_duplicate_reclaim(file_instance_ids=[duplicate_instance])

    assert result["summary"]["applied_count"] == 1
    assert not recycle_path.exists(), "file should be deleted after purge"

    with session_factory() as session:
        item = session.get(DuplicateReclaimItem, duplicate_instance)
        assert item is not None
        assert item.bin_state == DuplicateBinState.PURGED.value
        assert item.purged_at is not None


def test_purge_duplicate_planner_excludes_already_purged_items(
    session_factory,
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Items with purged_at set must not be re-planned for purge."""
    reclaim_root = tmp_path / "reclaim-root"
    recycle_root = tmp_path / "recycle-bin-root"
    monkeypatch.setenv("MEDIA_MANAGER_RECLAIM_ROOT", str(reclaim_root))
    monkeypatch.setenv("MEDIA_MANAGER_RECYCLE_BIN_ROOT", str(recycle_root))
    service = Phase3ActionService(session_factory)
    base = datetime(2026, 4, 10, 11, 0, tzinfo=UTC)
    monkeypatch.setattr(
        "media_manager.app.persistence.phase3_actions._utcnow",
        lambda: base + timedelta(days=8),
    )
    content_id = UUID("b135b1ed-4dc6-4a0d-88d5-81726006507c")
    canonical_instance = UUID("b135b1ed-4dc6-4a0d-88d5-817260065071")
    duplicate_instance = UUID("b135b1ed-4dc6-4a0d-88d5-817260065072")

    recycle_path = (
        recycle_root / "duplicates" / str(content_id) / f"{duplicate_instance}-copy.jpg"
    )

    with session_factory.begin() as session:
        _add_content(session, content_id, "hash-purge-exclude", base)
        session.flush()
        _add_instance(
            session,
            file_instance_id=canonical_instance,
            content_id=content_id,
            absolute_path=str(tmp_path / "library" / "main.jpg"),
            first_seen_at=base,
        )
        _add_instance(
            session,
            file_instance_id=duplicate_instance,
            content_id=content_id,
            absolute_path=str(recycle_path),
            first_seen_at=base + timedelta(seconds=1),
        )
        session.add(
            DuplicateReclaimRecord(
                content_id=content_id,
                reclaim_status=DuplicateReclaimStatus.SCHEDULED_FOR_DELETE.value,
                reviewed_at=base,
                reviewed_by="tester",
                restored_at=None,
                created_at=base,
                updated_at=base,
            )
        )
        session.add(
            DuplicateReclaimItem(
                file_instance_id=duplicate_instance,
                content_id=content_id,
                original_path=str(tmp_path / "library" / "copy.jpg"),
                archive_path=str(recycle_path),
                planned_bin_path=None,
                bin_path=str(recycle_path),
                item_status=DuplicateReclaimItemStatus.RECYCLED.value,
                reclaimed_at=base,
                bin_entered_at=base,
                expires_at=base + timedelta(days=7),
                restore_expires_at=base + timedelta(days=7),
                bin_state=DuplicateBinState.PURGED.value,
                recycle_path=str(recycle_path),
                recycled_at=base,
                purge_after_at=base + timedelta(days=7),
                purged_at=base + timedelta(days=8),
                restored_at=None,
                created_at=base,
                updated_at=base,
            )
        )

    run_id = service._plan_duplicate_purge(file_instance_ids=None)
    assert run_id is not None, "expected non-null run_id from _plan_duplicate_purge"

    with session_factory() as session:
        actions = session.scalars(
            select(PlannedAction).where(PlannedAction.run_id == run_id)
        ).all()
        assert len(actions) == 0, "already-purged item must not be re-planned"


def test_purge_integrity_planner_excludes_already_purged_items(
    session_factory,
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Integrity items with purged_at set must not be re-planned for purge."""
    reclaim_root = tmp_path / "reclaim-root"
    recycle_root = tmp_path / "recycle-bin-root"
    quarantine_root = tmp_path / "quarantine-root"
    monkeypatch.setenv("MEDIA_MANAGER_RECLAIM_ROOT", str(reclaim_root))
    monkeypatch.setenv("MEDIA_MANAGER_RECYCLE_BIN_ROOT", str(recycle_root))
    monkeypatch.setenv("MEDIA_MANAGER_INTEGRITY_QUARANTINE_ROOT", str(quarantine_root))
    service = Phase3ActionService(session_factory)
    base = datetime(2026, 4, 10, 12, 0, tzinfo=UTC)
    monkeypatch.setattr(
        "media_manager.app.persistence.phase3_actions._utcnow",
        lambda: base + timedelta(days=15),
    )
    file_instance_id = UUID("c135b1ed-4dc6-4a0d-88d5-817260065072")
    content_id = UUID("c135b1ed-4dc6-4a0d-88d5-81726006507c")
    check_id = UUID("c135b1ed-4dc6-4a0d-88d5-817260065073")
    check_run_id = UUID("c135b1ed-4dc6-4a0d-88d5-817260065074")

    recycle_path = str(
        recycle_root / "integrity" / f"{file_instance_id}-broken.jpg"
    )

    with session_factory.begin() as session:
        _add_content(session, content_id, "hash-integrity-purge-exclude", base)
        session.flush()
        _add_instance(
            session,
            file_instance_id=file_instance_id,
            content_id=content_id,
            absolute_path=recycle_path,
            first_seen_at=base,
        )
        session.add(
            IntegrityCheckRun(
                id=check_run_id,
                scan_mode="DEEP",
                status="COMPLETED",
                paths=[str(tmp_path / "library")],
                scanned_count=1,
                issues_found=1,
            )
        )
        session.flush()
        session.add(
            IntegrityCheck(
                id=check_id,
                file_instance_id=file_instance_id,
                latest_run_id=check_run_id,
                status="BROKEN",
            )
        )
        session.flush()
        session.add(
            IntegrityQuarantineRecord(
                file_instance_id=file_instance_id,
                check_id=check_id,
                original_path=str(tmp_path / "library" / "broken.jpg"),
                quarantine_path=str(quarantine_root / f"{file_instance_id}-broken.jpg"),
                quarantine_status=IntegrityQuarantineStatus.RECYCLED.value,
                quarantined_at=base,
                expires_at=base + timedelta(days=7),
                recycle_path=recycle_path,
                recycled_at=base + timedelta(days=7),
                purge_after_at=base + timedelta(days=14),
                purged_at=base + timedelta(days=15),
                restored_at=None,
                created_at=base,
                updated_at=base,
            )
        )

    run_id = service._plan_integrity_purge(file_instance_ids=None)
    assert run_id is not None, "expected non-null run_id from _plan_integrity_purge"

    with session_factory() as session:
        actions = session.scalars(
            select(PlannedAction).where(PlannedAction.run_id == run_id)
        ).all()
        assert len(actions) == 0, "already-purged integrity item must not be re-planned"


def test_purge_duplicate_reclaim_is_idempotent_on_repeat(
    session_factory,
    monkeypatch,
    tmp_path: Path,
) -> None:
    reclaim_root = tmp_path / "reclaim-root"
    recycle_root = tmp_path / "recycle-bin-root"
    monkeypatch.setenv("MEDIA_MANAGER_RECLAIM_ROOT", str(reclaim_root))
    monkeypatch.setenv("MEDIA_MANAGER_RECYCLE_BIN_ROOT", str(recycle_root))
    service = Phase3ActionService(session_factory)
    base = datetime(2026, 4, 10, 13, 0, tzinfo=UTC)
    monkeypatch.setattr("media_manager.app.persistence.phase3_actions._utcnow", lambda: base + timedelta(days=8))
    content_id = UUID("d135b1ed-4dc6-4a0d-88d5-81726006507c")
    canonical_instance = UUID("d135b1ed-4dc6-4a0d-88d5-817260065071")
    duplicate_instance = UUID("d135b1ed-4dc6-4a0d-88d5-817260065072")

    recycle_path = recycle_root / "duplicates" / str(content_id) / f"{duplicate_instance}-copy.jpg"
    recycle_path.parent.mkdir(parents=True, exist_ok=True)
    recycle_path.write_bytes(b"copy-data")

    with session_factory.begin() as session:
        _add_content(session, content_id, "hash-purge-repeat-dup", base)
        session.flush()
        _add_instance(
            session,
            file_instance_id=canonical_instance,
            content_id=content_id,
            absolute_path=str(tmp_path / "library" / "main.jpg"),
            first_seen_at=base,
        )
        _add_instance(
            session,
            file_instance_id=duplicate_instance,
            content_id=content_id,
            absolute_path=str(recycle_path),
            first_seen_at=base + timedelta(seconds=1),
        )
        session.add(
            DuplicateReclaimRecord(
                content_id=content_id,
                reclaim_status=DuplicateReclaimStatus.SCHEDULED_FOR_DELETE.value,
                reviewed_at=base,
                reviewed_by="tester",
                restored_at=None,
                created_at=base,
                updated_at=base,
            )
        )
        session.add(
            DuplicateReclaimItem(
                file_instance_id=duplicate_instance,
                content_id=content_id,
                original_path=str(tmp_path / "library" / "copy.jpg"),
                archive_path=str(recycle_path),
                planned_bin_path=None,
                bin_path=str(recycle_path),
                item_status=DuplicateReclaimItemStatus.RECYCLED.value,
                reclaimed_at=base,
                bin_entered_at=base,
                expires_at=base + timedelta(days=7),
                restore_expires_at=base + timedelta(days=7),
                bin_state=DuplicateBinState.IN_BIN.value,
                recycle_path=str(recycle_path),
                recycled_at=base,
                purge_after_at=base + timedelta(days=7),
                purged_at=None,
                restored_at=None,
                created_at=base,
                updated_at=base,
            )
        )

    first = service.purge_duplicate_reclaim(file_instance_ids=[duplicate_instance])
    second = service.purge_duplicate_reclaim(file_instance_ids=[duplicate_instance])

    assert first["summary"]["applied_count"] == 1
    assert second["summary"]["applied_count"] == 0
    assert not recycle_path.exists()
    with session_factory() as session:
        item = session.get(DuplicateReclaimItem, duplicate_instance)
        assert item is not None
        assert item.bin_state == DuplicateBinState.PURGED.value
        assert item.purged_at is not None


def test_purge_integrity_quarantine_is_idempotent_on_repeat(
    session_factory,
    monkeypatch,
    tmp_path: Path,
) -> None:
    reclaim_root = tmp_path / "reclaim-root"
    recycle_root = tmp_path / "recycle-bin-root"
    quarantine_root = tmp_path / "quarantine-root"
    monkeypatch.setenv("MEDIA_MANAGER_RECLAIM_ROOT", str(reclaim_root))
    monkeypatch.setenv("MEDIA_MANAGER_RECYCLE_BIN_ROOT", str(recycle_root))
    monkeypatch.setenv("MEDIA_MANAGER_INTEGRITY_QUARANTINE_ROOT", str(quarantine_root))
    service = Phase3ActionService(session_factory)
    base = datetime(2026, 4, 10, 14, 0, tzinfo=UTC)
    monkeypatch.setattr("media_manager.app.persistence.phase3_actions._utcnow", lambda: base + timedelta(days=15))
    file_instance_id = UUID("e135b1ed-4dc6-4a0d-88d5-817260065072")
    content_id = UUID("e135b1ed-4dc6-4a0d-88d5-81726006507c")
    check_id = UUID("e135b1ed-4dc6-4a0d-88d5-817260065073")
    check_run_id = UUID("e135b1ed-4dc6-4a0d-88d5-817260065074")
    recycle_path = recycle_root / "integrity" / f"{file_instance_id}-broken.jpg"
    recycle_path.parent.mkdir(parents=True, exist_ok=True)
    recycle_path.write_bytes(b"broken")

    with session_factory.begin() as session:
        _add_content(session, content_id, "hash-purge-repeat-int", base)
        session.flush()
        _add_instance(
            session,
            file_instance_id=file_instance_id,
            content_id=content_id,
            absolute_path=str(recycle_path),
            first_seen_at=base,
        )
        session.add(
            IntegrityCheckRun(
                id=check_run_id,
                scan_mode="DEEP",
                status="COMPLETED",
                paths=[str(tmp_path / "library")],
                scanned_count=1,
                issues_found=1,
            )
        )
        session.flush()
        session.add(
            IntegrityCheck(
                id=check_id,
                file_instance_id=file_instance_id,
                latest_run_id=check_run_id,
                status="BROKEN",
            )
        )
        session.flush()
        session.add(
            IntegrityQuarantineRecord(
                file_instance_id=file_instance_id,
                check_id=check_id,
                original_path=str(tmp_path / "library" / "broken.jpg"),
                quarantine_path=str(quarantine_root / f"{file_instance_id}-broken.jpg"),
                quarantine_status=IntegrityQuarantineStatus.RECYCLED.value,
                quarantined_at=base,
                expires_at=base + timedelta(days=7),
                recycle_path=str(recycle_path),
                recycled_at=base + timedelta(days=7),
                purge_after_at=base + timedelta(days=14),
                purged_at=None,
                restored_at=None,
                created_at=base,
                updated_at=base,
            )
        )

    first = service.purge_integrity_quarantine(file_instance_ids=[file_instance_id])
    second = service.purge_integrity_quarantine(file_instance_ids=[file_instance_id])

    assert first["summary"]["applied_count"] == 1
    assert second["summary"]["applied_count"] == 0
    assert not recycle_path.exists()
    with session_factory() as session:
        record = session.get(IntegrityQuarantineRecord, file_instance_id)
        assert record is not None
        assert record.purged_at is not None
        assert record.quarantine_status == IntegrityQuarantineStatus.RECYCLED.value


def test_duplicate_purge_resume_after_post_delete_persist_failure(
    session_factory,
    monkeypatch,
    tmp_path: Path,
) -> None:
    reclaim_root = tmp_path / "reclaim-root"
    recycle_root = tmp_path / "recycle-bin-root"
    monkeypatch.setenv("MEDIA_MANAGER_RECLAIM_ROOT", str(reclaim_root))
    monkeypatch.setenv("MEDIA_MANAGER_RECYCLE_BIN_ROOT", str(recycle_root))
    planner = Phase3ActionService(session_factory)
    base = datetime(2026, 4, 10, 15, 0, tzinfo=UTC)
    monkeypatch.setattr("media_manager.app.persistence.phase3_actions._utcnow", lambda: base + timedelta(days=8))
    content_id = UUID("f135b1ed-4dc6-4a0d-88d5-81726006507c")
    canonical_instance = UUID("f135b1ed-4dc6-4a0d-88d5-817260065071")
    duplicate_instance = UUID("f135b1ed-4dc6-4a0d-88d5-817260065072")
    recycle_path = recycle_root / "duplicates" / str(content_id) / f"{duplicate_instance}-copy.jpg"
    recycle_path.parent.mkdir(parents=True, exist_ok=True)
    recycle_path.write_bytes(b"copy-data")

    with session_factory.begin() as session:
        _add_content(session, content_id, "hash-purge-resume-dup", base)
        session.flush()
        _add_instance(
            session,
            file_instance_id=canonical_instance,
            content_id=content_id,
            absolute_path=str(tmp_path / "library" / "main.jpg"),
            first_seen_at=base,
        )
        _add_instance(
            session,
            file_instance_id=duplicate_instance,
            content_id=content_id,
            absolute_path=str(recycle_path),
            first_seen_at=base + timedelta(seconds=1),
        )
        session.add(
            DuplicateReclaimRecord(
                content_id=content_id,
                reclaim_status=DuplicateReclaimStatus.SCHEDULED_FOR_DELETE.value,
                reviewed_at=base,
                reviewed_by="tester",
                restored_at=None,
                created_at=base,
                updated_at=base,
            )
        )
        session.add(
            DuplicateReclaimItem(
                file_instance_id=duplicate_instance,
                content_id=content_id,
                original_path=str(tmp_path / "library" / "copy.jpg"),
                archive_path=str(recycle_path),
                planned_bin_path=None,
                bin_path=str(recycle_path),
                item_status=DuplicateReclaimItemStatus.RECYCLED.value,
                reclaimed_at=base,
                bin_entered_at=base,
                expires_at=base + timedelta(days=7),
                restore_expires_at=base + timedelta(days=7),
                bin_state=DuplicateBinState.IN_BIN.value,
                recycle_path=str(recycle_path),
                recycled_at=base,
                purge_after_at=base + timedelta(days=7),
                purged_at=None,
                restored_at=None,
                created_at=base,
                updated_at=base,
            )
        )

    run_id = planner._plan_duplicate_purge(file_instance_ids=[duplicate_instance])
    assert run_id is not None
    apply_service = ApplyService(session_factory)
    persist_failed = False
    real_persist = apply_service._persist_applied_action

    def _fail_once(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal persist_failed
        if not persist_failed:
            persist_failed = True
            raise RuntimeError("simulated persist failure after delete")
        return real_persist(*args, **kwargs)

    monkeypatch.setattr(apply_service, "_persist_applied_action", _fail_once)

    with pytest.raises(RuntimeError, match="simulated persist failure after delete"):
        apply_service.apply_run(run_id)

    assert not recycle_path.exists()
    resumed = ApplyService(session_factory).apply_run(run_id)
    assert resumed.applied_count == 1
    with session_factory() as session:
        run = session.get(Run, run_id)
        assert run is not None
        assert run.state == RunStateDB.COMPLETED
        item = session.get(DuplicateReclaimItem, duplicate_instance)
        assert item is not None
        assert item.bin_state == DuplicateBinState.PURGED.value
        assert item.purged_at is not None
        failure = session.scalar(
            select(FailureEvent).where(
                FailureEvent.run_id == run_id,
                FailureEvent.error_code == "APPLY_FAILED",
            )
        )
        assert failure is not None


def test_integrity_purge_resume_after_post_delete_persist_failure(
    session_factory,
    monkeypatch,
    tmp_path: Path,
) -> None:
    reclaim_root = tmp_path / "reclaim-root"
    recycle_root = tmp_path / "recycle-bin-root"
    quarantine_root = tmp_path / "quarantine-root"
    monkeypatch.setenv("MEDIA_MANAGER_RECLAIM_ROOT", str(reclaim_root))
    monkeypatch.setenv("MEDIA_MANAGER_RECYCLE_BIN_ROOT", str(recycle_root))
    monkeypatch.setenv("MEDIA_MANAGER_INTEGRITY_QUARANTINE_ROOT", str(quarantine_root))
    planner = Phase3ActionService(session_factory)
    base = datetime(2026, 4, 10, 16, 0, tzinfo=UTC)
    monkeypatch.setattr("media_manager.app.persistence.phase3_actions._utcnow", lambda: base + timedelta(days=15))
    file_instance_id = UUID("0135b1ed-4dc6-4a0d-88d5-817260065072")
    content_id = UUID("0135b1ed-4dc6-4a0d-88d5-81726006507c")
    check_id = UUID("0135b1ed-4dc6-4a0d-88d5-817260065073")
    check_run_id = UUID("0135b1ed-4dc6-4a0d-88d5-817260065074")
    recycle_path = recycle_root / "integrity" / f"{file_instance_id}-broken.jpg"
    recycle_path.parent.mkdir(parents=True, exist_ok=True)
    recycle_path.write_bytes(b"broken")

    with session_factory.begin() as session:
        _add_content(session, content_id, "hash-purge-resume-int", base)
        session.flush()
        _add_instance(
            session,
            file_instance_id=file_instance_id,
            content_id=content_id,
            absolute_path=str(recycle_path),
            first_seen_at=base,
        )
        session.add(
            IntegrityCheckRun(
                id=check_run_id,
                scan_mode="DEEP",
                status="COMPLETED",
                paths=[str(tmp_path / "library")],
                scanned_count=1,
                issues_found=1,
            )
        )
        session.flush()
        session.add(
            IntegrityCheck(
                id=check_id,
                file_instance_id=file_instance_id,
                latest_run_id=check_run_id,
                status="BROKEN",
            )
        )
        session.flush()
        session.add(
            IntegrityQuarantineRecord(
                file_instance_id=file_instance_id,
                check_id=check_id,
                original_path=str(tmp_path / "library" / "broken.jpg"),
                quarantine_path=str(quarantine_root / f"{file_instance_id}-broken.jpg"),
                quarantine_status=IntegrityQuarantineStatus.RECYCLED.value,
                quarantined_at=base,
                expires_at=base + timedelta(days=7),
                recycle_path=str(recycle_path),
                recycled_at=base + timedelta(days=7),
                purge_after_at=base + timedelta(days=14),
                purged_at=None,
                restored_at=None,
                created_at=base,
                updated_at=base,
            )
        )

    run_id = planner._plan_integrity_purge(file_instance_ids=[file_instance_id])
    assert run_id is not None
    apply_service = ApplyService(session_factory)
    persist_failed = False
    real_persist = apply_service._persist_applied_action

    def _fail_once(*args, **kwargs):  # type: ignore[no-untyped-def]
        nonlocal persist_failed
        if not persist_failed:
            persist_failed = True
            raise RuntimeError("simulated persist failure after delete")
        return real_persist(*args, **kwargs)

    monkeypatch.setattr(apply_service, "_persist_applied_action", _fail_once)

    with pytest.raises(RuntimeError, match="simulated persist failure after delete"):
        apply_service.apply_run(run_id)

    assert not recycle_path.exists()
    resumed = ApplyService(session_factory).apply_run(run_id)
    assert resumed.applied_count == 1
    with session_factory() as session:
        run = session.get(Run, run_id)
        assert run is not None
        assert run.state == RunStateDB.COMPLETED
        record = session.get(IntegrityQuarantineRecord, file_instance_id)
        assert record is not None
        assert record.purged_at is not None
        assert record.quarantine_status == IntegrityQuarantineStatus.RECYCLED.value
        failure = session.scalar(
            select(FailureEvent).where(
                FailureEvent.run_id == run_id,
                FailureEvent.error_code == "APPLY_FAILED",
            )
        )
        assert failure is not None


def test_plan_duplicate_reclaim_reentry_resets_reclaimed_at(
    session_factory,
    monkeypatch,
    tmp_path: Path,
) -> None:
    reclaim_root = tmp_path / "reclaim-root"
    recycle_root = tmp_path / "recycle-bin-root"
    monkeypatch.setenv("MEDIA_MANAGER_RECLAIM_ROOT", str(reclaim_root))
    monkeypatch.setenv("MEDIA_MANAGER_RECYCLE_BIN_ROOT", str(recycle_root))
    service = Phase3ActionService(session_factory)
    base = datetime(2026, 4, 10, 17, 0, tzinfo=UTC)
    now = base + timedelta(minutes=5)
    monkeypatch.setattr("media_manager.app.persistence.phase3_actions._utcnow", lambda: now)

    content_id = UUID("1135b1ed-4dc6-4a0d-88d5-81726006507c")
    canonical_instance = UUID("1135b1ed-4dc6-4a0d-88d5-817260065071")
    duplicate_instance = UUID("1135b1ed-4dc6-4a0d-88d5-817260065072")
    source_path = tmp_path / "library" / "copy.jpg"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_bytes(b"copy")

    with session_factory.begin() as session:
        _add_content(session, content_id, "hash-reentry-dup", base)
        session.flush()
        _add_instance(
            session,
            file_instance_id=canonical_instance,
            content_id=content_id,
            absolute_path=str(tmp_path / "library" / "main.jpg"),
            first_seen_at=base,
        )
        _add_instance(
            session,
            file_instance_id=duplicate_instance,
            content_id=content_id,
            absolute_path=str(source_path),
            first_seen_at=base + timedelta(seconds=1),
        )
        session.flush()
        fc = session.get(FileContent, content_id)
        assert fc is not None
        fc.canonical_file_instance_id = canonical_instance
        session.add(
            DuplicateReclaimRecord(
                content_id=content_id,
                reclaim_status=DuplicateReclaimStatus.REVIEWED_SAFE_TO_RECLAIM.value,
                reviewed_at=base,
                reviewed_by="tester",
                restored_at=None,
                created_at=base,
                updated_at=base,
            )
        )
        session.add(
            DuplicateReclaimItem(
                file_instance_id=duplicate_instance,
                content_id=content_id,
                original_path=str(source_path),
                archive_path=str(recycle_root / "old-copy.jpg"),
                planned_bin_path=None,
                bin_path=None,
                item_status=DuplicateReclaimItemStatus.RECYCLED.value,
                reclaimed_at=base - timedelta(days=30),
                bin_entered_at=base - timedelta(days=30),
                expires_at=base - timedelta(days=15),
                restore_expires_at=base - timedelta(days=15),
                bin_state=DuplicateBinState.PURGED.value,
                recycle_path=None,
                recycled_at=base - timedelta(days=20),
                purge_after_at=base - timedelta(days=10),
                purged_at=base - timedelta(days=9),
                restored_at=base - timedelta(days=8),
                created_at=base - timedelta(days=30),
                updated_at=base - timedelta(days=9),
            )
        )

    result = service._plan_duplicate_reclaim(content_ids=[content_id], retention_days=7)
    assert result["diagnostics"]["planned_action_count"] == 1
    with session_factory() as session:
        item = session.get(DuplicateReclaimItem, duplicate_instance)
        assert item is not None
        assert item.item_status == DuplicateReclaimItemStatus.PENDING.value
        assert item.reclaimed_at is None
        assert item.bin_entered_at is None
        assert item.purged_at is None
        assert item.restored_at is None


def test_plan_integrity_quarantine_reentry_resets_quarantine_timestamps(
    session_factory,
    monkeypatch,
    tmp_path: Path,
) -> None:
    reclaim_root = tmp_path / "reclaim-root"
    recycle_root = tmp_path / "recycle-bin-root"
    quarantine_root = tmp_path / "quarantine-root"
    monkeypatch.setenv("MEDIA_MANAGER_RECLAIM_ROOT", str(reclaim_root))
    monkeypatch.setenv("MEDIA_MANAGER_RECYCLE_BIN_ROOT", str(recycle_root))
    monkeypatch.setenv("MEDIA_MANAGER_INTEGRITY_QUARANTINE_ROOT", str(quarantine_root))
    service = Phase3ActionService(session_factory)
    base = datetime(2026, 4, 10, 18, 0, tzinfo=UTC)
    now = base + timedelta(minutes=5)
    monkeypatch.setattr("media_manager.app.persistence.phase3_actions._utcnow", lambda: now)

    file_instance_id = UUID("2135b1ed-4dc6-4a0d-88d5-817260065072")
    content_id = UUID("2135b1ed-4dc6-4a0d-88d5-81726006507c")
    check_id = UUID("2135b1ed-4dc6-4a0d-88d5-817260065073")
    check_run_id = UUID("2135b1ed-4dc6-4a0d-88d5-817260065074")

    with session_factory.begin() as session:
        _add_content(session, content_id, "hash-reentry-int", base)
        session.flush()
        _add_instance(
            session,
            file_instance_id=file_instance_id,
            content_id=content_id,
            absolute_path=str(tmp_path / "library" / "broken.jpg"),
            first_seen_at=base,
        )
        session.add(
            IntegrityCheckRun(
                id=check_run_id,
                scan_mode="DEEP",
                status="COMPLETED",
                paths=[str(tmp_path / "library")],
                scanned_count=1,
                issues_found=1,
            )
        )
        session.flush()
        session.add(
            IntegrityCheck(
                id=check_id,
                file_instance_id=file_instance_id,
                latest_run_id=check_run_id,
                status="BROKEN",
            )
        )
        session.flush()
        session.add(
            IntegrityQuarantineRecord(
                file_instance_id=file_instance_id,
                check_id=check_id,
                original_path=str(tmp_path / "library" / "broken.jpg"),
                quarantine_path=str(quarantine_root / f"{file_instance_id}-broken.jpg"),
                quarantine_status=IntegrityQuarantineStatus.RECYCLED.value,
                quarantined_at=base - timedelta(days=10),
                expires_at=base - timedelta(days=5),
                recycle_path=str(recycle_root / "integrity" / "old-broken.jpg"),
                recycled_at=base - timedelta(days=8),
                purge_after_at=base - timedelta(days=2),
                purged_at=base - timedelta(days=1),
                restored_at=base - timedelta(days=3),
                created_at=base - timedelta(days=10),
                updated_at=base - timedelta(days=1),
            )
        )

    run_id = service._plan_integrity_quarantine(check_id=check_id)
    assert run_id is not None
    with session_factory() as session:
        record = session.get(IntegrityQuarantineRecord, file_instance_id)
        assert record is not None
        assert record.quarantine_status == IntegrityQuarantineStatus.PENDING.value
        assert record.quarantined_at is None
        assert record.restored_at is None
        assert record.purged_at is None
