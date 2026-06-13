from __future__ import annotations

PROFILES = {
    "pre-release": {
        "specialists": ["qa", "security", "sre", "api_design"],
        "focus": ["regressions", "breaking_changes", "deployment_risk", "rollback", "critical_vulnerabilities"],
        "description": "Pre-release readiness check",
    },
    "cloud-migration": {
        "specialists": ["architecture", "security", "sre", "finops", "data_privacy"],
        "focus": ["identity", "networking", "data_migration", "resilience", "rollback", "cost", "compliance"],
        "description": "Cloud migration risk assessment",
    },
    "incident-readiness": {
        "specialists": ["sre", "architecture"],
        "focus": ["observability", "runbooks", "circuit_breakers", "graceful_shutdown", "rollback"],
        "description": "Incident response readiness",
    },
    "new-api": {
        "specialists": ["architecture", "security", "developer", "api_design"],
        "focus": ["http_semantics", "versioning", "idempotency", "rate_limiting", "contracts"],
        "description": "New API design review",
    },
}


def get_profile(name: str | None) -> dict | None:
    normalized = (name or "").strip().lower()
    if not normalized:
        return None
    return PROFILES.get(normalized)
