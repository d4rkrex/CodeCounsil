import json
from pathlib import Path

import pytest

from core.orchestration.orchestrator import run_consolidate_only, run_review


def test_full_review_generates_expected_artifacts(simple_api_repo: Path) -> None:
    result = run_review(str(simple_api_repo), mode="full")
    workspace = Path(result["workspace"])

    assert result["status"] == "complete"
    assert workspace.exists()
    for name in [
        "project-context.json",
        "execution-manifest.json",
        "challenged-findings.json",
        "consolidated-findings.json",
        "executive-summary.md",
        "technical-report.md",
        "prioritized-backlog.md",
        "limitations.md",
    ]:
        assert (workspace / name).exists(), name

    manifest = json.loads((workspace / "execution-manifest.json").read_text(encoding="utf-8"))
    selected_names = [item["name"] for item in manifest["specialists_selected"]]
    assert "discovery" in selected_names
    assert "challenger" in selected_names
    assert "consolidator" in selected_names
    assert "security" in selected_names

    project_context = json.loads((workspace / "project-context.json").read_text(encoding="utf-8"))
    assert "python" in project_context["languages"]
    assert "fastapi" in project_context["frameworks"]


def test_security_mode_only_runs_security_and_mandatory(simple_api_repo: Path) -> None:
    result = run_review(str(simple_api_repo), mode="security")
    workspace = Path(result["workspace"])
    assert result["status"] == "complete"

    manifest = json.loads((workspace / "execution-manifest.json").read_text(encoding="utf-8"))
    selected_names = {item["name"] for item in manifest["specialists_selected"]}
    excluded_names = {item["name"] for item in manifest["specialists_excluded"]}

    assert "security" in selected_names
    assert "discovery" in selected_names
    assert "challenger" in selected_names
    assert "consolidator" in selected_names
    assert "architecture" in excluded_names
    assert "developer" in excluded_names


def test_architecture_mode_selects_only_architecture(simple_api_repo: Path) -> None:
    result = run_review(str(simple_api_repo), mode="architecture")
    workspace = Path(result["workspace"])
    assert result["status"] == "complete"

    manifest = json.loads((workspace / "execution-manifest.json").read_text(encoding="utf-8"))
    selected_names = {item["name"] for item in manifest["specialists_selected"]}
    assert "architecture" in selected_names
    assert "security" not in selected_names
    assert "developer" not in selected_names


def test_consolidate_only_with_prepopulated_findings(simple_api_repo: Path) -> None:
    # Run full review first to create the workspace
    run_review(str(simple_api_repo), mode="full")
    workspace = simple_api_repo / ".review"

    # Pre-populate a finding in the security specialist output
    sample_finding = {
        "id": "CC-SEC-001",
        "title": "Missing authorization check in test endpoint",
        "domains": ["security"],
        "category": "authorization",
        "classification": "confirmed_finding",
        "severity": "high",
        "priority": "P2",
        "confidence": "high",
        "status": "pending",
        "observation": "The /users/{user_id} endpoint does not check if the requester owns the resource.",
        "impact": "Any authenticated user can read any other user's data (BOLA/IDOR).",
        "evidence": [{"file": "app.py", "start_line": 10, "end_line": 15, "description": "No authorization check before returning user data"}],
        "assumptions": [],
        "missing_evidence": [],
        "recommendation": "Add ownership check: verify that request.user.id == user_id before returning data.",
        "effort": "low",
    }
    (workspace / "raw" / "security.json").write_text(json.dumps([sample_finding]), encoding="utf-8")

    result = run_consolidate_only(str(simple_api_repo))

    assert result["status"] == "complete"
    assert result["findings_count"] == 1
    assert result["by_severity"].get("high") == 1

    consolidated = json.loads((workspace / "consolidated-findings.json").read_text())
    assert consolidated["total_findings"] == 1
    assert consolidated["findings"][0]["id"] == "CC-SEC-001"

    summary = (workspace / "executive-summary.md").read_text()
    assert "CC-SEC-001" in summary


def test_next_steps_guidance_when_no_findings(simple_api_repo: Path) -> None:
    result = run_review(str(simple_api_repo), mode="full")
    assert result["findings_count"] == 0
    assert len(result["next_steps"]) > 0
    assert any("prompt" in step.lower() or "consolidate" in step.lower() for step in result["next_steps"])


def test_full_review_result_includes_specialists_run(simple_api_repo: Path) -> None:
    result = run_review(str(simple_api_repo), mode="full")
    assert "specialists_run" in result
    assert "security" in result["specialists_run"]
    assert "discovery" in result["specialists_run"]
