# Specification: codecounsil-mvp

## Overview

CodeCounsil is an extensible multi-disciplinary code review framework. A user issues a single command and receives a consolidated, evidence-based review covering architecture, code quality, QA, and application security.

## Architecture Constraints

- **Two-layer design**: vendor-independent core + platform adapters
- **Core** contains: config, schemas, agent definitions, prompts, checklists, collection scripts, normalization, deduplication, prioritization, report templates
- **Adapters** translate platform-specific invocations to core orchestration (MVP: Claude Code only)
- **No persistent state**: all outputs are files in `.review/` directory
- **No code modification**: the framework is strictly read-only on the analyzed project

## Functional Requirements

### FR-1: Execution Modes

The system supports three modes:
- `full`: runs all specialists
- Focused (e.g., `architecture`, `security`, `qa`, `developer`, or comma-separated)
- `--diff <branch>`: analyzes changes relative to a branch

In all modes, Project Discovery, Findings Challenger, and Report Consolidator always execute.

### FR-2: Project Discovery

Given a repository path,
When discovery runs,
Then it produces `.review/project-context.json` containing:
- languages, frameworks, app type, components, entrypoints
- APIs, databases, external services, IaC, pipelines
- tests, documentation, frontend, auth mechanisms
- config files, dependency managers

### FR-3: Deterministic Evidence Collection

Given a discovered project context,
When tool collection runs,
Then for each tool (linters, type-check, tests, coverage, SAST, SCA, secret scan, container scan, IaC scan, complexity, OpenAPI validation, SBOM):
- detect if available
- attempt execution with timeout
- record: detected, executed, command, exit code, summary, result path, errors
- never treat missing tools as critical findings

### FR-4: Specialist Selection

Given a mode and project context,
When the orchestrator selects specialists,
Then it activates specialists appropriate for the project type and mode,
And it logs which specialists were selected and why,
And it logs which were excluded and why.

### FR-5: Independent Specialist Analysis

Given project context and collected evidence,
When a specialist runs,
Then it:
- reads only the common context (not the full repo)
- analyzes only its domain
- cites files and lines
- differentiates evidence from hypotheses
- declares limitations and assumptions
- assigns confidence levels
- produces findings compliant with the common schema
- does NOT modify code

### FR-6: Findings Challenger

Given all specialist findings,
When the challenger runs,
Then for each finding it evaluates:
- Does evidence support the claim?
- Is there a compensating control?
- Is severity justified?
- Is it a vulnerability, debt, improvement, or preference?
- Are assumptions unverified?
- Is it a duplicate?
- Is the framework correctly interpreted?
- Is the described impact technically possible?
- Is the recommendation proportional?

And it can: confirm, reject, downgrade, upgrade, merge, or mark as unverifiable.
And it records justification for each decision.

### FR-7: Consolidation

Given challenged findings,
When consolidation runs,
Then it:
- combines duplicates
- relates cross-domain findings
- avoids multiple tickets for same root cause
- assigns priority separating impact and effort
- generates executive summary, technical report, prioritized backlog
- indicates analysis limitations

### FR-8: Finding Schema Validation

Given any finding produced by a specialist,
When it is submitted,
Then it MUST validate against `schemas/finding.schema.json`,
And it includes: id, title, domains, category, classification, severity, priority, confidence, status, observation, impact, evidence, assumptions, missing_evidence, recommendation, effort.

Classification values: confirmed_finding, probable_risk, design_weakness, documentation_gap, test_gap, improvement, insufficient_evidence.

### FR-9: Output Structure

Given a completed review,
When reports are generated,
Then the output directory contains:
```
.review/
├── project-context.json
├── execution-manifest.json
├── tools/
├── raw/{specialist}.json
├── challenged-findings.json
├── consolidated-findings.json
├── executive-summary.md
├── technical-report.md
├── prioritized-backlog.md
└── limitations.md
```

### FR-10: Configuration

Given an optional `codecounsil.yaml` in the target repository,
When the framework starts,
Then it reads project metadata, review settings, specialist toggles, security focus areas, tool settings, and output directory.
If no config file exists, secure defaults are used.

### FR-11: Claude Code Adapter

Given a user in Claude Code,
When they run `/project-review full` (or focused/diff variants),
Then the adapter translates to core orchestration,
And executes the full pipeline read-only,
And outputs the review artifacts.

## Non-Functional Requirements

### NFR-1: Security

- No code modification on analyzed repos
- No exploit execution
- No external data exfiltration
- Redact tokens and credentials in output
- Treat repository content as untrusted input
- Explicit prompt injection defenses against README, comments, issues, config, docs, tool output, test data

### NFR-2: Extensibility

- New specialists can be added by creating an agent definition directory
- New adapters can be added without modifying core
- Plugin points for: specialist registration, tool registration, output format

### NFR-3: Reproducibility

- Same input produces same structured output
- All commands and tool invocations are logged in execution-manifest.json
- Deterministic tools run before non-deterministic agent analysis

## Scenarios

### Scenario: Full review on a Python web API

Given a repository with a FastAPI application,
And pytest tests exist,
And no SAST tools are installed,
When the user runs `project-review full`,
Then discovery detects Python, FastAPI, SQLAlchemy,
And tool collection runs pytest and records SAST as unavailable,
And all 4 domain specialists execute,
And the challenger reviews all findings,
And the consolidator produces the final reports,
And no finding has classification "confirmed_finding" without high-confidence evidence.

### Scenario: Focused security review

Given a repository with a Node.js Express API,
When the user runs `project-review security`,
Then only AppSec Reviewer executes as domain specialist,
And Project Discovery, Challenger, and Consolidator still execute,
And Architecture, Developer, and QA do not execute.

### Scenario: Diff mode review

Given a repository with changes on branch `feature/payments`,
When the user runs `project-review --diff main`,
Then discovery focuses on changed files and affected components,
And specialists analyze the diff plus transversal impact,
And findings reference specific changed lines where applicable.

### Scenario: Missing tools handled gracefully

Given a repository without any linters or SAST tools installed,
When deterministic collection runs,
Then it records each tool as "not detected",
And no critical finding is generated for missing tools,
And specialists proceed with available evidence only.

### Scenario: Finding deduplication

Given the architect reports "missing input validation on /api/users",
And the security reviewer reports "injection risk on /api/users endpoint",
When the consolidator runs,
Then it identifies these as related to the same root cause,
And produces a single consolidated finding referencing both domains.

### Scenario: Challenger rejects weak finding

Given a specialist reports a HIGH severity finding,
And the evidence is a comment in code saying "TODO: fix this",
When the challenger evaluates it,
Then it downgrades or rejects the finding,
And records reasoning: "insufficient evidence - TODO comment does not constitute a confirmed vulnerability".
