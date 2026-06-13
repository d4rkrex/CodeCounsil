from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASELINE_VERSION = "1.0"
CODECOUNSIL_VERSION = "1.1.0"


@dataclass
class BaselineManager:
    repo_path: Path
    data: dict[str, Any]

    @classmethod
    def load(cls, repo_path: str | Path) -> BaselineManager:
        resolved_repo = Path(repo_path).resolve()
        baseline_path = cls._baseline_path_for(resolved_repo)
        if baseline_path.exists():
            data = json.loads(baseline_path.read_text(encoding="utf-8"))
        else:
            now = cls._now()
            data = {
                "version": BASELINE_VERSION,
                "created_at": now,
                "updated_at": now,
                "codecouncil_version": CODECOUNSIL_VERSION,
                "commit": cls._current_commit(resolved_repo),
                "findings": {},
            }
        data.setdefault("findings", {})
        data.setdefault("version", BASELINE_VERSION)
        data.setdefault("codecouncil_version", CODECOUNSIL_VERSION)
        data.setdefault("created_at", cls._now())
        data.setdefault("updated_at", data["created_at"])
        data.setdefault("commit", cls._current_commit(resolved_repo))
        return cls(repo_path=resolved_repo, data=data)

    def save(self) -> None:
        baseline_path = self._baseline_path_for(self.repo_path)
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.data.get("created_at"):
            self.data["created_at"] = self._now()
        self.data["updated_at"] = self._now()
        self.data["codecouncil_version"] = CODECOUNSIL_VERSION
        self.data["commit"] = self._current_commit(self.repo_path)
        baseline_path.write_text(json.dumps(self.data, indent=2), encoding="utf-8")

    def diff(self, new_findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        current_by_id = {finding.get("id"): finding for finding in new_findings if finding.get("id")}
        baseline_findings = self.data.get("findings", {})

        result = {"new": [], "resolved": [], "reintroduced": [], "existing": []}
        seen_ids = set(current_by_id)

        for finding_id, finding in current_by_id.items():
            baseline_entry = baseline_findings.get(finding_id)
            if baseline_entry is None:
                result["new"].append(finding)
                continue

            baseline_status = str(baseline_entry.get("status", "existing")).lower()
            suppression_active = self._suppression_active(baseline_entry)
            if baseline_status == "resolved":
                result["reintroduced"].append(finding)
            elif baseline_status in {"accepted_risk", "false_positive"} and not suppression_active:
                result["reintroduced"].append(finding)
            else:
                result["existing"].append(finding)

        for finding_id, baseline_entry in baseline_findings.items():
            if finding_id in seen_ids:
                continue
            baseline_status = str(baseline_entry.get("status", "existing")).lower()
            if baseline_status in {"existing", "new", "reintroduced"}:
                result["resolved"].append({"id": finding_id, **baseline_entry})

        return result

    def update(self, new_findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        now = self._now()
        diff = self.diff(new_findings)
        findings = self.data.setdefault("findings", {})

        for finding in diff["new"]:
            findings[finding["id"]] = self._build_entry(finding, status="new", now=now)

        for finding in diff["reintroduced"]:
            existing = findings.get(finding["id"], {})
            updated = self._build_entry(
                finding,
                status="reintroduced",
                now=now,
                first_seen=existing.get("first_seen"),
            )
            updated["suppressed"] = False
            updated["suppression_reason"] = None
            updated["suppression_expires"] = None
            findings[finding["id"]] = updated

        for finding in diff["existing"]:
            existing = findings.get(finding["id"], {})
            prior_status = str(existing.get("status", "existing")).lower()
            status = "accepted_risk" if prior_status == "accepted_risk" and self._suppression_active(existing) else "existing"
            updated = self._build_entry(
                finding,
                status=status,
                now=now,
                first_seen=existing.get("first_seen"),
            )
            updated["suppressed"] = bool(existing.get("suppressed", False))
            updated["suppression_reason"] = existing.get("suppression_reason")
            updated["suppression_expires"] = existing.get("suppression_expires")
            findings[finding["id"]] = updated

        for finding in diff["resolved"]:
            finding_id = finding["id"]
            existing = findings.get(finding_id, {})
            existing["status"] = "resolved"
            existing.setdefault("first_seen", finding.get("first_seen", now))
            existing.setdefault("last_seen", finding.get("last_seen", now))
            findings[finding_id] = existing

        self.data["updated_at"] = now
        self.data["commit"] = self._current_commit(self.repo_path)
        return diff

    def suppress(self, finding_id: str, reason: str, expires: str | None = None) -> None:
        findings = self.data.setdefault("findings", {})
        if finding_id not in findings:
            raise KeyError(f"Finding {finding_id} is not present in the baseline")
        findings[finding_id]["status"] = "accepted_risk"
        findings[finding_id]["suppressed"] = True
        findings[finding_id]["suppression_reason"] = reason
        findings[finding_id]["suppression_expires"] = expires
        findings[finding_id]["last_seen"] = self._now()
        self.data["updated_at"] = self._now()

    def filter_new_only(self, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        diff = self.diff(findings)
        selected: list[dict[str, Any]] = []
        for bucket in ("new", "reintroduced"):
            for finding in diff[bucket]:
                baseline_entry = self.data.get("findings", {}).get(finding["id"])
                if baseline_entry and self._suppression_active(baseline_entry):
                    continue
                selected.append(finding)
        return selected

    @staticmethod
    def _baseline_path_for(repo_path: Path) -> Path:
        return repo_path / ".codecouncil" / "baseline.json"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _current_commit(repo_path: Path) -> str:
        try:
            proc = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except Exception:
            return "unknown"
        if proc.returncode != 0:
            return "unknown"
        return proc.stdout.strip() or "unknown"

    def _build_entry(
        self,
        finding: dict[str, Any],
        *,
        status: str,
        now: str,
        first_seen: str | None = None,
    ) -> dict[str, Any]:
        return {
            "title": finding.get("title", "Untitled finding"),
            "severity": finding.get("severity", "info"),
            "status": status,
            "first_seen": first_seen or now,
            "last_seen": now,
            "suppressed": False,
            "suppression_reason": None,
            "suppression_expires": None,
        }

    @staticmethod
    def _suppression_active(entry: dict[str, Any]) -> bool:
        if not entry.get("suppressed", False):
            return False
        expires = entry.get("suppression_expires")
        if not expires:
            return True
        try:
            expiry = datetime.fromisoformat(str(expires).replace("Z", "+00:00"))
        except ValueError:
            return False
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return expiry >= datetime.now(timezone.utc)
