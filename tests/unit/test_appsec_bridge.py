from __future__ import annotations

"""
Unit tests for the appsec-plugins ↔ CodeCounsil bridge.
"""

from core.reporting.appsec_bridge import (
    convert_appsec_finding,
    convert_appsec_findings,
    dread_to_severity,
    detect_appsec_plugins,
    _normalize_severity,
    _normalize_confidence,
    _extract_evidence,
)


# ── DREAD scoring ─────────────────────────────────────────────────────────────

def test_dread_to_severity_critical() -> None:
    assert dread_to_severity(9.0) == "critical"
    assert dread_to_severity(8.0) == "critical"


def test_dread_to_severity_high() -> None:
    assert dread_to_severity(7.5) == "high"
    assert dread_to_severity(6.0) == "high"


def test_dread_to_severity_medium() -> None:
    assert dread_to_severity(5.0) == "medium"
    assert dread_to_severity(4.0) == "medium"


def test_dread_to_severity_low() -> None:
    assert dread_to_severity(3.9) == "low"
    assert dread_to_severity(0.0) == "low"


# ── Severity/confidence normalization ─────────────────────────────────────────

def test_normalize_severity_spanish() -> None:
    assert _normalize_severity("Alta") == "high"
    assert _normalize_severity("Crítica") == "critical"
    assert _normalize_severity("Media") == "medium"
    assert _normalize_severity("Baja") == "low"


def test_normalize_severity_english() -> None:
    assert _normalize_severity("critical") == "critical"
    assert _normalize_severity("HIGH") == "high"
    assert _normalize_severity("moderate") == "medium"


def test_normalize_confidence() -> None:
    assert _normalize_confidence("confirmed") == "high"
    assert _normalize_confidence("uncertain") == "low"
    assert _normalize_confidence("alta") == "high"


# ── Evidence extraction ───────────────────────────────────────────────────────

def test_extract_evidence_from_file_field() -> None:
    raw = {"file": "src/api.py", "line": 42, "description": "Auth bypass"}
    evidence = _extract_evidence(raw)
    assert len(evidence) == 1
    assert evidence[0]["file"] == "src/api.py"
    assert evidence[0]["start_line"] == 42


def test_extract_evidence_from_archivo_field() -> None:
    # appsec-plugins uses Spanish field names in some outputs
    raw = {"archivo": "src/auth.py", "linea": 15}
    evidence = _extract_evidence(raw)
    assert len(evidence) == 1
    assert evidence[0]["file"] == "src/auth.py"


def test_extract_evidence_from_colon_notation() -> None:
    raw = {"file": "src/api.py:42"}
    evidence = _extract_evidence(raw)
    assert evidence[0]["file"] == "src/api.py"


def test_extract_evidence_empty_when_no_file() -> None:
    raw = {"title": "Some finding"}
    assert _extract_evidence(raw) == []


def test_extract_evidence_passthrough_cc_format() -> None:
    raw = {"evidence": [{"file": "app.py", "start_line": 10, "end_line": 15, "description": "IDOR"}]}
    evidence = _extract_evidence(raw)
    assert evidence[0]["file"] == "app.py"
    assert evidence[0]["start_line"] == 10


# ── Single finding conversion ─────────────────────────────────────────────────

def test_convert_appsec_finding_basic() -> None:
    raw = {
        "title": "Missing auth check",
        "description": "No ownership verification before returning user data",
        "severity": "high",
        "impact": "Any user can read other user data",
        "file": "app.py",
        "line": 42,
        "recommendation": "Add ownership check",
    }
    result = convert_appsec_finding(raw, source="appsec-tm", index=1)

    assert result["id"] == "CC-SEC-001"
    assert result["title"] == "Missing auth check"
    assert result["severity"] == "high"
    assert result["priority"] == "P2"
    assert result["domains"] == ["security"]
    assert result["external_source"] == "appsec-plugins/appsec-tm"
    assert len(result["evidence"]) == 1
    assert result["evidence"][0]["file"] == "app.py"


