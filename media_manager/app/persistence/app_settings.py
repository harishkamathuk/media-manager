"""Durable app settings foundation and narrow runtime dual-read helpers."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from sqlalchemy import update
from sqlalchemy.orm import Session, sessionmaker

from media_manager.app.canonical.factory import resolve_default_policy_name
from media_manager.app.core.config import REQUIRED_METADATA_CODES, load_environment, resolve_storage_roots
from media_manager.app.core.errors import AppSettingsValidationError, AppSettingsVersionConflictError
from media_manager.app.persistence.base import transactional_session
from media_manager.app.persistence.models import AppSetting, AppSettingHistory

ValueType = Literal["bool", "string", "string_list", "enum", "path", "float", "int"]

CANONICAL_POLICY_VALUES = frozenset({"FIRST_SEEN", "PREFER_ROOT", "EXIF_FILENAME_FALLBACK", "SHORTEST_PATH"})
BENCHMARK_WORKER_MODE_VALUES = frozenset({"forever", "once"})
DB_RESET_CHALLENGE_WORD_DEFAULT = "media-manager"
TRUTHY_VALUES = frozenset({"1", "true", "yes", "on"})
RUNTIME_DUAL_READ_KEYS = frozenset(
    {
        "video_thumbnails_enabled",
        "video_thumbnail_cache_dir",
        "canonical_read_cache_enabled",
        "canonical_read_cache_ttl_seconds",
        "metadata_upsert_batch_size",
        "benchmark_worker_mode",
        "benchmark_poll_interval_seconds",
    }
)


@dataclass(frozen=True)
class AppSettingDefinition:
    key: str
    env_var: str
    value_type: ValueType
    category: str
    is_sensitive: bool = False


@dataclass(frozen=True)
class AppSettingSnapshot:
    key: str
    value: bool | str | float | int | list[str]
    value_json: dict[str, object]
    value_type: str
    category: str
    scope: str
    is_sensitive: bool
    updated_by: str
    updated_at: datetime
    version: int
    source: str


@dataclass(frozen=True)
class BootstrapResult:
    inserted_keys: tuple[str, ...]
    skipped_keys: tuple[str, ...]


_CATALOG: dict[str, AppSettingDefinition] = {
    "required_metadata_codes": AppSettingDefinition(
        key="required_metadata_codes",
        env_var="MEDIA_REQUIRED_CODES",
        value_type="string_list",
        category="policy",
    ),
    "canonical_policy": AppSettingDefinition(
        key="canonical_policy",
        env_var="MEDIA_CANONICAL_POLICY",
        value_type="enum",
        category="policy",
    ),
    "preferred_roots": AppSettingDefinition(
        key="preferred_roots",
        env_var="MEDIA_PREFERRED_ROOTS",
        value_type="string_list",
        category="policy",
    ),
    "tag_normalization_remove_punctuation": AppSettingDefinition(
        key="tag_normalization_remove_punctuation",
        env_var="MEDIA_MANAGER_TAG_NORMALIZATION_REMOVE_PUNCTUATION",
        value_type="bool",
        category="policy",
    ),
    "canonical_storage_path": AppSettingDefinition(
        key="canonical_storage_path",
        env_var="MEDIA_CANONICAL_STORAGE_PATH",
        value_type="path",
        category="storage",
    ),
    "duplicate_storage_path": AppSettingDefinition(
        key="duplicate_storage_path",
        env_var="MEDIA_DUPLICATE_STORAGE_PATH",
        value_type="path",
        category="storage",
    ),
    "video_thumbnail_cache_dir": AppSettingDefinition(
        key="video_thumbnail_cache_dir",
        env_var="MEDIA_MANAGER_VIDEO_THUMBNAIL_CACHE_DIR",
        value_type="path",
        category="storage",
    ),
    "directory_picker_enabled": AppSettingDefinition(
        key="directory_picker_enabled",
        env_var="MEDIA_MANAGER_DIRECTORY_PICKER_ENABLED",
        value_type="bool",
        category="ui",
    ),
    "directory_picker_roots": AppSettingDefinition(
        key="directory_picker_roots",
        env_var="MEDIA_MANAGER_DIRECTORY_PICKER_ROOTS",
        value_type="string_list",
        category="ui",
    ),
    "video_thumbnails_enabled": AppSettingDefinition(
        key="video_thumbnails_enabled",
        env_var="MEDIA_MANAGER_VIDEO_THUMBNAILS_ENABLED",
        value_type="bool",
        category="ui",
    ),
    "benchmarks_enabled": AppSettingDefinition(
        key="benchmarks_enabled",
        env_var="MEDIA_MANAGER_BENCHMARKS_ENABLED",
        value_type="bool",
        category="ui",
    ),
    "allow_planner_mv_reads": AppSettingDefinition(
        key="allow_planner_mv_reads",
        env_var="MEDIA_MANAGER_ALLOW_PLANNER_MV_READS",
        value_type="bool",
        category="ui",
    ),
    "canonical_read_cache_enabled": AppSettingDefinition(
        key="canonical_read_cache_enabled",
        env_var="CANONICAL_READ_CACHE_ENABLED",
        value_type="bool",
        category="performance",
    ),
    "canonical_read_cache_ttl_seconds": AppSettingDefinition(
        key="canonical_read_cache_ttl_seconds",
        env_var="CANONICAL_READ_CACHE_TTL_SECONDS",
        value_type="float",
        category="performance",
    ),
    "metadata_upsert_batch_size": AppSettingDefinition(
        key="metadata_upsert_batch_size",
        env_var="METADATA_UPSERT_BATCH_SIZE",
        value_type="int",
        category="performance",
    ),
    "benchmark_max_items": AppSettingDefinition(
        key="benchmark_max_items",
        env_var="MEDIA_MANAGER_BENCHMARK_MAX_ITEMS",
        value_type="int",
        category="performance",
    ),
    "benchmark_poll_interval_seconds": AppSettingDefinition(
        key="benchmark_poll_interval_seconds",
        env_var="MEDIA_MANAGER_BENCHMARK_POLL_INTERVAL_SECONDS",
        value_type="float",
        category="performance",
    ),
    "benchmark_stale_after_seconds": AppSettingDefinition(
        key="benchmark_stale_after_seconds",
        env_var="MEDIA_MANAGER_BENCHMARK_STALE_AFTER_SECONDS",
        value_type="float",
        category="performance",
    ),
    "benchmark_worker_mode": AppSettingDefinition(
        key="benchmark_worker_mode",
        env_var="MEDIA_MANAGER_BENCHMARK_WORKER_MODE",
        value_type="enum",
        category="performance",
    ),
    "db_reset_include_dynamic": AppSettingDefinition(
        key="db_reset_include_dynamic",
        env_var="MEDIA_MANAGER_DB_RESET_INCLUDE_DYNAMIC",
        value_type="bool",
        category="admin_safety",
    ),
    "db_reset_challenge_word": AppSettingDefinition(
        key="db_reset_challenge_word",
        env_var="MEDIA_MANAGER_DB_RESET_CHALLENGE_WORD",
        value_type="string",
        category="admin_safety",
        is_sensitive=True,
    ),
}


def _truthy(raw: str) -> bool:
    return raw.strip().lower() in TRUTHY_VALUES


def _split_csv_preserve_order(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def _normalize_string_list(value: list[str] | tuple[str, ...]) -> list[str]:
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise AppSettingsValidationError("string_list settings must contain strings only.")
        cleaned = item.strip()
        if cleaned:
            normalized.append(cleaned)
    return normalized


def _normalize_path_string(raw: str, *, field_name: str) -> str:
    value = str(raw).strip()
    if not value:
        raise AppSettingsValidationError(f"{field_name} must not be empty.")
    expanded = str(Path(value).expanduser())
    if not Path(expanded).is_absolute():
        raise AppSettingsValidationError(f"{field_name} must be an absolute path.")
    return expanded


class AppSettingsService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def definition_for(key: str) -> AppSettingDefinition:
        definition = _CATALOG.get(key)
        if definition is None:
            raise AppSettingsValidationError(f"Unknown app setting key: {key}")
        return definition

    def get_setting(self, key: str, *, session: Session | None = None) -> AppSettingSnapshot | None:
        definition = self.definition_for(key)
        if session is not None:
            row = session.get(AppSetting, key)
            return None if row is None else self._snapshot_from_row(row, definition)
        with self._session_factory() as local_session:
            row = local_session.get(AppSetting, key)
            return None if row is None else self._snapshot_from_row(row, definition)

    def set_value(
        self,
        key: str,
        value: object,
        *,
        updated_by: str,
        source: str,
        expected_version: int = 0,
        reason: str | None = None,
    ) -> AppSettingSnapshot:
        definition = self.definition_for(key)
        normalized = self._normalize_value(definition, value)
        payload = {"value": normalized}

        with transactional_session(self._session_factory) as session:
            existing = session.get(AppSetting, key)
            if existing is None:
                if int(expected_version) != 0:
                    raise AppSettingsVersionConflictError(
                        f"App setting version conflict for {key}: expected 0, current missing."
                    )
                row = AppSetting(
                    key=key,
                    value_json=payload,
                    value_type=definition.value_type,
                    category=definition.category,
                    scope="global",
                    is_sensitive=definition.is_sensitive,
                    updated_by=updated_by,
                    source=source,
                )
                session.add(row)
                session.flush()
                session.add(
                    AppSettingHistory(
                        key=key,
                        old_value_json=None,
                        new_value_json=payload,
                        changed_by=updated_by,
                        reason=reason,
                        source=source,
                    )
                )
                session.flush()
                return self._snapshot_from_row(row, definition)

            old_value_json = dict(existing.value_json)
            stmt = (
                update(AppSetting)
                .where(AppSetting.key == key, AppSetting.version == int(expected_version))
                .values(
                    value_json=payload,
                    value_type=definition.value_type,
                    category=definition.category,
                    scope="global",
                    is_sensitive=definition.is_sensitive,
                    updated_by=updated_by,
                    updated_at=datetime.now(timezone.utc),
                    source=source,
                    version=AppSetting.version + 1,
                )
            )
            result = session.execute(stmt)
            if result.rowcount != 1:
                raise AppSettingsVersionConflictError(
                    f"App setting version conflict for {key}: expected {expected_version}, current {existing.version}."
                )
            session.add(
                AppSettingHistory(
                    key=key,
                    old_value_json=old_value_json,
                    new_value_json=payload,
                    changed_by=updated_by,
                    reason=reason,
                    source=source,
                )
            )
            session.flush()
            updated = session.get(AppSetting, key)
            if updated is None:  # pragma: no cover - defensive integrity guard
                raise RuntimeError(f"Updated app setting disappeared unexpectedly: {key}")
            return self._snapshot_from_row(updated, definition)

    def bootstrap_from_env(self) -> BootstrapResult:
        inserted: list[str] = []
        skipped: list[str] = []
        load_environment()

        with transactional_session(self._session_factory) as session:
            for key, definition in _CATALOG.items():
                if session.get(AppSetting, key) is not None:
                    skipped.append(key)
                    continue
                value = self._parse_env_value(definition, strict=True)
                payload = {"value": value}
                session.add(
                    AppSetting(
                        key=key,
                        value_json=payload,
                        value_type=definition.value_type,
                        category=definition.category,
                        scope="global",
                        is_sensitive=definition.is_sensitive,
                        updated_by="system:bootstrap_env",
                        source="bootstrap_env",
                    )
                )
                session.add(
                    AppSettingHistory(
                        key=key,
                        old_value_json=None,
                        new_value_json=payload,
                        changed_by="system:bootstrap_env",
                        reason=None,
                        source="bootstrap_env",
                    )
                )
                inserted.append(key)

        return BootstrapResult(inserted_keys=tuple(inserted), skipped_keys=tuple(skipped))

    def resolve_runtime_value(
        self,
        key: str,
        *,
        logger: logging.Logger | None = None,
        session: Session | None = None,
    ) -> bool | str | float | int | list[str]:
        if key not in RUNTIME_DUAL_READ_KEYS:
            raise AppSettingsValidationError(f"{key} is not enabled for runtime dual-read in this slice.")
        definition = self.definition_for(key)
        snapshot = self.get_setting(key, session=session)
        if snapshot is not None:
            return snapshot.value
        if logger is not None:
            logger.warning(
                "App setting missing in DB; using environment fallback",
                extra={"app_setting_key": key, "fallback_source": "env"},
            )
        return self._parse_env_value(definition, strict=False)

    def _snapshot_from_row(self, row: AppSetting, definition: AppSettingDefinition) -> AppSettingSnapshot:
        return AppSettingSnapshot(
            key=row.key,
            value=self._normalize_value(definition, row.value_json.get("value")),
            value_json=row.value_json,
            value_type=row.value_type,
            category=row.category,
            scope=row.scope,
            is_sensitive=bool(row.is_sensitive),
            updated_by=row.updated_by,
            updated_at=row.updated_at,
            version=int(row.version),
            source=row.source,
        )

    def _normalize_value(self, definition: AppSettingDefinition, value: object) -> bool | str | float | int | list[str]:
        key = definition.key
        if definition.value_type == "bool":
            if not isinstance(value, bool):
                raise AppSettingsValidationError(f"{key} must be a boolean.")
            return value
        if definition.value_type == "string":
            normalized = str(value).strip()
            if not normalized:
                raise AppSettingsValidationError(f"{key} must not be empty.")
            return normalized
        if definition.value_type == "string_list":
            if not isinstance(value, (list, tuple)):
                raise AppSettingsValidationError(f"{key} must be a list of strings.")
            if key == "required_metadata_codes":
                return [item.upper() for item in _normalize_string_list(list(value))]
            return _normalize_string_list(list(value))
        if definition.value_type == "path":
            return _normalize_path_string(str(value), field_name=key)
        if definition.value_type == "float":
            try:
                parsed = float(value)
            except (TypeError, ValueError) as exc:
                raise AppSettingsValidationError(f"{key} must be a float.") from exc
            if key in {
                "canonical_read_cache_ttl_seconds",
                "benchmark_poll_interval_seconds",
                "benchmark_stale_after_seconds",
            } and parsed <= 0:
                raise AppSettingsValidationError(f"{key} must be > 0.")
            return float(parsed)
        if definition.value_type == "int":
            try:
                parsed = int(value)
            except (TypeError, ValueError) as exc:
                raise AppSettingsValidationError(f"{key} must be an integer.") from exc
            if key == "metadata_upsert_batch_size":
                return min(max(parsed, 1), 50_000)
            if key in {"benchmark_max_items"} and parsed <= 0:
                raise AppSettingsValidationError(f"{key} must be > 0.")
            return int(parsed)
        if definition.value_type == "enum":
            normalized = str(value).strip()
            if key == "canonical_policy":
                normalized = normalized.upper()
                if normalized not in CANONICAL_POLICY_VALUES:
                    raise AppSettingsValidationError(
                        "canonical_policy must be one of FIRST_SEEN, PREFER_ROOT, EXIF_FILENAME_FALLBACK, SHORTEST_PATH."
                    )
                return normalized
            if key == "benchmark_worker_mode":
                normalized = normalized.lower()
                if normalized not in BENCHMARK_WORKER_MODE_VALUES:
                    raise AppSettingsValidationError("benchmark_worker_mode must be forever or once.")
                return normalized
        raise AppSettingsValidationError(f"Unsupported app setting type for {key}: {definition.value_type}")

    def _parse_env_value(self, definition: AppSettingDefinition, *, strict: bool) -> bool | str | float | int | list[str]:
        load_environment()
        key = definition.key
        env_name = definition.env_var
        raw = os.getenv(env_name)
        cleaned = (raw or "").strip()

        if key == "required_metadata_codes":
            values = [item.upper() for item in _split_csv_preserve_order(cleaned)] if cleaned else list(REQUIRED_METADATA_CODES)
            return values or list(REQUIRED_METADATA_CODES)
        if key == "canonical_policy":
            return self._normalize_value(definition, resolve_default_policy_name())
        if key in {"preferred_roots", "directory_picker_roots"}:
            return _split_csv_preserve_order(cleaned) if cleaned else []
        if key == "tag_normalization_remove_punctuation":
            return _truthy(cleaned or "0")
        if key == "canonical_storage_path":
            return str(resolve_storage_roots().canonical_root)
        if key == "duplicate_storage_path":
            return str(resolve_storage_roots().duplicate_root)
        if key == "video_thumbnail_cache_dir":
            path_value = cleaned if cleaned else str(Path(tempfile.gettempdir()) / "media-manager" / "video-thumbnails")
            return _normalize_path_string(path_value, field_name=key)
        if key in {
            "directory_picker_enabled",
            "video_thumbnails_enabled",
            "benchmarks_enabled",
            "allow_planner_mv_reads",
            "canonical_read_cache_enabled",
            "db_reset_include_dynamic",
        }:
            default = "false"
            return _truthy(cleaned or default)
        if key == "db_reset_challenge_word":
            return cleaned or DB_RESET_CHALLENGE_WORD_DEFAULT
        if key == "canonical_read_cache_ttl_seconds":
            return self._parse_float_env(key, cleaned, default=30.0, strict=strict, positive=True, fallback_on_invalid=30.0)
        if key == "metadata_upsert_batch_size":
            return self._parse_int_env(key, cleaned, default=1000, strict=strict, clamp=(1, 50_000), positive=False)
        if key == "benchmark_max_items":
            return self._parse_int_env(key, cleaned, default=10_000, strict=strict, clamp=None, positive=True)
        if key == "benchmark_poll_interval_seconds":
            return self._parse_float_env(key, cleaned, default=2.0, strict=strict, positive=strict, fallback_on_invalid=None)
        if key == "benchmark_stale_after_seconds":
            if strict:
                return self._parse_float_env(key, cleaned, default=900.0, strict=True, positive=True, fallback_on_invalid=None)
            value = self._parse_float_env(key, cleaned, default=900.0, strict=False, positive=False, fallback_on_invalid=None)
            return max(1.0, value)
        if key == "benchmark_worker_mode":
            if strict:
                return self._normalize_value(definition, cleaned or "forever")
            normalized = (cleaned or "forever").strip().lower()
            return "once" if normalized == "once" else "forever"
        raise AppSettingsValidationError(f"No env parser configured for {key}.")

    def _parse_float_env(
        self,
        key: str,
        raw: str,
        *,
        default: float,
        strict: bool,
        positive: bool,
        fallback_on_invalid: float | None,
    ) -> float:
        if not raw:
            return float(default)
        try:
            value = float(raw)
        except ValueError as exc:
            if strict:
                raise AppSettingsValidationError(f"{key} must be a valid float.") from exc
            if fallback_on_invalid is not None:
                return float(fallback_on_invalid)
            raise
        if positive and value <= 0:
            if strict:
                raise AppSettingsValidationError(f"{key} must be > 0.")
            if fallback_on_invalid is not None:
                return float(fallback_on_invalid)
        return float(value)

    def _parse_int_env(
        self,
        key: str,
        raw: str,
        *,
        default: int,
        strict: bool,
        clamp: tuple[int, int] | None,
        positive: bool,
    ) -> int:
        if not raw:
            value = int(default)
        else:
            try:
                value = int(raw)
            except ValueError as exc:
                if strict:
                    raise AppSettingsValidationError(f"{key} must be a valid integer.") from exc
                return int(default)
        if positive and value <= 0:
            raise AppSettingsValidationError(f"{key} must be > 0.")
        if clamp is not None:
            low, high = clamp
            value = min(max(value, low), high)
        return int(value)


def bootstrap_app_settings_from_env(session_factory: sessionmaker[Session]) -> BootstrapResult:
    return AppSettingsService(session_factory).bootstrap_from_env()


def render_bootstrap_result(result: BootstrapResult) -> str:
    return json.dumps(
        {
            "inserted_keys": list(result.inserted_keys),
            "skipped_keys": list(result.skipped_keys),
        },
        indent=2,
        sort_keys=False,
    )
