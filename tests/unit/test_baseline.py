from __future__ import annotations

import json
from pathlib import Path

from core.baseline import BaselineManager


def make_finding(identifier: str, severity: str = "high") -> dict:
    return {
        "id": identifier,
        "title": f"Finding {identifier}",
        "severity": severity,
    }


def test_baseline_manager_updates_and_persists_findings(tmp_path: Path) -> None:
    manager = BaselineManager.load(tmp_path)
    findings = [make_finding("CC-SEC-001"), make_finding("CC-QA-001", "medium")]

    diff = manager.update(findings)
    manager.save()

    assert [item["id"] for item in diff["new"]] == ["CC-SEC-001", "CC-QA-001"]
    baseline_path = tmp_path / ".codecouncil" / "baseline.json"
    assert baseline_path.exists()
    saved = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert saved["findings"]["CC-SEC-001"]["status"] == "new"


def test_baseline_diff_marks_reintroduced_and_resolved(tmp_path: Path) -> None:
    manager = BaselineManager.load(tmp_path)
    manager.update([make_finding("CC-SEC-001"), make_finding("CC-DEV-001", "low")])
    manager.save()

    manager.update([make_finding("CC-SEC-001")])
    manager.save()
    manager.update([])
    manager.save()

    reloaded = BaselineManager.load(tmp_path)
    diff = reloaded.diff([make_finding("CC-DEV-001", "low")])

    assert [item["id"] for item in diff["reintroduced"]] == ["CC-DEV-001"]
    assert diff["resolved"] == []


def test_filter_new_only_ignores_actively_suppressed_findings(tmp_path: Path) -> None:
    manager = BaselineManager.load(tmp_path)
    manager.update([make_finding("CC-SEC-001")])
    manager.suppress("CC-SEC-001", "accepted risk")
    manager.save()

    reloaded = BaselineManager.load(tmp_path)
    filtered = reloaded.filter_new_only([make_finding("CC-SEC-001"), make_finding("CC-SEC-002", "critical")])

    assert [item["id"] for item in filtered] == ["CC-SEC-002"]