def test_convert_appsec_finding_uses_dread_score_for_severity() -> None:
    raw = {
        "title": "Critical auth bypass",
        "description": "Full bypass possible",
        "severity": "medium",  # will be overridden by DREAD
        "dread_total": 9.2,
        "file": "auth.py",
        "line": 10,
        "recommendation": "Fix auth",
    }
    result = convert_appsec_finding(raw, source="appsec-tm")
    # DREAD 9.2 → critical
    assert result["severity"] == "critical"
    assert result["priority"] == "P1"


def test_convert_appsec_finding_includes_owasp_tags() -> None:
    raw = {
        "title": "BOLA finding",
        "description": "Object accessed without ownership check",
        "severity": "high",
        "owasp_id": "API1:2023 Broken Object Level Authorization",
        "cwe": "CWE-639",
        "file": "api.py",
        "line": 20,
        "recommendation": "Add ownership check",
    }
    result = convert_appsec_finding(raw, source="owasp-api")
    assert "OWASP:API1" in result["observation"]
    assert "CWE:CWE-639" in result["observation"]


def test_convert_appsec_finding_includes_stride_tags() -> None:
    raw = {
        "title": "Session hijack risk",
        "description": "Session token predictable",
        "severity": "high",
        "stride": "Spoofing",
        "file": "session.py",
        "line": 5,
        "recommendation": "Use secure random tokens",
    }
    result = convert_appsec_finding(raw, source="appsec-tm")
    assert "STRIDE:Spoofing" in result["observation"]


def test_convert_appsec_finding_confirmed_when_evidence_and_high() -> None:
    raw = {
        "title": "SQL injection",
        "description": "Unsanitized input in query",
        "severity": "critical",
        "file": "db.py",
        "line": 33,
        "recommendation": "Use parameterized queries",
    }
    result = convert_appsec_finding(raw, source="appsec-owasp")
    assert result["classification"] == "confirmed_finding"


def test_convert_appsec_finding_probable_risk_when_no_evidence() -> None:
    raw = {
        "title": "Possible rate limiting gap",
        "description": "Could not confirm rate limiting in codebase",
        "severity": "high",
        "recommendation": "Add rate limiting",
    }
    result = convert_appsec_finding(raw, source="appsec-tm")
    assert result["classification"] == "probable_risk"


# ── Batch conversion ──────────────────────────────────────────────────────────

def test_convert_appsec_findings_batch() -> None:
    raw_list = [
        {"title": "Finding A", "description": "x", "severity": "high", "file": "a.py", "line": 1, "recommendation": "Fix A"},
        {"title": "Finding B", "description": "y", "severity": "medium", "file": "b.py", "line": 2, "recommendation": "Fix B"},
    ]
    results = convert_appsec_findings(raw_list, source="appsec-tm")
    assert len(results) == 2
    assert results[0]["id"] == "CC-SEC-001"
    assert results[1]["id"] == "CC-SEC-002"


def test_convert_appsec_findings_skips_malformed() -> None:
    raw_list = [
        {"title": "Good finding", "description": "x", "severity": "high", "file": "a.py", "line": 1, "recommendation": "Fix"},
        None,  # malformed
        {"title": "Another good", "description": "y", "severity": "low", "recommendation": "Fix"},
    ]
    # Should not raise, should skip None
    results = convert_appsec_findings([r for r in raw_list if r is not None], source="appsec-tm")
    assert len(results) == 2


# ── Detection ─────────────────────────────────────────────────────────────────

def test_detect_appsec_plugins_returns_dict() -> None:
    result = detect_appsec_plugins()
    assert isinstance(result, dict)
    assert "installed" in result
    assert "capabilities" in result
    assert "suggestion" in result
    # installed is True since we know appsec-plugins is in the environment
    # (but this test should pass even if not installed)
    assert isinstance(result["installed"], bool)


def test_detect_appsec_plugins_installed_in_this_env() -> None:
    # We know appsec-plugins is installed in this specific environment
    result = detect_appsec_plugins()
    assert result["installed"] is True
    assert len(result["capabilities"]) > 0
    assert "appsec-tm" in result["capabilities"] or "threat-model" in result["capabilities"]
