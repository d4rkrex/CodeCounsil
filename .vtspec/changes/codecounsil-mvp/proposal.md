# Proposal: codecounsil-mvp

**Created**: 2026-06-12T14:24:09.579Z

## Intent

Implement the CodeCounsil MVP: an extensible multi-disciplinary code review framework that orchestrates specialized coding agents to produce structured evidence-based findings. Includes vendor-independent core with discovery, orchestration, evidence collection, specialist selection, validation, consolidation, and reporting. MVP agents: Project Discovery, Software Architect, Senior Developer, QA Reviewer, AppSec Reviewer, Findings Challenger, Report Consolidator. Claude Code adapter. JSON Schema validated findings with challenger workflow and prioritized backlog.

## Scope

- core/
- agents/
- schemas/
- checklists/
- scripts/
- adapters/claude-code/
- templates/
- tests/

## Approach

Phase-based: 1) Contracts - JSON schemas, config models, directory structure, fixtures. 2) Core - discovery, tool detection, specialist selection, orchestration, normalization. 3) Agents - prompts and config for 7 MVP specialists. 4) Adapter - Claude Code skill integration. 5) Reports and tests - consolidation, templates, e2e tests. Python core, YAML config, Jinja2 templates.
