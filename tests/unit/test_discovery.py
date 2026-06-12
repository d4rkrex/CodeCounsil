from __future__ import annotations

from pathlib import Path

import pytest

from core.discovery.discover import discover_project


@pytest.fixture()
def python_only_repo(tmp_path: Path) -> Path:
    """A minimal Python project with no frontend, no AI libraries."""
    (tmp_path / "app.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/health')\ndef health(): return {'ok': True}\n"
    )
    (tmp_path / "requirements.txt").write_text("fastapi>=0.100\npydantic>=2.0\n")
    return tmp_path


@pytest.fixture()
def docs_with_framework_names(tmp_path: Path) -> Path:
    """
    A Python project whose documentation mentions many frameworks.
    CC-ARCH-001 / CC-SEC-001 regression: these should NOT be detected.
    """
    (tmp_path / "app.py").write_text("print('hello')\n")
    # Checklist-style .md that mentions many framework names
    (tmp_path / "CHECKLIST.md").write_text(
        "# Frameworks checklist\n"
        "- react, angular, vue (frontend)\n"
        "- django, flask, express (web)\n"
        "- openai, anthropic, langchain (AI)\n"
        "- sqlalchemy (ORM)\n"
    )
    (tmp_path / "agents.md").write_text(
        "Use torch, tensorflow, sklearn for ML.\n"
        "Use import openai in Python.\n"
    )
    return tmp_path


def test_python_only_repo_detects_fastapi(python_only_repo: Path) -> None:
    ctx = discover_project(python_only_repo)
    assert "python" in ctx["languages"]
    assert "fastapi" in ctx["frameworks"]


def test_docs_with_framework_names_do_not_trigger_framework_detection(docs_with_framework_names: Path) -> None:
    """CC-ARCH-001 regression: framework detection must not fire on .md files."""
    ctx = discover_project(docs_with_framework_names)
    # None of these should be detected — they are only in .md files
    for false_positive in ["react", "angular", "vue", "django", "flask", "express"]:
        assert false_positive not in ctx["frameworks"], (
            f"False positive: '{false_positive}' was detected but is only in .md documentation"
        )


def test_docs_with_ai_names_do_not_set_has_ai_libraries(docs_with_framework_names: Path) -> None:
    """CC-DEV-001 regression: AI detection must not fire on .md files."""
    ctx = discover_project(docs_with_framework_names)
    assert ctx["has_ai_libraries"] is False, (
        "has_ai_libraries should be False — AI names only appear in .md files, not source code"
    )


def test_frontend_not_detected_from_md_content(docs_with_framework_names: Path) -> None:
    """CC-SEC-001 regression: frontend.present must not be triggered by .md content."""
    ctx = discover_project(docs_with_framework_names)
    assert ctx["frontend"]["present"] is False
    assert ctx["frontend"]["frameworks"] == []


def test_python_only_repo_has_no_ai_libraries(python_only_repo: Path) -> None:
    ctx = discover_project(python_only_repo)
    assert ctx["has_ai_libraries"] is False


def test_yaml_files_do_not_trigger_ai_detection(tmp_path: Path) -> None:
    """CC-DEV-001 regression: YAML tool outputs mentioning AI libs should not trigger detection."""
    (tmp_path / "app.py").write_text("print('hello')\n")
    (tmp_path / "results.yaml").write_text(
        "findings:\n  - tool: openai\n  - library: anthropic\n  - name: langchain\n"
    )
    ctx = discover_project(tmp_path)
    assert ctx["has_ai_libraries"] is False


def test_actual_ai_import_in_source_is_detected(tmp_path: Path) -> None:
    """Positive case: real AI import in .py file should be detected."""
    (tmp_path / "model.py").write_text("import openai\nclient = openai.OpenAI()\n")
    ctx = discover_project(tmp_path)
    assert ctx["has_ai_libraries"] is True
