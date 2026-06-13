from __future__ import annotations

"""
Concrete pipeline stage implementations.

CC-ARCH-002: Each stage is small, single-responsibility, and independently
testable. Stages share state through PipelineContext.
"""

import json
from pathlib import Path

from ..consolidation.challenger_debate import selective_debate
from ..consolidation.consolidator import consolidate
from ..consolidation.cross_domain import detect_contradictions
from ..discovery.discover import discover_project
from ..evidence.collector import collect_evidence
from ..output.workspace import safe_write
from ..prompts.builder import build_specialist_prompt
from ..reporting.remediation import generate_issue_templates, generate_remediation_plan
from ..reporting.reporter import (
    render_backlog,
    render_executive_summary,
    render_limitations,
    render_technical_report,
)
from ..selection.profiles import get_profile
from ..selection.selector import select_specialists
from ..validation.validator import validate_findings
from .pipeline import PipelineContext, PipelineStage

# ── Asset paths (VT-Spec T-009: resolved from package, never from repo) ──────
_PACKAGE_ROOT = Path(__file__).resolve().parents[2]
_AGENTS_DIR = _PACKAGE_ROOT / "agents"
_CHECKLIST_DIR = _PACKAGE_ROOT / "checklists"

SPECIALIST_AGENT_MAP = {
    "architecture": "software-architect",
    "developer": "senior-developer",
    "qa": "qa-reviewer",
    "security": "appsec-reviewer",
    "ux": "ux-reviewer",
    "sre": "sre-reviewer",
    "database": "database-reviewer",
    "finops": "finops-reviewer",
    "product": "product-reviewer",
    "data_privacy": "data-privacy-reviewer",
    "ai": "ai-reviewer",
    "api_design": "api-design-reviewer",
    "ai_security": "ai-security-reviewer",
    "ai_quality": "ai-quality-reviewer",
    "discovery": "project-discovery",
    "challenger": "findings-challenger",
    "consolidator": "report-consolidator",
}

CHECKLIST_MAP = {
    "architecture": _CHECKLIST_DIR / "architecture.md",
    "developer": _CHECKLIST_DIR / "development.md",
    "qa": _CHECKLIST_DIR / "qa.md",
    "security": _CHECKLIST_DIR / "security.md",
    "ux": _CHECKLIST_DIR / "ux.md",
    "sre": _CHECKLIST_DIR / "sre.md",
    "database": _CHECKLIST_DIR / "database.md",
    "finops": _CHECKLIST_DIR / "finops.md",
    "product": _CHECKLIST_DIR / "product.md",
    "data_privacy": _CHECKLIST_DIR / "data-privacy.md",
    "ai": _CHECKLIST_DIR / "ai.md",
    "api_design": _CHECKLIST_DIR / "api-design.md",
    "ai_security": _CHECKLIST_DIR / "ai-security.md",
    "ai_quality": _CHECKLIST_DIR / "ai-quality.md",
}


class DiscoveryStage(PipelineStage):
    name = "discovery"
    description = "FR-2: Project discovery"

    def run(self, ctx: PipelineContext) -> None:
        ctx.project_context = discover_project(ctx.repo_path, diff_branch=ctx.diff_branch)
        safe_write(ctx.workspace, "project-context.json", json.dumps(ctx.project_context, indent=2))
        ctx.manifest.log_artifact(
            ctx.manifest.data["stages"][-1],
            "project-context.json",
            ctx.workspace / "project-context.json",
        )


class EvidenceCollectionStage(PipelineStage):
    name = "evidence_collection"
    description = "FR-3: Deterministic tool collection"

    def run(self, ctx: PipelineContext) -> None:
        stage = ctx.manifest.data["stages"][-1]
        ctx.tool_results = collect_evidence(ctx.repo_path, ctx.config.tools, stage, ctx.manifest, ctx.workspace)
        
        # Detect appsec-plugins and add to tool_results as advisory info
        from ..reporting.appsec_bridge import detect_appsec_plugins
        appsec_info = detect_appsec_plugins()
        ctx.tool_results["_appsec_plugins"] = {
            "tool": "appsec-plugins",
            "detected": appsec_info["installed"],
            "executed": False,
            "capabilities": appsec_info["capabilities"],
            "suggestion": appsec_info["suggestion"],
            "errors": None,
        }
        
        ctx.manifest.log_artifact(stage, "tool-results.json", ctx.workspace / "tools" / "results.json")


