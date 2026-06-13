from __future__ import annotations

from core.cli import build_parser


def test_cli_supports_new_output_formats_and_profile_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(["--profile", "pre-release", "--output-format", "sarif"])

    assert args.profile == "pre-release"
    assert args.output_format == "sarif"


def test_cli_supports_fail_on_and_new_findings_flags() -> None:
    parser = build_parser()
    args = parser.parse_args(["full", "--fail-on", "high", "--new-findings-only", "--update-baseline"])

    assert args.mode == "full"
    assert args.fail_on == "high"
    assert args.new_findings_only is True
    assert args.update_baseline is True
