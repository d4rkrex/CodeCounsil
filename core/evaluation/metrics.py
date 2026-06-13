from __future__ import annotations

"""
Evaluation metrics for CodeCounsil output quality.

Roadmap section 4.3: precision, recall, duplicate_rate,
unsupported_claim_rate, severity_accuracy, actionability_rate.
"""

from dataclasses import dataclass, field
from typing import Optional


SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


@dataclass
class EvalResult:
    """Full evaluation result for one fixture project."""

    project: str
    findings_total: int = 0
    known_defects_total: int = 0
    known_defects_detected: int = 0
    false_positives: int = 0
    duplicates: int = 0
    unsupported_claims: int = 0  # findings with no evidence array
    severity_correct: int = 0
    severity_total: int = 0
    forbidden_violations: list = field(default_factory=list)
    matched_defects: list = field(default_factory=list)
    unmatched_defects: list = field(default_factory=list)
    notes: list = field(default_factory=list)

    @property
    def precision(self) -> Optional[float]:
        if self.findings_total == 0:
            return None
        valid = self.findings_total - self.false_positives
        return round(valid / self.findings_total, 3)

    @property
    def recall(self) -> Optional[float]:
        if self.known_defects_total == 0:
            return None
        return round(self.known_defects_detected / self.known_defects_total, 3)

    @property
    def duplicate_rate(self) -> float:
        if self.findings_total == 0:
            return 0.0
        return round(self.duplicates / self.findings_total, 3)

    @property
    def unsupported_claim_rate(self) -> float:
        if self.findings_total == 0:
            return 0.0
        return round(self.unsupported_claims / self.findings_total, 3)

    @property
    def severity_accuracy(self) -> Optional[float]:
        if self.severity_total == 0:
            return None
        return round(self.severity_correct / self.severity_total, 3)

    def passes_thresholds(self, thresholds: dict) -> tuple[bool, list]:
        """Check if this result passes the project's defined thresholds."""
        failures = []
        if "min_recall" in thresholds and self.recall is not None:
            if self.recall < thresholds["min_recall"]:
                failures.append(f"recall {self.recall} < required {thresholds['min_recall']}")
        if "max_false_positive_rate" in thresholds and self.findings_total > 0:
            fpr = self.false_positives / self.findings_total
            if fpr > thresholds["max_false_positive_rate"]:
                failures.append(f"false_positive_rate {fpr:.2f} > max {thresholds['max_false_positive_rate']}")
        if "max_confirmed_findings" in thresholds:
            confirmed = sum(1 for _ in self.matched_defects)  # crude proxy
            if self.false_positives > thresholds["max_confirmed_findings"]:
                failures.append(f"false positives {self.false_positives} > max {thresholds['max_confirmed_findings']}")
        if "max_total_findings" in thresholds:
            if self.findings_total > thresholds["max_total_findings"]:
                failures.append(f"total findings {self.findings_total} > max {thresholds['max_total_findings']}")
        if "max_high_severity_findings" in thresholds:
            pass  # computed during match phase, stored in forbidden_violations
        if self.forbidden_violations:
            failures.extend(self.forbidden_violations)
        return len(failures) == 0, failures

    def summary_dict(self) -> dict:
        return {
            "project": self.project,
            "findings_total": self.findings_total,
            "known_defects": self.known_defects_total,
            "detected": self.known_defects_detected,
            "false_positives": self.false_positives,
            "precision": self.precision,
            "recall": self.recall,
            "duplicate_rate": self.duplicate_rate,
            "unsupported_claim_rate": self.unsupported_claim_rate,
            "severity_accuracy": self.severity_accuracy,
            "forbidden_violations": self.forbidden_violations,
            "matched_defects": [d["id"] for d in self.matched_defects],
            "unmatched_defects": [d["id"] for d in self.unmatched_defects],
            "notes": self.notes,
        }
