from __future__ import annotations

"""
Unit tests for the evaluation harness and metrics.
"""

import json
from pathlib import Path

import pytest

from core.evaluation.harness import evaluate_fixture, _match_defect
from core.evaluation.metrics import EvalResult


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def minimal_fixture(tmp_path: Path) -> Path:
    """A fixture with one known defect and one matching finding."""
    expected = {
        "project": "test-project",
        "known_defects": [
            {
                "id": "KD-001",
                "description": "IDOR in /users",
                "file": "app.py",
                "line_hint": 10,
                "expected_domains": ["security"],
                "expected_classification": ["confirmed_finding"],
                "expected_severity_min": "high",
                "keywords": ["idor", "ownership", "authorization"],
            }
        ],
        "thresholds": {"min_recall": 0.5},
    }
    (tmp_path / "expected_findings.json").write_text(json.dumps(expected))

    review_dir = tmp_path / ".review"
    review_dir.mkdir()
    consolidated = {
        "total_findings": 1,
        "findings": [
            {
                "id": "CC-SEC-001",
                "title": "IDOR — missing authorization check",
                "domains": ["security"],
                "category": "authorization",
                "classification": "confirmed_finding",
                "severity": "high",
                "priority": "P2",
                "confidence": "high",
                "status": "confirmed",
                "observation": "The /users endpoint lacks an ownership check.",
                "impact": "Any user can read any other user's data.",
                "evidence": [{"file": "app.py", "start_line": 10, "end_line": 15, "description": "No auth check"}],
                "recommendation": "Add ownership verification.",
                "effort": "low",
            }
        ],
    }
    (review_dir / "consolidated-findings.json").write_text(json.dumps(consolidated))
    return tmp_path


@pytest.fixture()
def empty_fixture(tmp_path: Path) -> Path:
    """A healthy fixture — no known defects, review found nothing."""
    expected = {
        "project": "healthy-test",
        "known_defects": [],
        "thresholds": {"max_confirmed_findings": 0, "max_total_findings": 2},
    }
    (tmp_path / "expected_findings.json").write_text(json.dumps(expected))

    review_dir = tmp_path / ".review"
    review_dir.mkdir()
    (review_dir / "consolidated-findings.json").write_text(json.dumps({"total_findings": 0, "findings": []}))
    return tmp_path


# ── Harness tests ─────────────────────────────────────────────────────────────

def test_evaluate_fixture_detects_known_defect(minimal_fixture: Path) -> None:
    result = evaluate_fixture(minimal_fixture)
    assert result.known_defects_detected == 1
    assert result.recall == 1.0
    assert result.findings_total == 1


def test_evaluate_fixture_passes_threshold(minimal_fixture: Path) -> None:
    result = evaluate_fixture(minimal_fixture)
    expected = json.loads((minimal_fixture / "expected_findings.json").read_text())
    passed, failures = result.passes_thresholds(expected.get("thresholds", {}))
    assert passed, failures


def test_healthy_fixture_produces_zero_false_positives(empty_fixture: Path) -> None:
    result = evaluate_fixture(empty_fixture)
    assert result.findings_total == 0
    assert result.false_positives == 0
    assert result.precision is None  # no findings, undefined


def test_healthy_fixture_passes_max_confirmed_threshold(empty_fixture: Path) -> None:
    result = evaluate_fixture(empty_fixture)
    expected = json.loads((empty_fixture / "expected_findings.json").read_text())
    passed, failures = result.passes_thresholds(expected.get("thresholds", {}))
    assert passed, failures