class SpecialistSelectionStage(PipelineStage):
    name = "specialist_selection"
    description = "FR-4: Specialist selection"

    def run(self, ctx: PipelineContext) -> None:
        if ctx.profile:
            profile = get_profile(ctx.profile) or {}
            ctx.project_context["review_profile"] = {
                "name": ctx.profile,
                "description": profile.get("description"),
                "focus": profile.get("focus", []),
            }
        ctx.selected = select_specialists(ctx.profile or ctx.mode, ctx.project_context, ctx.config, ctx.manifest)


class SpecialistPrepStage(PipelineStage):
    name = "specialist_preparation"
    description = "FR-5: Prepare specialist prompts"

    def run(self, ctx: PipelineContext) -> None:
        for specialist in ctx.selected:
            agent_key = SPECIALIST_AGENT_MAP[specialist]
            agent_path = _AGENTS_DIR / agent_key / "agent.md"
            instructions = agent_path.read_text(encoding="utf-8")
            checklist_path = CHECKLIST_MAP.get(specialist)
            if checklist_path:
                prompt = build_specialist_prompt(
                    specialist=specialist,
                    project_context=ctx.project_context,
                    evidence=ctx.tool_results,
                    checklist_path=checklist_path,
                    agent_instructions=instructions,
                )
                safe_write(ctx.workspace, f"raw/{specialist}.json", "[]")
            else:
                prompt = instructions
            safe_write(ctx.workspace, f"raw/{specialist}.prompt.md", prompt)


class ValidationStage(PipelineStage):
    name = "validation"
    description = "FR-8: Schema validation"

    def run(self, ctx: PipelineContext) -> None:
        raw_findings = _collect_raw_findings(ctx.workspace, ctx.selected)
        ctx.valid_findings, invalid_findings = validate_findings(raw_findings)
        safe_write(ctx.workspace, "raw/invalid-findings.json", json.dumps(invalid_findings, indent=2))
        if invalid_findings:
            # Surface as a warning on the stage without failing the pipeline
            stage = ctx.manifest.data["stages"][-1]
            stage.setdefault("notes", f"{len(invalid_findings)} findings failed schema validation")


class ChallengerStage(PipelineStage):
    name = "challenger"
    description = "FR-6: Findings challenger"

    def run(self, ctx: PipelineContext) -> None:
        ctx.challenged = _load_or_default_challenged(ctx.workspace, ctx.valid_findings, ctx.manifest)
        safe_write(ctx.workspace, "challenged-findings.json", json.dumps(ctx.challenged, indent=2))
        ctx.manifest.log_artifact(
            ctx.manifest.data["stages"][-1],
            "challenged-findings.json",
            ctx.workspace / "challenged-findings.json",
        )


class ConsolidationStage(PipelineStage):
    name = "consolidation"
    description = "FR-7: Consolidation"

    def run(self, ctx: PipelineContext) -> None:
        ctx.consolidated = _build_consolidated_output(ctx.workspace, ctx.challenged)
        safe_write(ctx.workspace, "consolidated-findings.json", json.dumps(ctx.consolidated, indent=2))
        ctx.manifest.log_artifact(
            ctx.manifest.data["stages"][-1],
            "consolidated-findings.json",
            ctx.workspace / "consolidated-findings.json",
        )


class ReportingStage(PipelineStage):
    name = "reporting"
    description = "FR-9: Reporting"

    def run(self, ctx: PipelineContext) -> None:
        artifacts = _write_reporting_artifacts(
            workspace=ctx.workspace,
            consolidated=ctx.consolidated,
            project_context=ctx.project_context,
            config=ctx.config,
            manifest_data=ctx.manifest.data,
            tool_results=ctx.tool_results,
        )
        stage = ctx.manifest.data["stages"][-1]
        for artifact in artifacts:
            ctx.manifest.log_artifact(stage, artifact, ctx.workspace / artifact)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _collect_raw_findings(workspace: Path, selected: list) -> list:
    findings = []
    raw_dir = workspace / "raw"
    for specialist in selected:
        path = raw_dir / f"{specialist}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            findings.extend(data)
        elif isinstance(data, dict) and isinstance(data.get("findings"), list):
            findings.extend(data["findings"])
    return findings


