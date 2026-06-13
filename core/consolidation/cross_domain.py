from __future__ import annotations

from itertools import combinations


CONTRADICTION_RULES = [
    {
        "title": "Logging depth versus sensitive data exposure",
        "domains": ("sre", "security"),
        "left_keywords": ("logging", "trace", "telemetry"),
        "right_keywords": ("sensitive", "pii", "secret", "credential", "logs"),
        "description": "SRE recommends broader logging or tracing while Security warns that current logs expose sensitive data.",
        "recommendation": "Adopt structured logging with field allowlists, redaction, and separate secure audit trails for sensitive events.",
    },
    {
        "title": "Session duration trade-off",
        "domains": ("ux", "security"),
        "left_keywords": ("persistent session", "remember me", "session", "login"),
        "right_keywords": ("short session", "expiry", "expiration", "reauth", "session"),
        "description": "Security recommends shorter or stricter sessions while UX signals the main flow may become disruptive or encourage unsafe workarounds.",
        "recommendation": "Use short-lived sessions with rotating refresh tokens and step-up authentication only for sensitive actions.",
    },
    {
        "title": "Caching performance versus consistency risk",
        "domains": ("developer", "architecture"),
        "left_keywords": ("cache", "caching", "performance"),
        "right_keywords": ("stale", "inconsistency", "cache", "invalidat"),
        "description": "Developer guidance favors caching for performance while Architecture highlights invalidation or consistency hazards.",
        "recommendation": "Scope caching to read-safe paths and pair it with explicit invalidation, ownership, and consistency rules.",
    },
    {
        "title": "Security friction versus UX bypass risk",
        "domains": ("security", "ux"),
        "left_keywords": ("mfa", "re-auth", "reauth", "step-up", "approval"),
        "right_keywords": ("bypass", "drop-off", "workaround", "friction", "flow"),
        "description": "Security adds stronger checks, but UX indicates users may bypass or abandon the flow because of excessive friction.",
        "recommendation": "Keep strong controls for risky actions while simplifying low-risk paths and instrumenting friction-driven drop-offs.",
    },
    {
        "title": "Mock-heavy testing versus system realism",
        "domains": ("qa", "architecture"),
        "left_keywords": ("mock", "stub", "fixture", "simulate"),
        "right_keywords": ("integration", "realism", "production-like", "end-to-end"),
        "description": "QA recommends more mocking for coverage while Architecture warns that the system could lose enough realism to hide integration failures.",
        "recommendation": "Balance fast mocked tests with contract and integration tests that exercise real interfaces and failure modes.",
    },
    {
        "title": "Cost reduction versus resilience redundancy",
        "domains": ("finops", "sre"),
        "left_keywords": ("cost", "reduce redundancy", "downsize", "single region", "replica"),
        "right_keywords": ("redundancy", "failover", "replica", "ha", "resilience"),
        "description": "FinOps seeks lower spend by reducing redundancy while SRE identifies redundancy as necessary for resilience or recovery targets.",
        "recommendation": "Quantify resilience requirements first, then right-size redundancy with tiered environments and explicit recovery objectives.",
    },
    {
        "title": "Retention minimization versus historical analytics",
        "domains": ("data_privacy", "product"),
        "left_keywords": ("retention", "delete", "erasure", "minimization"),
        "right_keywords": ("analytics", "history", "historical", "trend", "insight"),
        "description": "Privacy guidance pushes for less retention while Product depends on historical data for analytics or user insight.",
        "recommendation": "Use privacy-preserving aggregation, shorter raw-data retention, and documented consent boundaries for analytics use cases.",
    },
]


def detect_contradictions(findings: list[dict]) -> list[dict]:
    """
    Detect findings from different domains that contradict each other.
    """
    contradictions: list[dict] = []
    seen_pairs: set[tuple[str, str, str]] = set()

    for left, right in combinations(findings, 2):
        for rule in CONTRADICTION_RULES:
            matched = _match_rule(left, right, rule) or _match_rule(right, left, rule)
            if not matched:
                continue
            ordered_ids = tuple(sorted((left.get("id", ""), right.get("id", ""))))
            dedup_key = (rule["title"], ordered_ids[0], ordered_ids[1])
            if dedup_key in seen_pairs:
                continue
            seen_pairs.add(dedup_key)
            contradictions.append(
                {
                    "id": f"CONTRA-{len(contradictions) + 1:03d}",
                    "title": rule["title"],
                    "findings": list(ordered_ids),
                    "domains": list(rule["domains"]),
                    "description": rule["description"],
                    "recommendation": rule["recommendation"],
                }
            )

    return contradictions


def _match_rule(primary: dict, secondary: dict, rule: dict) -> bool:
    left_domain, right_domain = rule["domains"]
    if left_domain not in primary.get("domains", []):
        return False
    if right_domain not in secondary.get("domains", []):
        return False
    return _has_keywords(primary, rule["left_keywords"]) and _has_keywords(secondary, rule["right_keywords"])


def _has_keywords(finding: dict, keywords: tuple[str, ...]) -> bool:
    haystack = " ".join(
        [
            str(finding.get("title", "")),
            str(finding.get("category", "")),
            str(finding.get("observation", "")),
            str(finding.get("impact", "")),
            str(finding.get("recommendation", "")),
        ]
    ).lower()
    return any(keyword.lower() in haystack for keyword in keywords)