def test_unmatched_defect_reduces_recall(tmp_path: Path) -> None:
    """When a known defect has no matching finding, recall drops."""
    expected = {
        "project": "partial-recall",
        "known_defects": [
            {
                "id": "KD-001",
                "description": "Auth bypass",
                "file": "app.py",
                "line_hint": 1,
                "expected_domains": ["security"],
                "expected_classification": ["confirmed_finding"],
                "expected_severity_min": "high",
                "keywords": ["auth", "bypass", "token"],
            },
            {
                "id": "KD-002",
                "description": "SQL injection",
                "file": "db.py",
                "line_hint": 20,
                "expected_domains": ["security"],
                "expected_classification": ["confirmed_finding"],
                "expected_severity_min": "critical",
                "keywords": ["sql", "injection", "query"],
            },
        ],
        "thresholds": {"min_recall": 0.4},
    }
    (tmp_path / "expected_findings.json").write_text(json.dumps(expected))
    review_dir = tmp_path / ".review"
    review_dir.mkdir()
    # Only one finding (matches KD-001)
    consolidated = {
        "total_findings": 1,
        "findings": [
            {
                "id": "CC-SEC-001",
                "title": "Missing auth check — token bypass",
                "domains": ["security"],
                "category": "authentication",
                "classification": "confirmed_finding",
                "severity": "high",
                "priority": "P2",
                "confidence": "high",
                "status": "confirmed",
                "observation": "auth bypass via token manipulation",
                "impact": "x",
                "evidence": [{"file": "app.py", "start_line": 1, "end_line": 5, "description": "bypass"}],
                "recommendation": "fix it",
                "effort": "low",
            }
        ],
    }
    (review_dir / "consolidated-findings.json").write_text(json.dumps(consolidated))

    result = evaluate_fixture(tmp_path)
    assert result.known_defects_detected == 1
    assert result.known_defects_total == 2
    assert result.recall == 0.5
    assert len(result.unmatched_defects) == 1
    assert result.unmatched_defects[0]["id"] == "KD-002"


def test_false_positive_counted_when_no_defect_matches(tmp_path: Path) -> None:
    expected = {
        "project": "fp-test",
        "known_defects": [],
        "thresholds": {"max_confirmed_findings": 0},
    }
    (tmp_path / "expected_findings.json").write_text(json.dumps(expected))
    review_dir = tmp_path / ".review"
    review_dir.mkdir()
    consolidated = {
        "total_findings": 1,
        "findings": [
            {
                "id": "CC-ARCH-001",
                "title": "Unnecessary complexity",
                "domains": ["architecture"],
                "category": "design",
                "classification": "confirmed_finding",
                "severity": "low",
                "priority": "P4",
                "confidence": "medium",
                "status": "confirmed",
                "observation": "x",
                "impact": "x",
                "recommendation": "refactor",
                "effort": "medium",
            }
        ],
    }
    (review_dir / "consolidated-findings.json").write_text(json.dumps(consolidated))

    result = evaluate_fixture(tmp_path)
    assert result.false_positives == 1
    assert result.findings_total == 1


# ── Metrics tests ─────────────────────────────────────────────────────────────

def test_precision_formula() -> None:
    r = EvalResult(project="x", findings_total=10, false_positives=2)
    assert r.precision == 0.8


def test_recall_formula() -> None:
    r = EvalResult(project="x", known_defects_total=5, known_defects_detected=4)
    assert r.recall == 0.8


def test_precision_none_when_no_findings() -> None:
    r = EvalResult(project="x", findings_total=0)
    assert r.precision is None


def test_recall_none_when_no_known_defects() -> None:
    r = EvalResult(project="x", known_defects_total=0)
    assert r.recall is None


def test_duplicate_rate_formula() -> None:
    r = EvalResult(project="x", findings_total=10, duplicates=3)
    assert r.duplicate_rate == 0.3


def test_threshold_recall_failure() -> None:
    r = EvalResult(project="x", known_defects_total=5, known_defects_detected=2)
    passed, failures = r.passes_thresholds({"min_recall": 0.6})
    assert not passed
    assert any("recall" in f for f in failures)


def test_threshold_pass() -> None:
    r = EvalResult(project="x", known_defects_total=5, known_defects_detected=4, findings_total=6, false_positives=1)
    passed, failures = r.passes_thresholds({"min_recall": 0.6, "max_false_positive_rate": 0.3})
    assert passed, failures


# ── Match defect tests ────────────────────────────────────────────────────────

def test_match_defect_by_keyword() -> None:
    defect = {"keywords": ["idor", "ownership"], "expected_domains": ["security"], "expected_classification": ["confirmed_finding"], "file": ""}
    findings = [
        {"title": "Missing ownership check — IDOR possible", "observation": "", "category": "authorization", "recommendation": "", "domains": ["security"], "classification": "confirmed_finding", "evidence": []},
    ]
    match = _match_defect(defect, findings)
    assert match is not None


def test_match_defect_no_match() -> None:
    defect = {"keywords": ["sql", "injection"], "expected_domains": ["security"], "expected_classification": ["confirmed_finding"], "file": ""}
    findings = [
        {"title": "Poor naming conventions", "observation": "", "category": "style", "recommendation": "", "domains": ["developer"], "classification": "improvement", "evidence": []},
    ]
    match = _match_defect(defect, findings)
    assert match is None
