from __future__ import annotations

"""
Evaluation runner: runs the harness against all fixture projects and
prints a metrics report.

Usage:
    codecouncil-eval                    # all fixtures
    codecouncil-eval --fixture vulnerable-project
    codecouncil-eval --format json
    codecouncil-eval --gate recall=0.6  # exit 1 if below threshold
"""

import argparse
import json
import sys
from pathlib import Path

from .harness import evaluate_fixture
from .metrics import EvalResult

_EVAL_DIR = Path(__file__).resolve().parents[2] / "tests" / "evaluation"

_ALL_FIXTURES = [
    "vulnerable-project",
    "healthy-project",
    "ambiguous-project",
    "architecture-smells",
    "qa-gaps",
    "authorization-flaws",
]


def run_evaluation(fixtures: list[str], output_format: str = "text") -> tuple[list[EvalResult], bool]:
    """Run evaluation on given fixture names. Returns (results, all_passed)."""
    results = []
    all_passed = True

    for name in fixtures:
        fixture_path = _EVAL_DIR / name
        if not fixture_path.exists():
            print(f"  ⚠️  Fixture not found: {fixture_path}", file=sys.stderr)
            continue

        expected_path = fixture_path / "expected_findings.json"
        if not expected_path.exists():
            print(f"  ⚠️  No expected_findings.json in {fixture_path}", file=sys.stderr)
            continue

        try:
            result = evaluate_fixture(fixture_path)
        except FileNotFoundError as e:
            # Review hasn't been run yet — report as not-evaluated
            result = EvalResult(project=name, notes=[f"No review output: {e}"])

        import json as _json
        thresholds = _json.loads(expected_path.read_text()).get("thresholds", {})
        passed, failures = result.passes_thresholds(thresholds)
        if not passed:
            all_passed = False
            result.notes.extend([f"THRESHOLD FAIL: {f}" for f in failures])

        results.append(result)

    return results, all_passed


def print_text_report(results: list[EvalResult]) -> None:
    print()
    print("=" * 72)
    print("  CodeCounsil Evaluation Report")
    print("=" * 72)

    for r in results:
        passed_sym = "✅" if not r.forbidden_violations and not any("THRESHOLD FAIL" in n for n in r.notes) else "❌"
        print(f"\n{passed_sym} {r.project}")
        print(f"   Findings total   : {r.findings_total}")
        if r.known_defects_total > 0:
            print(f"   Known defects    : {r.known_defects_total}")
            print(f"   Detected         : {r.known_defects_detected}")
            print(f"   Recall           : {r.recall if r.recall is not None else 'N/A'}")
            print(f"   Precision        : {r.precision if r.precision is not None else 'N/A'}")
        print(f"   False positives  : {r.false_positives}")
        print(f"   Duplicate rate   : {r.duplicate_rate}")
        print(f"   Unsupported      : {r.unsupported_claim_rate}")
        if r.severity_total > 0:
            print(f"   Severity acc.    : {r.severity_accuracy}")
        if r.unmatched_defects:
            print(f"   Missed defects   : {', '.join(d['id'] for d in r.unmatched_defects)}")
        if r.forbidden_violations:
            for v in r.forbidden_violations:
                print(f"   ⚠️  {v}")
        if r.notes:
            for n in r.notes:
                print(f"   ℹ️  {n}")

    print()
    print("=" * 72)
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="codecouncil-eval",
        description="Evaluate CodeCounsil output quality against fixture ground truth",
    )
    parser.add_argument(
        "--fixture",
        nargs="+",
        choices=_ALL_FIXTURES,
        default=_ALL_FIXTURES,
        help="Which fixtures to evaluate (default: all)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--gate",
        type=str,
        default=None,
        metavar="METRIC=VALUE",
        help="Exit 1 if metric below threshold, e.g. recall=0.6",
    )
    parser.add_argument(
        "--eval-dir",
        default=None,
        help="Override evaluation fixtures directory",
    )
    args = parser.parse_args()

    global _EVAL_DIR
    if args.eval_dir:
        _EVAL_DIR = Path(args.eval_dir).resolve()

    results, all_passed = run_evaluation(args.fixture, args.format)

    if args.format == "json":
        print(json.dumps([r.summary_dict() for r in results], indent=2))
    else:
        print_text_report(results)

    if not all_passed:
        sys.exit(1)

    if args.gate:
        _check_gate(results, args.gate)


def _check_gate(results: list[EvalResult], gate_expr: str) -> None:
    """Parse 'metric=value' and exit 1 if any result fails."""
    try:
        metric, value_str = gate_expr.split("=", 1)
        threshold = float(value_str)
    except ValueError:
        print(f"Invalid --gate expression: {gate_expr}", file=sys.stderr)
        sys.exit(2)

    for r in results:
        actual = getattr(r, metric, None)
        if actual is not None and actual < threshold:
            print(f"Gate failed: {r.project} {metric}={actual} < {threshold}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
