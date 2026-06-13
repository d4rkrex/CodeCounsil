from __future__ import annotations

from core.reporting.remediation import generate_issue_templates, generate_remediation_plan


def make_finding() -> dict:
    return {
        "id": "CC-SEC-001",
        "title": "Missing authorization check",
        "domains": ["security"],
        "category": "authorization",
        "classification": "confirmed_finding",
        "severity": "high",
        "priority": "P2",
        "confidence": "high",
        "status": "confirmed",
        "observation": "The endpoint returns data without checking resource ownership.",
        "impact": "Users can access data that does not belong to them.",
        "recommendation": "Add an ownership check before returning data.",
        "evidence": [{"file": "app.py", "start_line": 10, "end_line": 14, "description": "No ownership check present."}],
        "effort": "medium",
    }


def test_generate_remediation_plan_includes_problem_fix_and_definition_of_done() -> None:
    plan = generate_remediation_plan({"findings": [make_finding()]}, {"repo_path": "/repo"})

    assert "Problem summary" in plan
    assert "Fix approach" in plan
    assert "Definition of Done" in plan


def test_generate_issue_templates_creates_issue_markdown_per_finding() -> None:
    issues = generate_issue_templates({"findings": [make_finding()]})

    assert "issues/CC-SEC-001.md" in issues
    assert "Acceptance Criteria" in issues["issues/CC-SEC-001.md"]
