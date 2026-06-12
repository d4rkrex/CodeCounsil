from __future__ import annotations

# VT-Spec T-002: strict validation, immutable mandatory phases
# VT-Spec T-006: yaml.safe_load only

import hashlib
import json
from pathlib import Path
from typing import Any, Tuple

import yaml

from .models import CodeCounsilConfig

MANDATORY_SPECIALISTS = {"discovery", "security", "challenger", "consolidator"}
IMMUTABLE_SETTINGS = {"review.modify_code": False}


def load_config(repo_path: Path) -> Tuple[CodeCounsilConfig, dict[str, Any]]:
    """Load and validate config. Returns (config, rejected_overrides)."""
    config_path = repo_path / "codecounsil.yaml"
    rejected: dict[str, Any] = {}
    raw: dict[str, Any] = {}

    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle)
        if payload is None:
            raw = {}
        elif not isinstance(payload, dict):
            raise ValueError("codecounsil.yaml must contain a mapping at the document root")
        else:
            raw = payload

    _reject_immutable_overrides(raw, rejected)
    config = CodeCounsilConfig.model_validate(raw)
    return config, rejected


def hash_config(config: CodeCounsilConfig) -> str:
    serialized = json.dumps(config.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(serialized).hexdigest()


def _reject_immutable_overrides(raw: dict[str, Any], rejected: dict[str, Any]) -> None:
    review = raw.setdefault("review", {}) if isinstance(raw.get("review", {}), dict) else {}
    specialists = raw.setdefault("specialists", {}) if isinstance(raw.get("specialists", {}), dict) else {}
    tools = raw.setdefault("tools", {}) if isinstance(raw.get("tools", {}), dict) else {}

    if review.get("modify_code") not in (None, False):
        rejected["review.modify_code"] = review.get("modify_code")
        review["modify_code"] = False

    output_directory = review.get("output_directory")
    if output_directory is not None and not _is_safe_output_directory(str(output_directory)):
        rejected["review.output_directory"] = output_directory
        review["output_directory"] = ".review"

    security_cfg = specialists.get("security")
    if isinstance(security_cfg, dict) and security_cfg.get("enabled") is False:
        rejected["specialists.security.enabled"] = False
        security_cfg["enabled"] = True

    for mandatory in ("discovery", "challenger", "consolidator", "appsec"):
        if mandatory in specialists:
            rejected[f"specialists.{mandatory}"] = specialists.pop(mandatory)

    if "timeout_seconds" in tools:
        tools["timeout_seconds"] = min(int(tools["timeout_seconds"]), 300)

    if "max_file_size_bytes" in tools:
        tools["max_file_size_bytes"] = min(int(tools["max_file_size_bytes"]), 1_048_576)

    if "max_file_count" in tools:
        tools["max_file_count"] = min(int(tools["max_file_count"]), 10_000)

    if "max_output_bytes" in tools:
        tools["max_output_bytes"] = min(int(tools["max_output_bytes"]), 51_200)

    raw["review"] = review
    raw["specialists"] = specialists
    raw["tools"] = tools


def _is_safe_output_directory(value: str) -> bool:
    path = Path(value)
    if path.is_absolute():
        return False
    return all(part not in {"..", ""} for part in path.parts)
