from __future__ import annotations

from pathlib import Path

from core.config.models import CodeCounsilConfig
from core.discovery.discover import discover_project
from core.manifest.manifest import ExecutionManifest
from core.selection.selector import select_specialists


def make_manifest(tmp_path: Path) -> ExecutionManifest:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return ExecutionManifest(workspace=workspace, mode="full", target_repo=tmp_path, config_hash="sha256:test", effective_config={})


def test_database_reviewer_selected_when_databases_present(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    selected = select_specialists(
        "full",
        {"databases": ["postgres"], "database_signals": {"has_manual_migrations": False, "dev_prod_mismatch": False}},
        CodeCounsilConfig(),
        manifest,
    )
    assert "database" in selected


def test_database_reviewer_excluded_when_no_databases(tmp_path: Path) -> None:
    manifest = make_manifest(tmp_path)
    selected = select_specialists(
        "full",
        {"databases": [], "database_signals": {"has_manual_migrations": False, "dev_prod_mismatch": False}},
        CodeCounsilConfig(),
        manifest,
    )
    assert "database" not in selected


def test_discovery_detects_alembic(tmp_path: Path) -> None:
    (tmp_path / "alembic.ini").write_text("[alembic]\nscript_location = migrations\n", encoding="utf-8")
    (tmp_path / "migrations").mkdir()
    (tmp_path / "migrations" / "env.py").write_text("from sqlalchemy import create_engine\n", encoding="utf-8")
    (tmp_path / "settings.py").write_text("DATABASE_URL = 'postgresql://db/app'\n", encoding="utf-8")

    ctx = discover_project(tmp_path)

    assert ctx["database_signals"]["migration_tool"] == "alembic"
    assert sorted(ctx["database_signals"]["migration_tool_files"]) == ["alembic.ini", "migrations/env.py"]


def test_discovery_detects_manual_migrations(tmp_path: Path) -> None:
    (tmp_path / "settings.py").write_text("DATABASE_URL = 'postgresql://db/app'\n", encoding="utf-8")

    ctx = discover_project(tmp_path)

    assert ctx["database_signals"]["migration_tool"] == "manual"
    assert ctx["database_signals"]["has_manual_migrations"] is True


def test_discovery_detects_dev_prod_mismatch(tmp_path: Path) -> None:
    (tmp_path / "docker-compose.yml").write_text("services:\n  db:\n    image: postgres:16\n", encoding="utf-8")
    (tmp_path / "settings.py").write_text("DATABASE_URL = 'sqlite:///dev.db'\n", encoding="utf-8")

    ctx = discover_project(tmp_path)

    assert "postgres" in ctx["databases"]
    assert "sqlite" in ctx["databases"]
    assert ctx["database_signals"]["dev_prod_mismatch"] is True
