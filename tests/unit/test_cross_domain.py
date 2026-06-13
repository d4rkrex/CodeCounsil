from __future__ import annotations

from core.consolidation.cross_domain import detect_contradictions


def test_detect_contradictions_finds_logging_tradeoff() -> None:
    findings = [
        {
            "id": "CC-SRE-001",
            "title": "Increase request logging depth",
            "domains": ["sre"],
            "category": "observability",
            "observation": "Add more structured logging and request traces for incident response.",
            "impact": "Improves diagnosis of production failures.",
            "recommendation": "Log request payload fields for better debugging.",
        },
        {
            "id": "CC-SEC-001",
            "title": "Sensitive data exposed in logs",
            "domains": ["security"],
            "category": "logging",
            "observation": "Current logs include secrets and PII.",
            "impact": "Compromised logs would leak sensitive data.",
            "recommendation": "Redact sensitive fields before writing logs.",
        },
    ]

    contradictions = detect_contradictions(findings)

    assert len(contradictions) == 1
    assert contradictions[0]["findings"] == ["CC-SEC-001", "CC-SRE-001"]
