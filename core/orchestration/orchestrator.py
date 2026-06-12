# FR-1: Main orchestration — full/focused/diff modes
# VT-Spec T-002: mandatory stages enforced
# VT-Spec T-009: agent and checklist resolution uses package assets only

import json
from pathlib import Path
from typing import Optional

from ..config.loader import hash_config, load_config
from ..consolidation.consolidator import consolidate
from ..discovery.discover import discover_project
from ..evidence.collector import collect_evidence
from ..manifest.manifest import ExecutionManifest
from ..output.workspace import create_safe_workspace, safe_write
from ..prompts.builder import build_specialist_prompt
from ..reporting.reporter import render_backlog, render_executive_summary, render_limitations, render_technical_report
from ..selection.selector import select_specialists
from ..validation.validator import validate_findings

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = PACKAGE_ROOT / "agents"
CHECKLIST_DIR = PACKAGE_ROOT / "checklists"

SPECIALIST_AGENT_MAP = {
    "architecture": "software-architect",
    "developer": "senior-developer",
    "qa": "qa-reviewer",
    "security": "appsec-reviewer",
    "discovery": "project-discovery",
    "challenger": "findings-challenger",
    "consolidator": "report-consolidator",
}

CHECKLIST_MAP = {
    "architecture": CHECKLIST_DIR / "architecture.md",
    "developer": CHECKLIST_DIR / "development.md",
    "qa": CHECKLIST_DIR / "qa.md",
    "security": CHECKLIST_DIR / "security.md",
}


def run_review(repo_path_str: str, mode: str = "full", diff_branch: Optional[str] = None) -> dict:
    repo_path = Path(repo_path_str).resolve()
    config, rejected_overrides = load_config(repo_path)
    config_hash = hash_config(config)
    workspace = create_safe_workspace(repo_path, config.review.output_directory)
    manifest = ExecutionManifest(
        workspace=workspace,
        mode=mode,
        target_repo=repo_path,
        config_hash=config_hash,
        effective_config=config.model_dump(mode="json"),
    )

    for key, value in rejected_overrides.items():
        manifest.log_rejected_config(key, value)

    current_stage = None
    try:
        current_stage = manifest.begin_stage("discovery", "FR-2: Project discovery")
        project_context = discover_project(repo_path, diff_branch=diff_branch)
        safe_write(workspace, "project-context.json", json.dumps(project_context, indent=2))
        manifest.log_artifact(current_stage, "project-context.json", workspace / "project-context.json")
        manifest.complete_stage(current_stage)

        current_stage = manifest.begin_stage("evidence_collection", "FR-3: Deterministic tool collection")
        tool_results = collect_evidence(repo_path, config.tools, current_stage, manifest, workspace)
        manifest.log_artifact(current_stage, "tool-results.json", workspace / "tools" / "results.json")
        manifest.complete_stage(current_stage)

        current_stage = manifest.begin_stage("specialist_selection", "FR-4: Specialist selection")
        selected = select_specialists(mode, project_context, config, manifest)
        manifest.complete_stage(current_stage)

        current_stage = manifest.begin_stage("specialist_preparation", "FR-5: Prepare specialist prompts")
        _prepare_specialist_artifacts(workspace, selected, project_context, tool_results)
        manifest.complete_stage(current_stage)

        current_stage = manifest.begin_stage("validation", "FR-8: Schema validation")
        raw_findings = _collect_raw_findings(workspace, selected)
        valid_findings, invalid_findings = validate_findings(raw_findings)
        safe_write(workspace, "raw/invalid-findings.json", json.dumps(invalid_findings, indent=2))
        if invalid_findings:
            manifest.complete_stage(current_stage, status="complete", error=f"{len(invalid_findings)} findings failed schema validation")
        else:
            manifest.complete_stage(current_stage)

        current_stage = manifest.begin_stage("challenger", "FR-6: Findings challenger")
        challenged = _load_or_default_challenged_findings(workspace, valid_findings, manifest)
        safe_write(workspace, "challenged-findings.json", json.dumps(challenged, indent=2))
        manifest.log_artifact(current_stage, "challenged-findings.json", workspace / "challenged-findings.json")
        manifest.complete_stage(current_stage)

        current_stage = manifest.begin_stage("consolidation", "FR-7: Consolidation")
        consolidated = consolidate(challenged)
        safe_write(workspace, "consolidated-findings.json", json.dumps(consolidated, indent=2))
        manifest.log_artifact(current_stage, "consolidated-findings.json", workspace / "consolidated-findings.json")
        manifest.complete_stage(current_stage)

        current_stage = manifest.begin_stage("reporting", "FR-9: Reporting")
        _write_reports(workspace, consolidated, project_context, config, manifest.data, tool_results)
        manifest.log_artifact(current_stage, "executive-summary.md", workspace / "executive-summary.md")
        manifest.log_artifact(current_stage, "technical-report.md", workspace / "technical-report.md")
        manifest.log_artifact(current_stage, "prioritized-backlog.md", workspace / "prioritized-backlog.md")
        manifest.log_artifact(current_stage, "limitations.md", workspace / "limitations.md")
        manifest.complete_stage(current_stage)

        manifest.finalize(consolidated["total_findings"])
        return {
            "status": "complete",
            "run_id": manifest.run_id,
            "workspace": str(workspace),
            "findings_count": consolidated["total_findings"],
            "by_severity": consolidated["by_severity"],
        }
    except Exception as exc:
        if current_stage is not None:
            manifest.complete_stage(current_stage, status="failed", error=str(exc))
        manifest.data.setdefault("errors", []).append({"stage": "orchestrator", "error": str(exc), "at": manifest.now()})
        manifest._flush()
        raise


