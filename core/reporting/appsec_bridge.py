from __future__ import annotations

"""
Bridge between appsec-plugins output and CodeCounsil finding schema.

When the appsec-plugins toolkit is available and has been run against a repo,
this module converts its findings to CodeCounsil's JSON schema format
so they can be consolidated alongside other specialist findings.

Usage:
    from core.reporting.appsec_bridge import convert_appsec_findings, detect_appsec_plugins
    
    if detect_appsec_plugins():
        # Suggest using appsec-plugins in the security prompt
        ...
    
    # After appsec-plugins ran and produced output:
    cc_findings = convert_appsec_findings(raw_appsec_output, source="appsec-tm")
    # Save to .review/raw/security.json or security-plugins.json
"""

import os
import re
from pathlib import Path
from typing import Optional


# Known appsec-plugins install locations
_PLUGIN_PATHS = [
    Path.home() / ".copilot" / "installed-plugins" / "appsec-plugins" / "appsec-review",
    Path.home() / ".claude" / "agents",  # claude code agent install
    Path("/usr/local/share/appsec-plugins"),
]

_APPSEC_SKILL_MARKERS = [
    "appsec-tm",
    "appsec-review",
    "appsec-diff",
    "threat-model",
    "owasp-api",
]


def detect_appsec_plugins() -> dict:
    """
    Detect if appsec-plugins is installed and which capabilities are available.
    
    Returns:
        {
          "installed": bool,
          "path": str | None,
          "capabilities": list[str],
          "suggestion": str  # human-readable suggestion
        }
    """
    for path in _PLUGIN_PATHS:
        if path.exists():
            capabilities = _detect_capabilities(path)
            return {
                "installed": True,
                "path": str(path),
                "capabilities": capabilities,
                "suggestion": _build_suggestion(capabilities),
            }
    
    # Also check if skill files exist in copilot skills directory
    copilot_skills = Path.home() / ".copilot" / "skills"
    if copilot_skills.exists():
        found_skills = [
            d.name for d in copilot_skills.iterdir()
            if d.is_dir() and any(m in d.name for m in _APPSEC_SKILL_MARKERS)
        ]
        if found_skills:
            return {
                "installed": True,
                "path": str(copilot_skills),
                "capabilities": found_skills,
                "suggestion": _build_suggestion(found_skills),
            }
    
    return {
        "installed": False,
        "path": None,
        "capabilities": [],
        "suggestion": "appsec-plugins not detected. Install from: copilot plugin install appsec-review@appsec-plugins",
    }


def _detect_capabilities(base_path: Path) -> list[str]:
    """Return list of available capability names from the installation."""
    caps = []
    # Check agents
    agents_dir = base_path / "agents"
    if agents_dir.exists():
        for f in agents_dir.glob("*.agent.md"):
            caps.append(f.stem.replace(".agent", ""))
    # Check skills
    skills_dir = base_path / "skills"
    if skills_dir.exists():
        for d in skills_dir.iterdir():
            if d.is_dir() and (d / "SKILL.md").exists():
                caps.append(d.name)
    return sorted(set(caps))


def _build_suggestion(capabilities: list[str]) -> str:
    lines = ["appsec-plugins detected. Recommended usage with CodeCounsil:"]
    if "appsec-tm" in capabilities or "threat-model" in capabilities:
        lines.append("  → @appsec-tm or threat-model skill: STRIDE+DREAD threat model")
    if "owasp-api" in capabilities:
        lines.append("  → owasp-api skill: OWASP API Security Top 10 (2023)")
    if "dependency-sca" in capabilities:
        lines.append("  → dependency-sca skill: SCA with exploitability validation")
    if "cloud-security" in capabilities:
        lines.append("  → cloud-security skill: IaC + cloud configuration review")
    if "container-security" in capabilities:
        lines.append("  → container-security skill: Dockerfile + K8s security")
    if "owasp-llm" in capabilities:
        lines.append("  → owasp-llm skill: OWASP LLM Top 10 (2025)")
    lines.append("  After running, convert output to CC schema and save to .review/raw/security.json")
    lines.append("  Then: project-review --consolidate-only")
    return "\n".join(lines)


