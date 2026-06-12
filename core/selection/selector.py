# FR-4: Specialist selection with reason logging

from ..manifest.manifest import ExecutionManifest

DOMAIN_SPECIALISTS = ["architecture", "developer", "qa", "security"]
MANDATORY_SPECIALISTS = ["discovery", "challenger", "consolidator"]
MODE_MAP = {
    "full": DOMAIN_SPECIALISTS,
    "architecture": ["architecture"],
    "developer": ["developer"],
    "qa": ["qa"],
    "security": ["security"],
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
        if specialist == "qa" and not project_context.get("tests", {}).get("present"):
            manifest.log_specialist_excluded(specialist, "No test infrastructure detected")
            continue
        manifest.log_specialist_selected(specialist, f"Requested in mode={mode}")
        selected.append(specialist)

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
