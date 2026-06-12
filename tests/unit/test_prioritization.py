from core.consolidation.consolidator import consolidate, prioritize_findings


def finding(identifier: str, severity: str, priority: str, confidence: str, status: str = "confirmed") -> dict:
    return {
        "id": identifier,
        "title": identifier,
        "domains": ["security"],
        "category": identifier,
        "classification": "confirmed_finding",
        "severity": severity,
        "priority": priority,
        "confidence": confidence,
        "status": status,
        "observation": "obs",
        "impact": "impact",
        "recommendation": "fix",
        "evidence": [{"file": f"{identifier}.py", "start_line": 1, "end_line": 2, "description": "desc"}],
    }


def test_critical_p1_before_high_p2_before_medium_p3() -> None:
    ordered = prioritize_findings([
        finding("CC-SEC-003", "medium", "P3", "medium"),
        finding("CC-SEC-002", "high", "P2", "medium"),
        finding("CC-SEC-001", "critical", "P1", "medium"),
    ])
    assert [item["id"] for item in ordered] == ["CC-SEC-001", "CC-SEC-002", "CC-SEC-003"]


def test_same_severity_is_sorted_by_confidence() -> None:
    ordered = prioritize_findings([
        finding("CC-SEC-002", "high", "P2", "low"),
        finding("CC-SEC-001", "high", "P2", "high"),
    ])
    assert [item["id"] for item in ordered] == ["CC-SEC-001", "CC-SEC-002"]


def test_rejected_findings_are_excluded_from_active_results() -> None:
    result = consolidate([
        finding("CC-SEC-001", "high", "P2", "high", status="confirmed"),
        finding("CC-SEC-002", "critical", "P1", "high", status="rejected"),
    ])
    assert result["total_findings"] == 1
    assert result["findings"][0]["id"] == "CC-SEC-001"