# ── DREAD severity mapping ────────────────────────────────────────────────────

_DREAD_TO_SEVERITY = [
    (8.0, "critical"),
    (6.0, "high"),
    (4.0, "medium"),
    (0.0, "low"),
]

_DREAD_TO_PRIORITY = {
    "critical": "P1",
    "high": "P2",
    "medium": "P3",
    "low": "P4",
    "info": "P4",
}


def dread_to_severity(score: float) -> str:
    for threshold, level in _DREAD_TO_SEVERITY:
        if score >= threshold:
            return level
    return "low"


# ── Finding format conversion ─────────────────────────────────────────────────

def convert_appsec_finding(
    raw: dict,
    source: str,
    index: int = 1,
) -> dict:
    """
    Convert a single appsec-plugins finding to CodeCounsil schema format.
    
    Handles outputs from: appsec-tm, appsec-owasp, appsec-diff, owasp-api,
    threat-model skill, dependency-sca, cloud-security.
    
    Args:
        raw: raw finding dict from appsec-plugins
        source: capability name (e.g., "appsec-tm", "owasp-api")
        index: sequential number for ID generation
    
    Returns:
        CodeCounsil finding dict compliant with schemas/finding.schema.json
    """
    # Generate ID
    finding_id = f"CC-SEC-{index:03d}"
    
    # Extract severity — try multiple field names used by different plugins
    raw_severity = (
        raw.get("severity") or raw.get("risk_level") or raw.get("level") or "medium"
    ).lower()
    
    # Handle DREAD scores if present
    dread_total = raw.get("dread_total") or raw.get("dread_score")
    if dread_total is not None:
        try:
            raw_severity = dread_to_severity(float(dread_total))
        except (TypeError, ValueError):
            pass
    
    # Normalize severity
    severity = _normalize_severity(raw_severity)
    priority = _DREAD_TO_PRIORITY.get(severity, "P3")
    
    # Extract confidence
    confidence = _normalize_confidence(raw.get("confidence") or raw.get("certainty") or "medium")
    
    # Build classification
    classification = _infer_classification(raw, severity)
    
    # Build observation with DREAD scores if available
    observation = raw.get("observation") or raw.get("description") or raw.get("scenario") or ""
    if dread_total is not None:
        observation = f"{observation}\n\nDREAD Score: {dread_total}/10 ({source})"
    
    # Build evidence list
    evidence = _extract_evidence(raw)
    
    # Build STRIDE/OWASP metadata for observation
    stride = raw.get("stride") or raw.get("stride_category")
    owasp_id = raw.get("owasp_id") or raw.get("owasp_category")
    cwe = raw.get("cwe") or raw.get("cwe_id")
    tags = []
    if stride:
        tags.append(f"STRIDE:{stride}")
    if owasp_id:
        tags.append(f"OWASP:{owasp_id}")
    if cwe:
        tags.append(f"CWE:{cwe}")
    
    if tags:
        observation = f"[{', '.join(tags)}] {observation}"
    
    return {
        "id": finding_id,
        "title": raw.get("title") or raw.get("name") or f"Security finding from {source}",
        "domains": ["security"],
        "category": _infer_category(raw, owasp_id, stride),
        "classification": classification,
        "severity": severity,
        "priority": priority,
        "confidence": confidence,
        "status": "pending",
        "observation": observation.strip(),
        "impact": raw.get("impact") or raw.get("dark_corner") or "",
        "evidence": evidence,
        "assumptions": raw.get("assumptions") or [],
        "missing_evidence": raw.get("missing_evidence") or [],
        "recommendation": raw.get("recommendation") or raw.get("remediation") or raw.get("mitigation") or "",
        "effort": raw.get("effort") or _infer_effort(severity),
        "external_source": f"appsec-plugins/{source}",
    }


