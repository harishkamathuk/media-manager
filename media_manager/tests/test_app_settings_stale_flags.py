from __future__ import annotations

from pathlib import Path


def test_media_manager_ui_v2_enabled_has_no_runtime_python_references() -> None:
    runtime_root = Path("media_manager/app")
    hits = []
    for candidate in runtime_root.rglob("*.py"):
        if "MEDIA_MANAGER_UI_V2_ENABLED" in candidate.read_text(encoding="utf-8"):
            hits.append(str(candidate))

    assert hits == []
