from __future__ import annotations

# FR-4: Specialist selection with reason logging

from ..manifest.manifest import ExecutionManifest

MVP_SPECIALISTS = ["architecture", "developer", "qa", "security"]
V11_SPECIALISTS = ["ux", "sre", "finops", "product", "data_privacy", "ai"]
DOMAIN_SPECIALISTS = MVP_SPECIALISTS + V11_SPECIALISTS
MANDATORY_SPECIALISTS = ["discovery", "challenger", "consolidator"]
SPECIALIST_CONDITIONS = {
    "qa": lambda ctx: ctx.get("tests", {}).get("present", False),
    "ux": lambda ctx: ctx.get("frontend", {}).get("present", False),
    "sre": lambda ctx: bool(ctx.get("iac") or ctx.get("pipelines")),
    "finops": lambda ctx: any(
        "terraform" in str(file_name).lower() or "cloudformation" in str(file_name).lower()
        for file_name in ctx.get("iac", [])
    ),
    "product": lambda ctx: bool(ctx.get("documentation")),
    "data_privacy": lambda ctx: True,
    "ai": lambda ctx: ctx.get("has_ai_libraries", False),
}
EXCLUSION_REASONS = {
    "qa": "No test infrastructure detected",
    "ux": "No frontend detected",
    "sre": "No IaC or deployment pipeline detected",
    "finops": "No Terraform or CloudFormation detected",
    "product": "No project documentation detected",
    "ai": "No AI/ML libraries detected",
}
MODE_MAP = {
    "full": DOMAIN_SPECIALISTS,
    "architecture": ["architecture"],
    "developer": ["developer"],
    "qa": ["qa"],
    "security": ["security"],
    "ux": ["ux"],
    "sre": ["sre"],
    "finops": ["finops"],
    "product": ["product"],
    "data_privacy": ["data_privacy"],
    "ai": ["ai"],
}


def select_specialists(mode: str, project_context: dict, config, manifest: ExecutionManifest) -> list[str]:
    requested = _requested_specialists(mode)
    selected: list[str] = []

    for specialist in DOMAIN_SPECIALISTS:
        if specialist not in requested:
            manifest.log_specialist_excluded(specialist, f"Not requested in mode={mode}")
            continue
        specialist_config = getattr(config.specialists, specialist)
        if not specialist_config.enabled:
            manifest.log_specialist_excluded(specialist, "Disabled in config")
            continue
        condition = SPECIALIST_CONDITIONS.get(specialist)
        if condition and not condition(project_context):
            manifest.log_specialist_excluded(specialist, EXCLUSION_REASONS.get(specialist, "Selection conditions not met"))
            continue
        manifest.log_specialist_selected(specialist, f"Requested in mode={mode}")
        selected.append(specialist)

    # VT-Spec T-002: mandatory phases remain enforced separately from optional domain specialists, including v1.1 reviewers.
    for mandatory in MANDATORY_SPECIALISTS:
        manifest.log_specialist_selected(mandatory, "VT-Spec T-002: mandatory — cannot be excluded")
        if mandatory not in selected:
            selected.append(mandatory)

    return selected


def _requested_specialists(mode: str) -> list[str]:
    normalized = (mode or "full").strip().lower()
    if "," in normalized:
        requested = [item.strip() for item in normalized.split(",") if item.strip()]
        return [item for item in requested if item in DOMAIN_SPECIALISTS]
    return MODE_MAP.get(normalized, DOMAIN_SPECIALISTS)
