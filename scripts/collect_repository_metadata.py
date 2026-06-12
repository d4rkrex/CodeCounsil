#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from core.discovery.discover import discover_project


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect CodeCounsil project metadata")
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--diff", dest="diff_branch", default=None)
    args = parser.parse_args()
    context = discover_project(Path(args.repo), diff_branch=args.diff_branch)
    print(json.dumps(context, indent=2))


if __name__ == "__main__":
    main()
