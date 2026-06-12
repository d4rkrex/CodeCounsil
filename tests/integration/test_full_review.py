import json
from pathlib import Path

from core.orchestration.orchestrator import run_review


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
