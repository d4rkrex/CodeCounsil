from __future__ import annotations

"""
Evaluation harness: loads a fixture project's findings and ground truth,
then computes metrics.

Usage:
    from core.evaluation.harness import evaluate_fixture
    result = evaluate_fixture(Path("tests/evaluation/vulnerable-project"))
"""

import json
from pathlib import Path
from typing import Optional

from .metrics import EvalResult, SEVERITY_RANK


def evaluate_fixture(fixture_path: Path, review_output_dir: str = ".review") -> EvalResult:
    """
    Compare CodeCounsil output against expected_findings.json ground truth.

    The fixture must have already been reviewed (run project-review against it).
    This function only reads and compares — it does not run the review.
    """
    fixture_path = fixture_path.resolve()
    expected_path = fixture_path / "expected_findings.json"
    consolidated_path = fixture_path / review_output_dir / "consolidated-findings.json"

    if not expected_path.exists():
        raise FileNotFoundError(f"No expected_findings.json in {fixture_path}")

    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    result = EvalResult(project=expected.get("project", fixture_path.name))

    # Load actual findings (from review output)
    actual_findings: list[dict] = []
    if consolidated_path.exists():
        data = json.loads(consolidated_path.read_text(encoding="utf-8"))
        actual_findings = data.get("findings", [])

    result.findings_total = len(actual_findings)
    result.known_defects_total = len(expected.get("known_defects", []))

    # Check for unsupported claims (findings without evidence)
    for f in actual_findings:
        evidence = f.get("evidence", [])
        if not evidence:
            result.unsupported_claims += 1

    # Check for duplicates (same category + file)
    seen_keys: set = set()
    for f in actual_findings:
        evidence = f.get("evidence", [])
        first_file = evidence[0].get("file", "") if evidence else ""
        key = (f.get("category", ""), first_file)
        if key in seen_keys and key != ("", ""):
            result.duplicates += 1
        seen_keys.add(key)

    # Match actual findings against known defects
    known_defects = expected.get("known_defects", [])
    matched_ids: set = set()

    for defect in known_defects:
        matched = _match_defect(defect, actual_findings)
        if matched:
            result.known_defects_detected += 1
            result.matched_defects.append(defect)
            # Check severity accuracy
            actual_sev = matched.get("severity", "info")
            min_sev = defect.get("expected_severity_min", "info")
            result.severity_total += 1
            if SEVERITY_RANK.get(actual_sev, 0) >= SEVERITY_RANK.get(min_sev, 0):
                result.severity_correct += 1
            else:
                result.notes.append(
                    f"{defect['id']}: severity {actual_sev} below expected min {min_sev}"
                )
            matched_ids.add(id(matched))
        else:
            result.unmatched_defects.append(defect)

    # Count false positives (findings that don't match any known defect)
    matched_finding_ids = set()
    for defect in known_defects:
        m = _match_defect(defect, actual_findings)
        if m:
            matched_finding_ids.add(id(m))
    result.false_positives = sum(1 for f in actual_findings if id(f) not in matched_finding_ids)

    # Check forbidden outputs for ambiguous/healthy projects
    forbidden = expected.get("forbidden_outputs", [])
    expected_behavior = expected.get("expected_behavior", {})

    # Check healthy-project: no confirmed_findings should exist
    max_confirmed = expected.get("thresholds", {}).get("max_confirmed_findings")
    if max_confirmed is not None:
        confirmed = [f for f in actual_findings if f.get("classification") == "confirmed_finding"]
        if len(confirmed) > max_confirmed:
            result.forbidden_violations.append(
                f"Found {len(confirmed)} confirmed_finding(s), max allowed: {max_confirmed}"
            )

    # Check ambiguous-project: no high-severity confirmed findings
    max_high = expected.get("thresholds", {}).get("max_high_severity_findings")
    if max_high is not None:
        high_confirmed = [
            f for f in actual_findings
            if f.get("classification") == "confirmed_finding"
            and SEVERITY_RANK.get(f.get("severity", "info"), 0) >= SEVERITY_RANK["high"]
        ]
        if len(high_confirmed) > max_high:
            result.forbidden_violations.append(
                f"Found {len(high_confirmed)} high-severity confirmed_finding(s), max allowed: {max_high}"
            )

    return result


def _match_defect(defect: dict, findings: list[dict]) -> Optional[dict]:
    """
    Try to match a known defect against the list of actual findings.
    Requires at least one keyword match to avoid false matches on domain alone.
    """
    keywords = [k.lower() for k in defect.get("keywords", [])]
    expected_domains = defect.get("expected_domains", [])
    expected_classifications = defect.get("expected_classification", [])
    defect_file = defect.get("file", "").lower()

    best: Optional[dict] = None
    best_score = 0

    for finding in findings:
        score = 0
        keyword_hits = 0

        text = " ".join([
            finding.get("title", ""),
            finding.get("observation", ""),
            finding.get("category", ""),
            finding.get("recommendation", ""),
        ]).lower()
        for kw in keywords:
            if kw in text:
                score += 2
                keyword_hits += 1

        finding_domains = finding.get("domains", [])
        if any(d in finding_domains for d in expected_domains):
            score += 1

        if finding.get("classification") in expected_classifications:
            score += 1

        evidence = finding.get("evidence", [])
        for ev in evidence:
            ev_file = ev.get("file", "").lower()
            if defect_file and (defect_file in ev_file or ev_file.endswith(defect_file.split("/")[-1])):
                score += 2

        # Require at least one keyword match to avoid domain-only false matches
        if score > best_score and score >= 2 and (keyword_hits > 0 or not keywords):
            best_score = score
            best = finding

    return best
