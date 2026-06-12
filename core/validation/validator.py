# FR-8: JSON Schema validation for findings

import json
from pathlib import Path

import jsonschema

_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"


def load_finding_schema() -> dict:
    return json.loads((_SCHEMA_DIR / "finding.schema.json").read_text(encoding="utf-8"))


def validate_finding(finding: dict) -> list[str]:
    schema = load_finding_schema()
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(finding), key=lambda error: list(error.path))
    return [error.message for error in errors]


def validate_findings(findings: list[dict]) -> tuple[list[dict], list[dict]]:
    valid: list[dict] = []
    invalid: list[dict] = []
    for finding in findings:
        errors = validate_finding(finding)
        if errors:
            invalid.append({"finding": finding, "errors": errors})
        else:
            valid.append(finding)
    return valid, invalid
