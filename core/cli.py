import argparse
import json
import sys
from pathlib import Path

from .orchestration.orchestrator import run_consolidate_only, run_review


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="project-review",
        description="Run a CodeCounsil multi-disciplinary code review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  full              Run all available specialists (default)
  security          AppSec reviewer only
  architecture      Architecture reviewer only
  developer         Senior developer reviewer only
  qa                QA reviewer only
  data_privacy      Data Privacy reviewer only
  ux                UX reviewer only (requires frontend)
  sre               SRE reviewer only (requires IaC/pipelines)
  finops            FinOps reviewer only (requires Terraform/CF)
  product           Product reviewer only (requires docs)
  ai                AI reviewer only (requires AI/ML libraries)
  arch,security     Multiple specialists comma-separated

Workflow:
  1. project-review full --repo <path>   -> generates .review/raw/*.prompt.md
  2. Run each specialist agent (e.g. via Claude Code /project-review)
  3. Agents write findings to .review/raw/{specialist}.json
  4. project-review --consolidate-only --repo <path>  -> challenge + report

Examples:
  project-review full --repo .
  project-review security --repo /path/to/repo
  project-review full --repo . --diff main
  project-review --consolidate-only --repo .
  project-review full --repo . --format text
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
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    repo = str(Path(args.repo).resolve())

    try:
        if args.consolidate_only:
            result = run_consolidate_only(repo)
        else:
            result = run_review(repo, mode=args.mode, diff_branch=args.diff_branch)
    except Exception as exc:
        if args.format == "json":
            print(json.dumps({"status": "error", "error": str(exc)}, indent=2))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        _print_text_summary(result)


def _print_text_summary(result: dict) -> None:
    status = result.get("status", "unknown")
    workspace = result.get("workspace", "")
    findings = result.get("findings_count", 0)
    by_sev = result.get("by_severity", {})

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


if __name__ == "__main__":
    main()
