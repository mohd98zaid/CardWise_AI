"""Tests verifying local-only deployment configuration and Alembic migration lifecycle."""

import os
import sqlite3
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import Settings
from app.core.ratelimit import get_client_ip, reset_rate_limits


def test_local_only_defaults() -> None:
    """Verify application defaults to local-only 127.0.0.1 and SQLite."""
    s = Settings()
    assert s.host == "127.0.0.1"
    assert s.port == 8000
    assert "sqlite" in s.database_url
    assert s.app_env in {"development", "test", "local"}


def test_migration_fresh_sqlite_database_lifecycle() -> None:
    """Verify that a fresh SQLite database runs all migrations without duplicate column errors."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        backend_dir = Path(__file__).resolve().parents[2]
        ini_path = backend_dir / "alembic.ini"
        cfg = Config(str(ini_path))
        cfg.set_main_option("script_location", str(backend_dir / "migrations"))
        # Force the migration runner to target the temp database
        db_url = f"sqlite:///{db_path.replace('\\', '/')}"
        cfg.set_main_option("sqlalchemy.url", db_url)
        os.environ["DATABASE_URL"] = db_url

        # 1. Upgrade from empty to head
        command.upgrade(cfg, "head")

        # 2. Inspect sqlite schema directly
        con = sqlite3.connect(db_path)
        tables = [
            r[0]
            for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        ]
        assert "scenario_spend" in tables
        assert "rule_test_cases" in tables
        assert "calculation_trace_steps" in tables

        cols = [r[1] for r in con.execute("PRAGMA table_info(scenario_spend)").fetchall()]
        assert "point_value_per_point" in cols

        # 3. Test downgrade to 0003
        command.downgrade(cfg, "0003_calculation_trace_steps")
        cols_after_downgrade = [
            r[1] for r in con.execute("PRAGMA table_info(scenario_spend)").fetchall()
        ]
        assert "point_value_per_point" not in cols_after_downgrade

        # 4. Test re-upgrade from 0003 to 0004 (upgrade from previous schema)
        command.upgrade(cfg, "head")
        cols_after_reupgrade = [
            r[1] for r in con.execute("PRAGMA table_info(scenario_spend)").fetchall()
        ]
        assert "point_value_per_point" in cols_after_reupgrade
        con.close()
    finally:
        os.environ.pop("DATABASE_URL", None)
        try:
            os.remove(db_path)
        except OSError:
            pass


def test_in_memory_rate_limiting_local_only() -> None:
    """Verify in-memory rate limiting works cleanly for local development."""
    reset_rate_limits()

    class MockRequest:
        def __init__(self, ip: str) -> None:
            from unittest.mock import MagicMock
            self.client = MagicMock(host=ip)
            self.headers = {}

    req = MockRequest("127.0.0.1")
    assert get_client_ip(req) == "127.0.0.1"