def convert_appsec_findings(
    raw_findings: list[dict],
    source: str,
    start_index: int = 1,
) -> list[dict]:
    """Convert a list of appsec-plugins findings to CodeCounsil schema."""
    result = []
    for i, raw in enumerate(raw_findings, start=start_index):
        try:
            converted = convert_appsec_finding(raw, source, i)
            result.append(converted)
        except Exception:
            # Skip malformed findings rather than crashing
            continue
    return result


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize_severity(raw: str) -> str:
    mapping = {
        "crítica": "critical", "critica": "critical", "critical": "critical",
        "alta": "high", "high": "high",
        "media": "medium", "medium": "medium", "moderate": "medium",
        "baja": "low", "low": "low",
        "info": "info", "informational": "info",
    }
    return mapping.get(raw.lower(), "medium")


def _normalize_confidence(raw: str) -> str:
    mapping = {
        "alta": "high", "high": "high", "confirmed": "high",
        "media": "medium", "medium": "medium",
        "baja": "low", "low": "low", "uncertain": "low",
    }
    return mapping.get(str(raw).lower(), "medium")


def _infer_classification(raw: dict, severity: str) -> str:
    # If source explicitly sets classification, use it
    if raw.get("classification"):
        return raw["classification"]
    # Findings with evidence are confirmed
    if raw.get("evidence") or raw.get("file"):
        if severity in ("critical", "high"):
            return "confirmed_finding"
        return "probable_risk"
    # No evidence → probable or insufficient
    if severity in ("critical", "high"):
        return "probable_risk"
    return "insufficient_evidence"


def _infer_category(raw: dict, owasp_id: Optional[str], stride: Optional[str]) -> str:
    if raw.get("category"):
        return raw["category"]
    # Map OWASP → category
    owasp_map = {
        "A01": "access_control", "A02": "cryptography", "A03": "injection",
        "A04": "insecure_design", "A05": "misconfiguration", "A06": "supply_chain",
        "A07": "authentication", "A08": "integrity", "A09": "logging", "A10": "ssrf",
        "API1": "bola", "API2": "authentication", "API3": "authorization",
        "API4": "rate_limiting", "API5": "bfla", "API6": "business_logic",
        "API7": "ssrf", "API8": "misconfiguration", "API9": "inventory",
        "API10": "third_party",
    }
    if owasp_id:
        prefix = owasp_id.split(":")[0].strip()
        for key, val in owasp_map.items():
            if prefix.upper().startswith(key):
                return val
    # Map STRIDE → category
    stride_map = {
        "Spoofing": "authentication", "Tampering": "integrity",
        "Repudiation": "logging", "Information Disclosure": "information_disclosure",
        "Denial of Service": "availability", "Elevation of Privilege": "authorization",
    }
    if stride and stride in stride_map:
        return stride_map[stride]
    return "security"


def _extract_evidence(raw: dict) -> list[dict]:
    # Standard CC evidence format
    if isinstance(raw.get("evidence"), list):
        return raw["evidence"]
    # appsec-plugins uses "archivo" / "file" directly
    file_ref = raw.get("archivo") or raw.get("file") or raw.get("path")
    if file_ref:
        line_ref = raw.get("linea") or raw.get("line") or raw.get("start_line") or 0
        try:
            line = int(str(line_ref).split("-")[0].split(":")[0]) if line_ref else 0
        except (ValueError, TypeError):
            line = 0
        return [{
            "file": str(file_ref).split(":")[0],
            "start_line": line,
            "end_line": line,
            "description": raw.get("description") or raw.get("scenario") or "",
        }]
    return []


def _infer_effort(severity: str) -> str:
    return {"critical": "high", "high": "medium", "medium": "medium", "low": "low"}.get(severity, "medium")
