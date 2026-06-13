from __future__ import annotations

import json

from core.reporting.sarif import render_sarif


def test_render_sarif_maps_findings_to_rules_results_and_locations() -> None:
    consolidated = {
        "findings": [
            {
                "id": "CC-SEC-001",
                "title": "Missing authorization check",
                "severity": "high",
                "priority": "P2",
                "classification": "confirmed_finding",
                "confidence": "high",
                "domains": ["security"],
                "observation": "The endpoint is missing an ownership check.",
                "impact": "Users can access records they do not own.",
                "evidence": [
                    {"file": "app.py", "start_line": 10, "end_line": 12, "description": "No auth guard."}
                ],
            }
        ]
    }

    payload = json.loads(render_sarif(consolidated, {"repo_path": "/repo"}))

    assert payload["version"] == "2.1.0"
    driver = payload["runs"][0]["tool"]["driver"]
    assert driver["name"] == "CodeCounsil"
    assert driver["rules"][0]["id"] == "CC-SEC-001"
    result = payload["runs"][0]["results"][0]
    assert result["ruleId"] == "CC-SEC-001"
    assert result["level"] == "error"
    assert result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "app.py"
