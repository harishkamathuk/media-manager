from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from media_manager.app.persistence.models import (
    DuplicateBinState,
    DuplicateReclaimItem,
    DuplicateReclaimItemStatus,
    DuplicateReclaimRecord,
    DuplicateReclaimStatus,
    FileContent,
    FileInstance,
    FileInstanceStatus,
    IntegrityCheck,
    IntegrityCheckRun,
    IntegrityQuarantineRecord,
    IntegrityQuarantineStatus,
    PlannedAction,
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

    with session_factory() as session:
        actions = session.scalars(
            select(PlannedAction).where(PlannedAction.run_id == run_id)
        ).all()
        assert len(actions) == 0, "already-purged integrity item must not be re-planned"


def test_duplicate_replan_resets_purged_at(
    session_factory,
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Re-planning a previously-purged duplicate item must reset purged_at so it
    can be purged again after the next recycle cycle."""
    reclaim_root = tmp_path / "reclaim-root"
    recycle_root = tmp_path / "recycle-bin-root"
    monkeypatch.setenv("MEDIA_MANAGER_RECLAIM_ROOT", str(reclaim_root))
    monkeypatch.setenv("MEDIA_MANAGER_RECYCLE_BIN_ROOT", str(recycle_root))
    service = Phase3ActionService(session_factory)
    base = datetime(2026, 4, 10, 13, 0, tzinfo=UTC)
    monkeypatch.setattr(
        "media_manager.app.persistence.phase3_actions._utcnow",
        lambda: base,
    )
    content_id = UUID("d135b1ed-4dc6-4a0d-88d5-81726006507c")
    canonical_instance = UUID("d135b1ed-4dc6-4a0d-88d5-817260065071")
    duplicate_instance = UUID("d135b1ed-4dc6-4a0d-88d5-817260065072")

    source_path = str(tmp_path / "library" / "copy.jpg")
    Path(source_path).parent.mkdir(parents=True, exist_ok=True)
    Path(source_path).write_bytes(b"dup-data")

    with session_factory.begin() as session:
        _add_content(session, content_id, "hash-replan-dup", base)
        session.flush()
        # Set canonical_file_instance_id on FileContent
        from media_manager.app.persistence.models import FileContent as FC

        fc = session.get(FC, content_id)
        fc.canonical_file_instance_id = canonical_instance
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
            absolute_path=source_path,
            first_seen_at=base + timedelta(seconds=1),
        )
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
        # Pre-existing purged item row
        session.add(
            DuplicateReclaimItem(
                file_instance_id=duplicate_instance,
                content_id=content_id,
                original_path=source_path,
                archive_path=str(recycle_root / "old-archive.jpg"),
                planned_bin_path=None,
                bin_path=None,
                item_status=DuplicateReclaimItemStatus.RECYCLED.value,
                reclaimed_at=base - timedelta(days=30),
                bin_entered_at=base - timedelta(days=30),
                expires_at=base - timedelta(days=16),
                restore_expires_at=base - timedelta(days=16),
                bin_state=DuplicateBinState.PURGED.value,
                recycle_path=None,
                recycled_at=base - timedelta(days=16),
                purge_after_at=base - timedelta(days=9),
                purged_at=base - timedelta(days=9),
                restored_at=None,
                created_at=base - timedelta(days=30),
                updated_at=base - timedelta(days=9),
            )
        )

    service._plan_duplicate_reclaim(content_ids=[content_id], retention_days=14)

    with session_factory() as session:
        item = session.get(DuplicateReclaimItem, duplicate_instance)
        assert item is not None
        assert item.purged_at is None, "purged_at must be reset on re-plan"
        assert item.bin_state == DuplicateBinState.PENDING_MOVE.value
        assert item.item_status == DuplicateReclaimItemStatus.PENDING.value


def test_integrity_replan_resets_purged_at(
    session_factory,
    monkeypatch,
    tmp_path: Path,
) -> None:
    """Re-planning a previously-purged integrity quarantine record must reset
    purged_at so it can be purged again after the next recycle cycle."""
    reclaim_root = tmp_path / "reclaim-root"
    recycle_root = tmp_path / "recycle-bin-root"
    quarantine_root = tmp_path / "quarantine-root"
    monkeypatch.setenv("MEDIA_MANAGER_RECLAIM_ROOT", str(reclaim_root))
    monkeypatch.setenv("MEDIA_MANAGER_RECYCLE_BIN_ROOT", str(recycle_root))
    monkeypatch.setenv("MEDIA_MANAGER_INTEGRITY_QUARANTINE_ROOT", str(quarantine_root))
    service = Phase3ActionService(session_factory)
    base = datetime(2026, 4, 10, 14, 0, tzinfo=UTC)
    monkeypatch.setattr(
        "media_manager.app.persistence.phase3_actions._utcnow",
        lambda: base,
    )
    file_instance_id = UUID("e135b1ed-4dc6-4a0d-88d5-817260065072")
    content_id = UUID("e135b1ed-4dc6-4a0d-88d5-81726006507c")
    check_id = UUID("e135b1ed-4dc6-4a0d-88d5-817260065073")
    check_run_id = UUID("e135b1ed-4dc6-4a0d-88d5-817260065074")

    source_path = str(tmp_path / "library" / "broken.jpg")
    Path(source_path).parent.mkdir(parents=True, exist_ok=True)
    Path(source_path).write_bytes(b"broken-data")

    with session_factory.begin() as session:
        _add_content(session, content_id, "hash-integrity-replan", base)
        session.flush()
        _add_instance(
            session,
            file_instance_id=file_instance_id,
            content_id=content_id,
            absolute_path=source_path,
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
        # Pre-existing purged quarantine record
        session.add(
            IntegrityQuarantineRecord(
                file_instance_id=file_instance_id,
                check_id=check_id,
                original_path=source_path,
                quarantine_path=str(quarantine_root / f"{file_instance_id}-broken.jpg"),
                quarantine_status=IntegrityQuarantineStatus.RECYCLED.value,
                quarantined_at=base - timedelta(days=30),
                expires_at=base - timedelta(days=16),
                recycle_path=str(recycle_root / "integrity" / f"{file_instance_id}-broken.jpg"),
                recycled_at=base - timedelta(days=16),
                purge_after_at=base - timedelta(days=9),
                purged_at=base - timedelta(days=9),
                restored_at=None,
                created_at=base - timedelta(days=30),
                updated_at=base - timedelta(days=9),
            )
        )

    service._plan_integrity_quarantine(check_id=check_id)

    with session_factory() as session:
        record = session.get(IntegrityQuarantineRecord, file_instance_id)
        assert record is not None
        assert record.purged_at is None, "purged_at must be reset on re-plan"
        assert record.quarantine_status == IntegrityQuarantineStatus.PENDING.value
