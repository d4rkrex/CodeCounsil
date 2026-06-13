from __future__ import annotations

"""
CC-ARCH-002: Thin orchestrator — runs a list of PipelineStage objects
through a shared PipelineContext. All pipeline logic lives in stages.py.
"""

import json
from pathlib import Path
from typing import Optional

from ..config.loader import hash_config, load_config
from ..manifest.manifest import ExecutionManifest
from ..output.workspace import create_safe_workspace, safe_write
from ..selection.profiles import get_profile
from ..validation.validator import validate_findings
from .pipeline import PipelineContext
from .stages import (
    CHECKLIST_MAP,
    SPECIALIST_AGENT_MAP,
    _build_consolidated_output,
    _collect_raw_findings,
    _load_or_default_challenged,
    _write_reporting_artifacts,
    build_full_pipeline,
)

# Re-export constants so existing imports don't break
__all__ = [
    "run_review",
    "run_consolidate_only",
    "SPECIALIST_AGENT_MAP",
    "CHECKLIST_MAP",
]


def run_review(repo_path_str: str, mode: str = "full", diff_branch: Optional[str] = None) -> dict:
    """
    FR-1: Main entry point. Runs the full pipeline on a repository.
    Public API is unchanged — only the internals are restructured.
    """
    repo_path = Path(repo_path_str).resolve()
    config, rejected_overrides = load_config(repo_path)
    workspace = create_safe_workspace(repo_path, config.review.output_directory)
    profile_name = mode if get_profile(mode) else None
    manifest = ExecutionManifest(
        workspace=workspace,
        mode=mode,
        target_repo=repo_path,
        config_hash=hash_config(config),
        effective_config=config.model_dump(mode="json"),
    )
    for key, value in rejected_overrides.items():
        manifest.log_rejected_config(key, value)
    if profile_name:
        manifest.data["change"]["profile"] = profile_name
        manifest._flush()

    ctx = PipelineContext(
        repo_path=repo_path,
        mode=mode,
        diff_branch=diff_branch,
        workspace=workspace,
        config=config,
        manifest=manifest,
        profile=profile_name,
    )

    try:
        for stage in build_full_pipeline():
            stage.execute(ctx)
        manifest.finalize(ctx.consolidated.get("total_findings", 0))
        return ctx.result()
    except Exception as exc:
        manifest.data.setdefault("errors", []).append({
            "stage": "orchestrator",
            "error": str(exc),
            "at": manifest.now(),
        })
        manifest._flush()
        raise


def run_consolidate_only(repo_path_str: str) -> dict:
    """
    FR-1: Re-run challenger → consolidation → reporting only.
    Used after specialist agents have populated .review/raw/*.json.
    """
    repo_path = Path(repo_path_str).resolve()
    config, _ = load_config(repo_path)
    workspace = repo_path / config.review.output_directory

    if not workspace.exists():
        raise FileNotFoundError(
            f"No workspace found at {workspace}. Run a full review first: "
            f"project-review full --repo {repo_path}"
        )

    ctx_path = workspace / "project-context.json"
    project_context = json.loads(ctx_path.read_text()) if ctx_path.exists() else {"repo_path": str(repo_path)}
    tool_results_path = workspace / "tools" / "results.json"
    tool_results = json.loads(tool_results_path.read_text()) if tool_results_path.exists() else {}
    manifest_path = workspace / "execution-manifest.json"
    manifest_data = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}

    raw_findings: list = []
    for json_file in sorted((workspace / "raw").glob("*.json")):
        if json_file.stem in {"invalid-findings", "challenger"}:
            continue
        data = json.loads(json_file.read_text(encoding="utf-8"))
        if isinstance(data, list):
            raw_findings.extend(data)
        elif isinstance(data, dict) and isinstance(data.get("findings"), list):
            raw_findings.extend(data["findings"])

    valid_findings, invalid_findings = validate_findings(raw_findings)
    safe_write(workspace, "raw/invalid-findings.json", json.dumps(invalid_findings, indent=2))

    challenged_path = workspace / "raw" / "challenger.json"
    if challenged_path.exists():
        challenged = json.loads(challenged_path.read_text(encoding="utf-8"))
    else:
        challenged = [
            {**f, "challenger": {"decision": "confirmed", "reasoning": "Auto-confirmed in consolidate-only mode."}, "status": "confirmed"}
            for f in valid_findings
        ]

    safe_write(workspace, "challenged-findings.json", json.dumps(challenged, indent=2))
    consolidated = _build_consolidated_output(workspace, challenged)
    safe_write(workspace, "consolidated-findings.json", json.dumps(consolidated, indent=2))

    _write_reporting_artifacts(
        workspace=workspace,
        consolidated=consolidated,
        project_context=project_context,
        config=config,
        manifest_data=manifest_data,
        tool_results=tool_results,
    )

    return {
        "status": "complete",
        "workspace": str(workspace),
        "findings_count": consolidated["total_findings"],
        "by_severity": consolidated["by_severity"],
        "next_steps": [
            f"Review {workspace}/executive-summary.md",
            f"Review {workspace}/prioritized-backlog.md for action items",
            f"Review {workspace}/remediation-plan.md for P1/P2 fixes",
        ],
    }