def _prepare_specialist_artifacts(workspace: Path, selected: list[str], project_context: dict, tool_results: dict) -> None:
    for specialist in selected:
        agent_key = SPECIALIST_AGENT_MAP[specialist]
        agent_path = AGENTS_DIR / agent_key / "agent.md"
        instructions = agent_path.read_text(encoding="utf-8")
        if specialist in CHECKLIST_MAP:
            prompt = build_specialist_prompt(
                specialist=specialist,
                project_context=project_context,
                evidence=tool_results,
                checklist_path=CHECKLIST_MAP[specialist],
                agent_instructions=instructions,
            )
        else:
            prompt = instructions
        safe_write(workspace, f"raw/{specialist}.prompt.md", prompt)
        if specialist in CHECKLIST_MAP:
            safe_write(workspace, f"raw/{specialist}.json", "[]")


def _collect_raw_findings(workspace: Path, selected: list[str]) -> list[dict]:
    findings: list[dict] = []
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


def _load_or_default_challenged_findings(workspace: Path, valid_findings: list[dict], manifest: ExecutionManifest) -> list[dict]:
    candidate = workspace / "raw" / "challenger.json"
    if candidate.exists():
        data = json.loads(candidate.read_text(encoding="utf-8"))
        if isinstance(data, list):
            for finding in data:
                challenger = finding.get("challenger")
                if isinstance(challenger, dict):
                    manifest.log_challenger_decision(finding.get("id", "unknown"), challenger.get("decision", "pending"), challenger.get("reasoning", ""))
            return data

    challenged: list[dict] = []
    for finding in valid_findings:
        updated = dict(finding)
        updated.setdefault("challenger", {"decision": "confirmed", "reasoning": "No challenger override supplied; preserving validated finding."})
        updated["status"] = "confirmed" if updated.get("status") == "pending" else updated.get("status")
        manifest.log_challenger_decision(updated.get("id", "unknown"), updated["challenger"]["decision"], updated["challenger"]["reasoning"])
        challenged.append(updated)
    return challenged


def _write_reports(workspace: Path, consolidated: dict, project_context: dict, config, manifest_data: dict, tool_results: dict) -> None:
    safe_write(workspace, "executive-summary.md", render_executive_summary(consolidated, project_context, config))
    safe_write(workspace, "technical-report.md", render_technical_report(consolidated, project_context))
    safe_write(workspace, "prioritized-backlog.md", render_backlog(consolidated))
    safe_write(workspace, "limitations.md", render_limitations(manifest_data, tool_results))
