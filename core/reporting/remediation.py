from __future__ import annotations


def generate_remediation_plan(consolidated: dict, project_context: dict) -> str:
    """
    Generate a structured remediation plan for confirmed findings.
    """
    findings = _high_priority_findings(consolidated)
    lines = [
        "# Remediation Plan",
        "",
        f"**Repository**: {project_context.get('repo_path', 'unknown')}",
        f"**High Priority Findings**: {len(findings)}",
        "",
    ]

    if not findings:
        lines.extend(
            [
                "No P1/P2 confirmed findings require a remediation plan at this time.",
                "",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    for finding in findings:
        acceptance = _acceptance_criteria(finding)
        lines.extend(
            [
                f"## {finding.get('id', 'UNKNOWN')} — {finding.get('title', 'Untitled finding')}",
                "",
                "### 1. Problem summary",
                finding.get("observation", "No problem summary provided."),
                "",
                "### 2. Root cause",
                _root_cause(finding),
                "",
                "### 3. Fix approach",
                finding.get("recommendation", "Define and implement a code-level fix for the affected flow."),
                "",
                "### 4. Test verification criteria",
                *[f"- {item}" for item in acceptance],
                "",
                "### 5. Issue template (GitHub/Jira format)",
                f"- Title: [{finding.get('id', 'UNKNOWN')}] {finding.get('title', 'Untitled finding')}",
                f"- Priority: {finding.get('priority', 'P4')}",
                f"- Severity: {finding.get('severity', 'info').capitalize()}",
                f"- Owner suggestion: {', '.join(finding.get('domains', [])) or 'engineering'}",
                "",
                "### 6. PR description template",
                f"- Summary: Fix {finding.get('id', 'UNKNOWN')} by implementing {finding.get('recommendation', 'the recommended remediation')}",
                "- Validation: Include updated or new automated tests plus any manual verification steps.",
                "- Risk/rollback: Document rollout guardrails and rollback or feature-flag strategy if applicable.",
                "",
                "### 7. Definition of Done",
                *[f"- [ ] {item}" for item in acceptance],
                "- [ ] Relevant reviewer sign-off recorded",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def generate_issue_templates(consolidated: dict) -> dict[str, str]:
    findings = _high_priority_findings(consolidated)
    issues: dict[str, str] = {}
    for finding in findings:
        primary_domain = str((finding.get("domains") or ["codecounsil"])[0]).replace("_", " ").title()
        evidence_lines = [
            f"- `{item.get('file', 'unknown')}:{item.get('start_line', '?')}-{item.get('end_line', '?')}`: {item.get('description', '')}"
            for item in finding.get("evidence", [])
        ] or ["- No direct evidence captured; confirm manually during remediation."]
        acceptance = _acceptance_criteria(finding)
        issues[f"issues/{finding.get('id', 'UNKNOWN')}.md"] = "\n".join(
            [
                f"## [{finding.get('id', 'UNKNOWN')}] {finding.get('title', 'Untitled finding')}",
                "",
                f"**Type**: {primary_domain} Finding  ",
                f"**Severity**: {finding.get('severity', 'info').capitalize()}  ",
                f"**Priority**: {finding.get('priority', 'P4')}  ",
                f"**Effort**: {str(finding.get('effort', 'medium')).capitalize()}  ",
                "",
                "### Problem",
                finding.get("observation", "No problem statement provided."),
                "",
                "### Impact",
                finding.get("impact", "Impact not provided."),
                "",
                "### Evidence",
                *evidence_lines,
                "",
                "### Acceptance Criteria",
                *[f"- [ ] {item}" for item in acceptance],
                "- [ ] Security review sign-off",
                "",
            ]
        ).rstrip() + "\n"
    return issues


def _high_priority_findings(consolidated: dict) -> list[dict]:
    active_statuses = {"confirmed", "upgraded", "downgraded", "merged", "pending"}
    return [
        finding
        for finding in consolidated.get("findings", [])
        if finding.get("priority") in {"P1", "P2"} and finding.get("status") in active_statuses
    ]


def _root_cause(finding: dict) -> str:
    domains = ", ".join(finding.get("domains", [])) or "engineering"
    evidence = finding.get("evidence") or []
    if evidence:
        first = evidence[0]
        location = f"{first.get('file', 'unknown')}:{first.get('start_line', '?')}-{first.get('end_line', '?')}"
        return f"The issue appears rooted in {finding.get('category', 'implementation')} decisions owned by {domains}, first evidenced at {location}."
    return f"The issue appears rooted in {finding.get('category', 'implementation')} decisions owned by {domains}, but more code-level evidence may be needed during remediation."


def _acceptance_criteria(finding: dict) -> list[str]:
    criteria = [f"Implement the recommended fix for {finding.get('id', 'UNKNOWN')}"]
    evidence = finding.get("evidence") or []
    if evidence:
        first = evidence[0]
        criteria.append(f"Add or update automated tests that cover {first.get('file', 'the affected component')}")
    else:
        criteria.append("Add automated coverage for the affected scenario")
    criteria.append("Verify the unsafe path now fails safely or returns the expected guarded response")
    if finding.get("domains"):
        criteria.append(f"Obtain sign-off from the {finding['domains'][0]} reviewer or owning team")
    return criteria
