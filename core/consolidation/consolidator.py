from __future__ import annotations

# FR-7: Deduplication, cross-domain correlation, prioritization

PRIORITY_MAP = {
    "critical": "P1",
    "high": "P2",
    "medium": "P3",
    "low": "P4",
    "info": "P4",
}

PRIORITY_ORDER = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
CONFIDENCE_ORDER = {"high": 0, "medium": 1, "low": 2}


def deduplicate_findings(findings: list[dict]) -> list[dict]:
    groups: dict[str, dict] = {}
    for finding in findings:
        merged = dict(finding)
        merged.setdefault("priority", PRIORITY_MAP.get(merged.get("severity", "info"), "P4"))
        key = _dedup_key(merged)
        if key not in groups:
            groups[key] = merged
            continue
        existing = groups[key]
        existing["domains"] = sorted(set(existing.get("domains", []) + merged.get("domains", [])))
        existing.setdefault("_merged_from", [])
        existing["_merged_from"].append(merged.get("id"))
        if _severity_rank(merged.get("severity", "info")) > _severity_rank(existing.get("severity", "info")):
            existing["severity"] = merged.get("severity", existing.get("severity"))
            existing["priority"] = PRIORITY_MAP.get(existing["severity"], existing.get("priority", "P4"))
        else:
            existing["priority"] = min(existing.get("priority", "P4"), merged.get("priority", "P4"), key=lambda item: PRIORITY_ORDER.get(item, 99))
    return list(groups.values())


def prioritize_findings(findings: list[dict]) -> list[dict]:
    def sort_key(finding: dict) -> tuple[int, int, int, str]:
        return (
            PRIORITY_ORDER.get(finding.get("priority", "P4"), 99),
            SEVERITY_ORDER.get(finding.get("severity", "info"), 99),
            CONFIDENCE_ORDER.get(finding.get("confidence", "low"), 99),
            finding.get("id", ""),
        )

    return sorted(findings, key=sort_key)


def consolidate(challenged_findings: list[dict]) -> dict:
    active = [finding for finding in challenged_findings if finding.get("status") not in {"rejected"}]
    deduped = deduplicate_findings(active)
    prioritized = prioritize_findings(deduped)
    by_domain: dict[str, int] = {}
    for finding in prioritized:
        for domain in finding.get("domains", []):
            by_domain[domain] = by_domain.get(domain, 0) + 1
    return {
        "total_findings": len(prioritized),
        "by_severity": _count_by(prioritized, "severity"),
        "by_domain": by_domain,
        "by_classification": _count_by(prioritized, "classification"),
        "findings": prioritized,
    }


def _dedup_key(finding: dict) -> str:
    evidence = finding.get("evidence") or []
    first_file = evidence[0].get("file", "") if evidence else ""
    return f"{finding.get('category', '')}:{first_file}"


def _severity_rank(severity: str) -> int:
    return {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}.get(severity, 0)


def _count_by(findings: list[dict], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        value = finding.get(field, "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts
