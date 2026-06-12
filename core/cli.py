import argparse
import json
from pathlib import Path

from .orchestration.orchestrator import run_review


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a CodeCounsil review")
    parser.add_argument("mode", nargs="?", default="full", help="Review mode: full, security, qa, developer, architecture, or comma-separated")
    parser.add_argument("--repo", default=".", help="Target repository path")
    parser.add_argument("--diff", dest="diff_branch", default=None, help="Base branch for diff-aware review")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    summary = run_review(str(Path(args.repo).resolve()), mode=args.mode, diff_branch=args.diff_branch)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
