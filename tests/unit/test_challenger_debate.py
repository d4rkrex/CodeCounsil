from __future__ import annotations

from core.consolidation.challenger_debate import selective_debate


def test_selective_debate_adds_prompt_for_high_severity_low_confidence_finding() -> None:
    findings = [
        {
            "id": "CC-SEC-001",
            "title": "Critical auth bypass",
            "severity": "critical",
            "confidence": "low",
            "classification": "confirmed_finding",
            "observation": "Authorization may be bypassed.",
            "impact": "Attackers could access admin data.",
            "recommendation": "Verify and fix authorization.",
            "evidence": [{"file": "app.py", "start_line": 1, "end_line": 2, "description": "Potential bypass"}],
        }
    ]

    debated = selective_debate(findings)

    assert "debate_prompt" in debated[0]
    assert "Offensive Analyst" in debated[0]["debate_prompt"]


def test_selective_debate_adds_prompt_when_evidence_is_missing() -> None:
    findings = [
        {
            "id": "CC-QA-001",
            "title": "Possible regression gap",
            "severity": "medium",
            "confidence": "high",
            "classification": "test_gap",
            "observation": "Critical flow lacks tests.",
            "impact": "Regressions may go unnoticed.",
            "recommendation": "Add automated coverage.",
            "evidence": [],
        }
    ]

    debated = selective_debate(findings)

    assert "debate_prompt" in debated[0]
