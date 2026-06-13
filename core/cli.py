from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path

from .baseline import BaselineManager
from .orchestration.orchestrator import run_consolidate_only, run_review
from .reporting.reporter import render_technical_report
from .reporting.sarif import render_sarif

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="project-review",
        description="Run a CodeCounsil multi-disciplinary code review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  full              Run all available specialists (default)
  pre-release       Pre-release readiness profile
  cloud-migration   Cloud migration risk profile
  incident-readiness Incident readiness profile
  new-api           New API design profile
  security          AppSec reviewer only
  architecture      Architecture reviewer only
  developer         Senior developer reviewer only
  qa                QA reviewer only
  api_design        API design reviewer only
  data_privacy      Data Privacy reviewer only
  ux                UX reviewer only (requires frontend)
  sre               SRE reviewer only (requires IaC/pipelines)
  finops            FinOps reviewer only (requires Terraform/CF)
  product           Product reviewer only (requires docs)
  ai                AI reviewer only (requires AI/ML libraries)
  ai_security       AI security reviewer only
  ai_quality        AI quality reviewer only
  arch,security     Multiple specialists comma-separated

Workflow:
  1. project-review full --repo <path>   -> generates .review/raw/*.prompt.md
  2. Run each specialist agent (e.g. via Claude Code /project-review)
  3. Agents write findings to .review/raw/{specialist}.json
  4. project-review --consolidate-only --repo <path>  -> challenge + report

Examples:
  project-review full --repo .
  project-review --profile pre-release --repo .
  project-review security --repo /path/to/repo
  project-review full --repo . --diff main
  project-review --consolidate-only --repo .
  project-review full --repo . --output-format text
""",
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="full",
        help="Review mode (default: full)",
    )
    parser.add_argument(
        "--repo",
        default=".",
        help="Target repository path (default: current directory)",
    )
    parser.add_argument(
        "--diff",
        dest="diff_branch",
        default=None,
        metavar="BRANCH",
        help="Base branch for diff-aware review",
    )
    parser.add_argument(
        "--consolidate-only",
        action="store_true",
        default=False,
        help="Re-run challenger+consolidation+reporting only (after specialist agents wrote .json files)",
    )
    parser.add_argument(
        "--profile",
        choices=["pre-release", "cloud-migration", "incident-readiness", "new-api"],
        default=None,
        help="Predefined review profile to run",
    )
    parser.add_argument(
        "--output-format",
        "--format",
        dest="output_format",
        choices=["sarif", "json", "text", "markdown"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--fail-on",
        choices=["critical", "high", "medium", "low"],
        default=None,
        help="Exit with status 1 if findings at or above this severity exist",
    )
    parser.add_argument(
        "--new-findings-only",
        action="store_true",
        default=False,
        help="Only show/report new or reintroduced findings versus .codecouncil/baseline.json",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        default=False,
        help="Update .codecouncil/baseline.json with the current consolidated findings after the run",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    repo = str(Path(args.repo).resolve())
    requested_mode = args.profile or args.mode

    try:
        if args.consolidate_only:
            result = run_consolidate_only(repo)
        else:
            result = run_review(repo, mode=requested_mode, diff_branch=args.diff_branch)
    except Exception as exc:
        if args.output_format == "json":
            print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    project_context, consolidated = _load_workspace_artifacts(result.get("workspace", ""))
    display_consolidated = deepcopy(consolidated)
    output_payload: dict = dict(result)
    baseline_diff = None

    if args.new_findings_only or args.update_baseline:
        baseline = BaselineManager.load(repo)
        baseline_diff = baseline.diff(consolidated.get("findings", []))
        if args.new_findings_only:
            display_consolidated["findings"] = baseline.filter_new_only(consolidated.get("findings", []))
            display_consolidated["total_findings"] = len(display_consolidated["findings"])
            display_consolidated["by_severity"] = _count_by(display_consolidated["findings"], "severity")
            display_consolidated["by_domain"] = _count_domains(display_consolidated["findings"])
            display_consolidated["by_classification"] = _count_by(display_consolidated["findings"], "classification")
            output_payload["findings_count"] = display_consolidated["total_findings"]
            output_payload["by_severity"] = display_consolidated["by_severity"]
            output_payload["baseline_diff"] = {
                key: [item.get("id") for item in value]
                for key, value in baseline_diff.items()
            }
        if args.update_baseline:
            baseline.update(consolidated.get("findings", []))
            baseline.save()

    if args.output_format == "json":
        output_payload["consolidated"] = display_consolidated
        print(json.dumps(output_payload, indent=2))
    elif args.output_format == "sarif":
        print(render_sarif(display_consolidated, project_context))
    elif args.output_format == "markdown":
        print(render_technical_report(display_consolidated, project_context))
    else:
        _print_text_summary(output_payload, display_consolidated)

    if args.fail_on and _has_findings_at_or_above(display_consolidated.get("findings", []), args.fail_on):
        sys.exit(1)


def _load_workspace_artifacts(workspace_str: str) -> tuple[dict, dict]:
    workspace = Path(workspace_str)
    consolidated_path = workspace / "consolidated-findings.json"
    project_context_path = workspace / "project-context.json"
    consolidated = json.loads(consolidated_path.read_text(encoding="utf-8")) if consolidated_path.exists() else {"findings": []}
    project_context = json.loads(project_context_path.read_text(encoding="utf-8")) if project_context_path.exists() else {"repo_path": workspace.parent.as_posix()}
    return project_context, consolidated


def _print_text_summary(result: dict, consolidated: dict | None = None) -> None:
    status = result.get("status", "unknown")
    workspace = result.get("workspace", "")
    consolidated = consolidated or {"findings": []}
    findings = consolidated.get("total_findings", result.get("findings_count", 0))
    by_sev = consolidated.get("by_severity", result.get("by_severity", {}))

    print(f"\n{'='*60}")
    print(f"  CodeCounsil Review — {status.upper()}")
    print(f"{'='*60}")
    print(f"  Run ID   : {result.get('run_id', 'N/A')}")
    print(f"  Workspace: {workspace}")
    print(f"  Findings : {findings}")

    if by_sev:
        print()
        icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "⚪"}
        for sev in ["critical", "high", "medium", "low", "info"]:
            count = by_sev.get(sev, 0)
            if count:
                print(f"  {icons.get(sev, '•')} {sev.capitalize():12s}: {count}")

    next_steps = result.get("next_steps", [])
    if next_steps:
        print("\n  Next steps:")
        for step in next_steps:
            print(f"  → {step}")
    print()


def _has_findings_at_or_above(findings: list[dict], threshold: str) -> bool:
    threshold_rank = SEVERITY_RANK[threshold]
    for finding in findings:
        severity = str(finding.get("severity", "info")).lower()
        if SEVERITY_RANK.get(severity, 99) <= threshold_rank:
            return True
    return False


def _count_by(findings: list[dict], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        value = str(finding.get(field, "unknown"))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _count_domains(findings: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in findings:
        for domain in finding.get("domains", []):
            counts[domain] = counts.get(domain, 0) + 1
    return counts


if __name__ == "__main__":
    main()
