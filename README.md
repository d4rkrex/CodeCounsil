# CodeCounsil

CodeCounsil is a multi-disciplinary, read-only code review framework that combines deterministic repository discovery, safe evidence collection, specialist review prompts, adversarial challenge, and consolidated reporting.

## What is CodeCounsil?

CodeCounsil helps a reviewer run one command and obtain a structured review across architecture, development quality, QA, and application security. The core is vendor-independent and produces portable artifacts. Adapters translate those artifacts into a specific agent platform workflow.

Key properties:

- Read-only analysis of the target repository
- Security-first handling of untrusted repository content
- Deterministic discovery and evidence collection before specialist analysis
- Independent specialist prompts plus challenger and consolidator stages
- Reproducible `.review/` outputs with execution manifest logging

## Installation

```bash
python3 -m pip install -e ".[dev]"
```

This installs the core framework, development dependencies, and the `project-review` CLI entrypoint.

## Usage

### How It Works (Three-Phase Model)

CodeCounsil uses a **three-phase workflow**. Understanding this is key to getting results:

```
Phase 1 — Automated Setup
  project-review full --repo .
  → Discovers the project, runs deterministic tools
  → Generates .review/raw/{specialist}.prompt.md for each specialist
  → .review/ workspace is ready, but findings = 0 (expected!)

Phase 2 — Specialist Analysis (LLM agents)
  Each specialist reads their .prompt.md and writes findings to
  .review/raw/{specialist}.json (via Claude Code, Codex, or manually)

Phase 3 — Consolidation
  project-review --consolidate-only --repo .
  → Challenges all findings, deduplicates, prioritizes
  → Generates .review/executive-summary.md, technical-report.md, backlog
```

The CLI shows guidance on next steps after Phase 1 runs.

### CLI Commands

Run a full review (Phase 1):

```bash
project-review full
```

Run with diff awareness relative to a branch:

```bash
project-review full --diff main
```

Run a focused review (fewer specialists):

```bash
project-review security
project-review architecture,developer
```

After specialist agents write their findings (Phase 2), consolidate (Phase 3):

```bash
project-review --consolidate-only
```

Review another repository path:

```bash
project-review full --repo /path/to/repository
```

Use text output format:

```bash
project-review full --format text
```

## Output Files Explained

A successful run produces:

```text
.review/
├── project-context.json
├── execution-manifest.json
├── tools/
├── raw/
├── challenged-findings.json
├── consolidated-findings.json
├── executive-summary.md
├── technical-report.md
├── prioritized-backlog.md
└── limitations.md
```

- `project-context.json`: repository discovery summary
- `execution-manifest.json`: append-only audit log for stage starts, commands, decisions, and artifact hashes
- `tools/`: deterministic tool outputs and tool-results summary
- `raw/`: specialist prompt bundles and specialist finding payloads
- `challenged-findings.json`: challenger-reviewed findings
- `consolidated-findings.json`: deduplicated, prioritized result set
- `executive-summary.md`: leadership-oriented summary
- `technical-report.md`: finding-by-finding technical report
- `prioritized-backlog.md`: remediation backlog grouped by priority
- `limitations.md`: unavailable tools, excluded specialists, and execution errors

## Known Limitations

### Project Discovery (heuristic-based)

`project-context.json` is produced by heuristic content scanning. **Always review it after Phase 1** before trusting specialist selections.

Common false positives:
- **Frameworks**: if your repo contains documentation, checklists, or agent `.md` files that mention framework names (e.g., `react`, `django`), those may be detected even if the framework is not used. Fixed in v1.1 — framework detection is restricted to source code files.
- **AI libraries**: same as above — `openai`, `langchain` in `.md` docs will not trigger AI detection (restricted to `.py`, `.ts`, `.js` etc.).
- **Databases**: `postgres` or `sqlite` mentioned in docs or test fixtures may appear in `databases`.

If discovery produces wrong results, you can:
1. Check `.review/project-context.json` and manually verify
2. Use focused mode (`project-review security`) to skip specialists for unrelated domains
3. File an issue — detection rules are in `core/discovery/discover.py`

### Tool Execution

Deterministic tools (SAST, SCA, linters) only run if installed on the host. Missing tools are recorded in `.review/limitations.md` and never treated as findings.

For production use, run inside a sandboxed container with tools pre-installed.

## Architecture Overview

CodeCounsil uses a two-layer design:

1. **Core layer**
   - Configuration loading and validation
   - Repository discovery
   - Deterministic evidence collection
   - Specialist selection
   - Schema validation
   - Consolidation and reporting
2. **Adapter layer**
   - Platform-specific commands
   - Agent definitions for a host environment
   - Prompt packaging and execution conventions

The core never depends on repository-defined plugins. Adapters are shipped with the framework package.

## Claude Code Adapter Installation

The Claude Code adapter lives in `adapters/claude-code/`.

1. Copy `adapters/claude-code/skills/project-review/SKILL.md` into your Claude Code skills path.
2. Copy `adapters/claude-code/agents/*.md` into the target repository `.claude/agents/` directory.
3. Invoke `/project-review full`, `/project-review security`, or `/project-review --diff <branch>` from Claude Code.

The adapter instructs Claude Code to call `run_review()` and then surface the generated artifacts.

## Extending with New Specialists

To add a specialist:

1. Create a new agent definition under `agents/<specialist>/agent.md`
2. Add the corresponding checklist if required
3. Update `core/selection/selector.py` with selection rules
4. Update schemas or consolidation rules if the specialist introduces new structured fields
5. Add adapter-specific definitions under `adapters/<adapter>/agents/`
6. Add tests covering selection and output validation

## Security Model

CodeCounsil treats the analyzed repository as untrusted input.

Security controls include:

- Provenance-wrapped repository content in prompts
- Safe YAML parsing and strict Pydantic validation
- Immutable security defaults for mandatory stages
- Fresh workspace creation with symlink and hardlink rejection
- Allowlisted subprocess execution with `shell=False`
- Secret redaction before prompt inclusion
- Sandboxed Jinja2 report rendering with autoescaping
- Package-local template and agent resolution only

For production use, run deterministic tools inside an isolated container or VM with read-only mounts, blocked network by default, and no host credentials.

## Development Setup

```bash
python3 -m pip install -e ".[dev]"
pytest --tb=short
```

Useful helper scripts:

- `scripts/collect_repository_metadata.py`
- `scripts/detect_tooling.py`
- `scripts/normalize_results.py`

## Limitations of the MVP

The MVP prepares specialist prompts and artifacts, but it does not embed a hosted LLM runtime. Platform adapters are expected to execute the prompts and write specialist findings back into `.review/raw/` before consolidation.
