from copy import deepcopy

from core.validation.validator import validate_finding


def valid_finding() -> dict:
    return {
        "id": "CC-SEC-001",
        "title": "Missing authorization check",
        "domains": ["security"],
        "category": "authorization",
        "classification": "confirmed_finding",
        "severity": "high",
        "priority": "P2",
        "confidence": "high",
        "status": "pending",
        "observation": "Endpoint returns data without checking ownership.",
        "impact": "Users may access data they do not own.",
        "recommendation": "Enforce resource ownership validation.",
    }


def test_valid_finding_passes_schema_validation() -> None:
    assert validate_finding(valid_finding()) == []


def test_invalid_classification_fails_schema_validation() -> None:
    finding = valid_finding()
    finding["classification"] = "style_nit"
    assert validate_finding(finding)


def test_missing_required_field_fails_validation() -> None:
    finding = valid_finding()
    del finding["impact"]
    assert validate_finding(finding)


def test_valid_evidence_array_passes_validation() -> None:
    finding = valid_finding()
    finding["evidence"] = [
        {
            "file": "app.py",
            "start_line": 1,
            "end_line": 5,
            "description": "Endpoint definition lacks an ownership check.",
        }
    ]
    assert validate_finding(finding) == []
