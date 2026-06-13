from __future__ import annotations

"""
Pipeline context and stage protocol for CodeCounsil orchestration.

CC-ARCH-002: Replaces the God Object run_review() with a list of small,
independently testable Stage objects that share a single PipelineContext.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..config.models import CodeCounsilConfig
from ..manifest.manifest import ExecutionManifest


@dataclass
class PipelineContext:
    """
    Shared mutable state passed through the pipeline.
    Each stage reads what it needs and writes its outputs here.
    """

    # ── Setup (immutable after construction) ──────────────────────────
    repo_path: Path
    mode: str
    diff_branch: Optional[str]
    workspace: Path
    config: CodeCounsilConfig
    manifest: ExecutionManifest
    profile: Optional[str] = None

    # ── Populated by stages ───────────────────────────────────────────
    project_context: dict = field(default_factory=dict)
    tool_results: dict = field(default_factory=dict)
    selected: list = field(default_factory=list)
    valid_findings: list = field(default_factory=list)
    challenged: list = field(default_factory=list)
    consolidated: dict = field(default_factory=dict)

    def result(self) -> dict:
        """Build the final return dict for run_review()."""
        prompts = list((self.workspace / "raw").glob("*.prompt.md"))
        next_steps = []
        if self.consolidated.get("total_findings", 0) == 0 and prompts:
            next_steps.append(f"Run each specialist using prompts in {self.workspace}/raw/*.prompt.md")
            next_steps.append(f"Then re-run: project-review --consolidate-only --repo {self.repo_path}")
        else:
            next_steps.append(f"Review {self.workspace}/executive-summary.md")
            next_steps.append(f"Review {self.workspace}/prioritized-backlog.md for action items")
            next_steps.append(f"Review {self.workspace}/remediation-plan.md for P1/P2 fixes")
        return {
            "status": "complete",
            "run_id": self.manifest.run_id,
            "workspace": str(self.workspace),
            "findings_count": self.consolidated.get("total_findings", 0),
            "by_severity": self.consolidated.get("by_severity", {}),
            "specialists_run": self.selected,
            "prompts_generated": [p.name for p in prompts],
            "next_steps": next_steps,
        }


class PipelineStage:
    """
    Base class for pipeline stages.

    Subclasses must set `name` and `description` and implement `run(ctx)`.
    """

    name: str = ""
    description: str = ""

    def run(self, ctx: PipelineContext) -> None:  # pragma: no cover
        raise NotImplementedError

    def execute(self, ctx: PipelineContext) -> None:
        """
        Wrapper: opens a manifest stage before run(), closes it after.
        Marks the stage failed and re-raises on any exception.
        """
        stage = ctx.manifest.begin_stage(self.name, self.description)
        try:
            self.run(ctx)
            ctx.manifest.complete_stage(stage)
        except Exception as exc:
            ctx.manifest.complete_stage(stage, status="failed", error=str(exc))
            raise
        return stage
