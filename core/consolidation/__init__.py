from __future__ import annotations

from .challenger_debate import selective_debate
from .consolidator import consolidate, deduplicate_findings, prioritize_findings
from .cross_domain import detect_contradictions

__all__ = ["consolidate", "deduplicate_findings", "detect_contradictions", "prioritize_findings", "selective_debate"]
