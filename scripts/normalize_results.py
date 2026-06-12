#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from core.consolidation.consolidator import consolidate
from core.validation.validator import validate_findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and normalize CodeCounsil findings")
    parser.add_argument("input", help="Path to a JSON file containing a list of findings")
    args = parser.parse_args()

    findings = json.loads(Path(args.input).read_text(encoding="utf-8"))
    valid, invalid = validate_findings(findings)
    output = {
        "valid": valid,
        "invalid": invalid,
        "consolidated": consolidate(valid),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
