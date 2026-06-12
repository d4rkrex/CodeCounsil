# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.1.0] - 2026-06-12

### Added
- UX Reviewer specialist (frontend accessibility, usability)
- SRE Reviewer specialist (observability, resilience, deployment safety)
- FinOps Reviewer specialist (cloud cost optimization)
- Product Reviewer specialist (requirements traceability, feature completeness)
- Data Privacy Reviewer specialist (GDPR/CCPA, PII handling)
- AI Reviewer specialist (prompt injection, model safety, AI ethics)
- Specialist extension registry (`agents/REGISTRY.md`)
- Conditional specialist selection based on project context

## [1.0.0] - 2026-06-12

### Added
- Initial MVP release
- Core orchestration pipeline (discovery → evidence → selection → analysis → challenge → consolidation → reporting)
- 7 MVP specialist agents
- JSON Schema validated findings
- Execution manifest audit trail
- Security mitigations T-001 through T-009
- Claude Code adapter for /project-review
- 31 unit + integration tests
