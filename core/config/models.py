from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SecurityPosture(str, Enum):
    STANDARD = "standard"
    ELEVATED = "elevated"


class SpecialistConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    # VT-Spec T-002: mandatory specialists cannot be disabled.
    # Enforced in loader.py so repository overrides can be rejected and logged.


class ReviewConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    default_mode: str = "full"
    modify_code: bool = False
    require_evidence: bool = True
    minimum_confidence: str = "medium"
    output_directory: str = ".review"

    @field_validator("default_mode")
    @classmethod
    def normalize_mode(cls, value: str) -> str:
        return (value or "full").strip().lower()

    @field_validator("modify_code", mode="before")
    @classmethod
    def force_read_only(cls, value: bool) -> bool:
        # VT-Spec T-002: code modification is immutable and always false.
        return False


class SpecialistsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    architecture: SpecialistConfig = Field(default_factory=SpecialistConfig)
    developer: SpecialistConfig = Field(default_factory=SpecialistConfig)
    qa: SpecialistConfig = Field(default_factory=SpecialistConfig)
    security: SpecialistConfig = Field(default_factory=SpecialistConfig)
    ux: SpecialistConfig = Field(default_factory=SpecialistConfig)
    sre: SpecialistConfig = Field(default_factory=SpecialistConfig)
    finops: SpecialistConfig = Field(default_factory=SpecialistConfig)
    product: SpecialistConfig = Field(default_factory=SpecialistConfig)
    data_privacy: SpecialistConfig = Field(default_factory=SpecialistConfig)
    ai: SpecialistConfig = Field(default_factory=SpecialistConfig)
    api_design: SpecialistConfig = Field(default_factory=SpecialistConfig)
    ai_security: SpecialistConfig = Field(default_factory=SpecialistConfig)
    ai_quality: SpecialistConfig = Field(default_factory=SpecialistConfig)
    # VT-Spec T-002: discovery, challenger, and consolidator are mandatory and not configurable.


class SecurityFocusConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    focus: List[str] = Field(default_factory=lambda: ["authorization", "business_logic", "secrets", "cloud_iam"])


class ToolsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    allow_execution: bool = True
    timeout_seconds: int = Field(default=60)
    max_file_size_bytes: int = Field(default=1_048_576)
    max_file_count: int = Field(default=10_000)
    max_output_bytes: int = Field(default=51_200)

    @field_validator("timeout_seconds", mode="before")
    @classmethod
    def clamp_timeout(cls, value: int) -> int:
        # VT-Spec T-007: subprocess timeout capped at 300 seconds.
        timeout = int(value or 60)
        if timeout < 1:
            return 1
        return min(timeout, 300)

    @field_validator("max_file_size_bytes", mode="before")
    @classmethod
    def clamp_file_size(cls, value: int) -> int:
        # VT-Spec T-007: per-file limit is capped at 1MB.
        size = int(value or 1_048_576)
        return min(size, 1_048_576)

    @field_validator("max_file_count", mode="before")
    @classmethod
    def clamp_file_count(cls, value: int) -> int:
        count = int(value or 10_000)
        return min(count, 10_000)

    @field_validator("max_output_bytes", mode="before")
    @classmethod
    def clamp_output_bytes(cls, value: int) -> int:
        size = int(value or 51_200)
        return min(size, 51_200)


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    description: Optional[str] = None
    criticality: str = "standard"
    environment: str = "unknown"


class CodeCounsilConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    review: ReviewConfig = Field(default_factory=ReviewConfig)
    specialists: SpecialistsConfig = Field(default_factory=SpecialistsConfig)
    security: SecurityFocusConfig = Field(default_factory=SecurityFocusConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
