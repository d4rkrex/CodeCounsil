# VT-Spec T-006: Jinja2 SandboxedEnvironment + autoescape
# VT-Spec T-009: templates are loaded from package assets, never from the repository

from pathlib import Path

from jinja2 import FileSystemLoader
from jinja2.sandbox import SandboxedEnvironment

_TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "templates"


def _get_env() -> SandboxedEnvironment:
    # VT-Spec T-006: SandboxedEnvironment prevents template code execution.
    return SandboxedEnvironment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=True)


def render_executive_summary(consolidated: dict, project_context: dict, config) -> str:
    return _get_env().get_template("executive-summary.md.j2").render(consolidated=consolidated, project=project_context, config=config)


def render_technical_report(consolidated: dict, project_context: dict) -> str:
    return _get_env().get_template("technical-report.md.j2").render(consolidated=consolidated, project=project_context)


def render_backlog(consolidated: dict) -> str:
    return _get_env().get_template("backlog.md.j2").render(consolidated=consolidated)


def render_limitations(manifest_data: dict, tool_results: dict) -> str:
    missing_tools = [name for name, result in tool_results.items() if not result.get("executed")]
    excluded = manifest_data.get("specialists_excluded", [])
    errors = manifest_data.get("errors", [])

    lines = ["# Analysis Limitations", ""]
    if missing_tools:
        lines.extend(["## Tools Not Executed", *[f"- {tool}" for tool in missing_tools], ""])
    if excluded:
        lines.append("## Specialists Not Executed")
        lines.extend(f"- **{item['name']}**: {item['reason']}" for item in excluded)
        lines.append("")
    if errors:
        lines.append("## Errors During Analysis")
        lines.extend(f"- Stage `{item['stage']}`: {item['error']}" for item in errors)
        lines.append("")
    if len(lines) == 2:
        lines.append("No analysis limitations recorded.")
    return "\n".join(lines).rstrip() + "\n"
