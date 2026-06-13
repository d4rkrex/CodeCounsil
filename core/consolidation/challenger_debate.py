from __future__ import annotations


def selective_debate(findings: list[dict]) -> list[dict]:
    """
    Attach debate prompts to findings that warrant deeper scrutiny.
    """
    debated: list[dict] = []
    for finding in findings:
        updated = dict(finding)
        if _needs_debate(updated):
            updated["debate_prompt"] = _build_debate_prompt(updated)
        debated.append(updated)
    return debated


def _needs_debate(finding: dict) -> bool:
    severity = str(finding.get("severity", "info")).lower()
    confidence = str(finding.get("confidence", "high")).lower()
    classification = str(finding.get("classification", "")).lower()
    evidence = finding.get("evidence") or []

    if severity in {"critical", "high"} and confidence == "low":
        return True
    if severity == "critical" and classification == "probable_risk":
        return True
    if not evidence:
        return True
    return False


def _build_debate_prompt(finding: dict) -> str:
    evidence_lines = finding.get("evidence") or []
    evidence_block = "\n".join(
        f"- {item.get('file', 'unknown')}:{item.get('start_line', '?')}-{item.get('end_line', '?')} — {item.get('description', '')}"
        for item in evidence_lines
    ) or "- No concrete evidence attached."

    return "\n".join(
        [
            f"# Debate Review for {finding.get('id', 'UNKNOWN')}",
            "",
            "## Finding Under Review",
            f"- Title: {finding.get('title', 'Untitled finding')}",
            f"- Severity: {finding.get('severity', 'info')}",
            f"- Confidence: {finding.get('confidence', 'low')}",
            f"- Classification: {finding.get('classification', 'unknown')}",
            f"- Observation: {finding.get('observation', '')}",
            f"- Impact: {finding.get('impact', '')}",
            f"- Recommendation: {finding.get('recommendation', '')}",
            "",
            "## Evidence",
            evidence_block,
            "",
            "## Offensive Analyst",
            "Argue why this finding is real, exploitable, and important. Use the evidence, likely attack path, blast radius, and why a reviewer should trust the claim.",
            "",
            "## Defensive Analyst",
            "Argue why this may be a false positive, low-priority issue, or context-dependent concern. Identify missing assumptions, compensating controls, or evidence gaps.",
            "",
            "## Judge",
            "Decide whether the finding should remain confirmed, be downgraded, or be rejected. Explain which side is stronger and what additional evidence would close the gap.",
        ]
    ).strip() + "\n"
