"""add app settings foundation tables

Revision ID: 0033_app_settings_pilot
Revises: 0032_drop_duplicate_reclaim_record_legacy_columns
Create Date: 2026-04-03 12:00:00
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0033_app_settings_pilot"
down_revision = "0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value_json JSONB NOT NULL,
            value_type TEXT NOT NULL,
            category TEXT NOT NULL,
            scope TEXT NOT NULL DEFAULT 'global',
            is_sensitive BOOLEAN NOT NULL DEFAULT false,
            updated_by TEXT NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            version BIGINT NOT NULL DEFAULT 1,
            source TEXT NOT NULL DEFAULT 'api'
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings_history (
            id BIGSERIAL PRIMARY KEY,
            key TEXT NOT NULL,
            old_value_json JSONB NULL,
            new_value_json JSONB NOT NULL,
            changed_by TEXT NOT NULL,
            changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            reason TEXT NULL,
            source TEXT NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_app_settings_category ON app_settings (category)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_app_settings_updated_at ON app_settings (updated_at DESC)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_app_settings_history_key_time "
        "ON app_settings_history (key, changed_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_app_settings_history_key_time")
    op.execute("DROP INDEX IF EXISTS idx_app_settings_updated_at")
    op.execute("DROP INDEX IF EXISTS idx_app_settings_category")
    op.execute("DROP TABLE IF EXISTS app_settings_history")
    op.execute("DROP TABLE IF EXISTS app_settings")
