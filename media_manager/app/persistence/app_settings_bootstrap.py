"""Bootstrap current env-backed settings into durable app_settings."""

from __future__ import annotations

from media_manager.app.persistence.app_settings import bootstrap_app_settings_from_env, render_bootstrap_result
from media_manager.app.persistence.base import create_db_engine, create_session_factory


def main() -> None:
    engine = create_db_engine()
    session_factory = create_session_factory(engine)
    try:
        result = bootstrap_app_settings_from_env(session_factory)
        print(render_bootstrap_result(result))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