def _load_or_default_challenged(workspace: Path, valid_findings: list, manifest) -> list:
    candidate = workspace / "raw" / "challenger.json"
    if candidate.exists():
        data = json.loads(candidate.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for finding in data:
                challenger = finding.get("challenger")
                if isinstance(challenger, dict):
                    manifest.log_challenger_decision(
                        finding.get("id", "unknown"),
                        challenger.get("decision", "pending"),
                        challenger.get("reasoning", ""),
                    )
            return data

    challenged = []
    for finding in valid_findings:
        updated = dict(finding)
        updated.setdefault("challenger", {
            "decision": "confirmed",
            "reasoning": "No challenger override supplied; preserving validated finding.",
        })
        updated["status"] = "confirmed" if updated.get("status") == "pending" else updated.get("status")
        manifest.log_challenger_decision(
            updated.get("id", "unknown"),
            updated["challenger"]["decision"],
            updated["challenger"]["reasoning"],
        )
        challenged.append(updated)
    return challenged


def _build_consolidated_output(workspace: Path, challenged_findings: list[dict]) -> dict:
    debated_findings = selective_debate(challenged_findings)
    _write_debate_prompts(workspace, debated_findings)
    consolidated = consolidate(debated_findings)
    consolidated["contradictions"] = detect_contradictions(debated_findings)
    return consolidated


def _write_debate_prompts(workspace: Path, findings: list[dict]) -> None:
    raw_dir = workspace / "raw"
    for existing in raw_dir.glob("*.debate.md"):
        existing.unlink(missing_ok=True)
    for finding in findings:
        prompt = finding.get("debate_prompt")
        if not prompt:
            continue
        safe_write(workspace, f"raw/{finding.get('id', 'UNKNOWN')}.debate.md", str(prompt))


def _write_reporting_artifacts(
    *,
    workspace: Path,
    consolidated: dict,
    project_context: dict,
    config,
    manifest_data: dict,
    tool_results: dict,
) -> list[str]:
    safe_write(workspace, "executive-summary.md", render_executive_summary(consolidated, project_context, config))
    safe_write(workspace, "technical-report.md", render_technical_report(consolidated, project_context))
    safe_write(workspace, "prioritized-backlog.md", render_backlog(consolidated))
    safe_write(workspace, "limitations.md", render_limitations(manifest_data, tool_results))
    safe_write(workspace, "remediation-plan.md", generate_remediation_plan(consolidated, project_context))

    issues_dir = workspace / "issues"
    if issues_dir.exists():
        for existing in issues_dir.glob("*.md"):
            existing.unlink(missing_ok=True)
    issue_templates = generate_issue_templates(consolidated)
    artifacts = [
        "executive-summary.md",
        "technical-report.md",
        "prioritized-backlog.md",
        "limitations.md",
        "remediation-plan.md",
    ]
    for relative_path, content in issue_templates.items():
        safe_write(workspace, relative_path, content)
        artifacts.append(relative_path)
    return artifacts


# ── Default full pipeline ─────────────────────────────────────────────────────

def build_full_pipeline() -> list:
    """Return the ordered list of stages for a full review."""
    return [
        DiscoveryStage(),
        EvidenceCollectionStage(),
        SpecialistSelectionStage(),
        SpecialistPrepStage(),
        ValidationStage(),
        ChallengerStage(),
        ConsolidationStage(),
        ReportingStage(),
    ]


def build_consolidate_pipeline() -> list:
    """Return the stages for a consolidate-only run (after specialists ran)."""
    return [
        ValidationStage(),
        ChallengerStage(),
        ConsolidationStage(),
        ReportingStage(),
    ]
