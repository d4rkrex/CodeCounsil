from __future__ import annotations

# VT-Spec T-004: append-only execution manifest — log BEFORE execution

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..output.workspace import safe_write


class ExecutionManifest:
    """VT-Spec T-004: Append-only execution manifest written before each stage executes."""

    def __init__(self, workspace: Path, mode: str, target_repo: Path, config_hash: str, effective_config: dict):
        self.workspace = workspace
        self.manifest_path = workspace / "execution-manifest.json"
        self.run_id = str(uuid.uuid4())
        self.data = {
            "run_id": self.run_id,
            "started_at": self.now(),
            "change": {
                "mode": mode,
                "target_repo": str(target_repo.resolve()),
                "config_hash": config_hash,
                "effective_config": effective_config,
            },
            "stages": [],
            "specialists_selected": [],
            "specialists_excluded": [],
            "rejected_config_overrides": {},
            "findings_count": 0,
            "challenger_decisions": [],
            "completed_at": None,
            "errors": [],
        }
        self._flush()

    def begin_stage(self, stage_name: str, notes: str = "") -> dict:
        stage = {
            "stage_name": stage_name,
            "started_at": self.now(),
            "completed_at": None,
            "status": "running",
            "commands": [],
            "tool_results": [],
            "artifact_hashes": {},
            "notes": notes,
        }
        self.data["stages"].append(stage)
        self._flush()
        return stage

    def complete_stage(self, stage: dict, status: str = "complete", error: str | None = None) -> None:
        stage["completed_at"] = self.now()
        stage["status"] = status
        if error:
            self.data["errors"].append({"stage": stage["stage_name"], "error": error, "at": self.now()})
        self._flush()

    def log_command(self, stage: dict, command: list[str], exit_code: int | None, summary: str) -> None:
        stage["commands"].append({"cmd": command, "exit_code": exit_code, "summary": summary, "at": self.now()})
        self._flush()

    def log_tool_result(self, stage: dict, result: dict) -> None:
        stage["tool_results"].append(result)
        self._flush()

    def log_artifact(self, stage: dict, name: str, path: Path) -> None:
        if path.exists():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            stage["artifact_hashes"][name] = f"sha256:{digest}"
            self._flush()

    def log_specialist_selected(self, name: str, reason: str) -> None:
        self.data["specialists_selected"].append({"name": name, "reason": reason})
        self._flush()

    def log_specialist_excluded(self, name: str, reason: str) -> None:
        self.data["specialists_excluded"].append({"name": name, "reason": reason})
        self._flush()

    def log_rejected_config(self, key: str, value: Any) -> None:
        self.data["rejected_config_overrides"][key] = value
        self._flush()

    def log_challenger_decision(self, finding_id: str, decision: str, reasoning: str) -> None:
        self.data["challenger_decisions"].append({
            "finding_id": finding_id,
            "decision": decision,
            "reasoning": reasoning,
            "at": self.now(),
        })
        self._flush()

    def finalize(self, findings_count: int) -> None:
        self.data["completed_at"] = self.now()
        self.data["findings_count"] = findings_count
        self._flush()

    def now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _flush(self) -> None:
        safe_write(self.workspace, "execution-manifest.json", json.dumps(self.data, indent=2, sort_keys=False))
