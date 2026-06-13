from __future__ import annotations

import json
from pathlib import Path


SEVERITY_TO_LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}


def render_sarif(consolidated: dict, project_context: dict, version: str = "1.1.0") -> str:
    """
    Generate SARIF 2.1.0 JSON for CI/CD integration.
    """
    findings = consolidated.get("findings", [])
    rules: list[dict] = []
    results: list[dict] = []
    seen_rules: set[str] = set()
    repo_root = Path(project_context.get("repo_path", "."))

    for finding in findings:
        rule_id = finding.get("id", "CC-UNKNOWN-000")
        level = SEVERITY_TO_LEVEL.get(str(finding.get("severity", "info")).lower(), "note")
        if rule_id not in seen_rules:
            seen_rules.add(rule_id)
            rules.append(
                {
                    "id": rule_id,
                    "name": finding.get("title", rule_id),
                    "shortDescription": {"text": finding.get("title", rule_id)},
                    "fullDescription": {"text": finding.get("observation", "")},
                    "properties": {
                        "precision": finding.get("confidence", "low"),
                        "severity": finding.get("severity", "info"),
                        "priority": finding.get("priority", "P4"),
                        "classification": finding.get("classification", "improvement"),
                        "domains": finding.get("domains", []),
                    },
                }
            )

        result = {
            "ruleId": rule_id,
            "level": level,
            "message": {"text": _message_text(finding)},
            "properties": {
                "priority": finding.get("priority", "P4"),
                "confidence": finding.get("confidence", "low"),
                "classification": finding.get("classification", "improvement"),
                "domains": finding.get("domains", []),
            },
        }

        locations = []
        for evidence in finding.get("evidence", [])[:1]:
            file_path = evidence.get("file", "")
            locations.append(
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": _relativize_path(file_path, repo_root)},
                        "region": {
                            "startLine": int(evidence.get("start_line", 1)),
                            "endLine": int(evidence.get("end_line", evidence.get("start_line", 1))),
                        },
                    },
                    "message": {"text": evidence.get("description", "")},
                }
            )
        if locations:
            result["locations"] = locations

        results.append(result)

    payload = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "CodeCounsil",
                        "version": version,
                        "informationUri": "https://github.com/mroldan/CodeCounsil",
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }
    return json.dumps(payload, indent=2)


def _message_text(finding: dict) -> str:
    observation = finding.get("observation", "").strip()
    impact = finding.get("impact", "").strip()
    if observation and impact:
        return f"{observation} Impact: {impact}"
    return observation or impact or finding.get("title", "CodeCounsil finding")


def _relativize_path(file_path: str, repo_root: Path) -> str:
    path = Path(file_path)
    if path.is_absolute():
        try:
            return str(path.resolve().relative_to(repo_root.resolve()))
        except Exception:
            return path.name
    return str(path)
