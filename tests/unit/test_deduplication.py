from core.consolidation.consolidator import deduplicate_findings


def make_finding(identifier: str, domain: str, severity: str, category: str = "input_validation", file_name: str = "app.py") -> dict:
    return {
        "id": identifier,
        "title": "Duplicate root cause",
        "domains": [domain],
        "category": category,
        "classification": "confirmed_finding",
        "severity": severity,
        "priority": "P2",
        "confidence": "high",
        "status": "confirmed",
        "observation": "Observation",
        "impact": "Impact",
        "recommendation": "Recommendation",
        "evidence": [{"file": file_name, "start_line": 1, "end_line": 2, "description": "desc"}],
    }


def test_two_findings_with_same_category_and_file_are_merged() -> None:
    findings = [make_finding("CC-SEC-001", "security", "high"), make_finding("CC-ARC-001", "architecture", "medium")]
    merged = deduplicate_findings(findings)
    assert len(merged) == 1


def test_merged_finding_has_combined_domains() -> None:
    merged = deduplicate_findings([make_finding("CC-SEC-001", "security", "high"), make_finding("CC-DEV-001", "developer", "medium")])
    assert sorted(merged[0]["domains"]) == ["developer", "security"]


def test_highest_severity_wins_in_merge() -> None:
    merged = deduplicate_findings([make_finding("CC-SEC-001", "security", "low"), make_finding("CC-DEV-001", "developer", "critical")])
    assert merged[0]["severity"] == "critical"


def test_three_distinct_findings_remain_distinct() -> None:
    findings = [
        make_finding("CC-SEC-001", "security", "high", category="auth", file_name="auth.py"),
        make_finding("CC-DEV-001", "developer", "medium", category="complexity", file_name="service.py"),
        make_finding("CC-QA-001", "qa", "low", category="test_gap", file_name="test_app.py"),
    ]
    assert len(deduplicate_findings(findings)) == 3
