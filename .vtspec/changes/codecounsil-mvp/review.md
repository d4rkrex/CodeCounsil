---
spec_hash: "sha256:95b10d91750bac2d00299d9e8894b79869928e5096e47693469a26da66a43c77"
posture: "elevated"
findings_count: 9
critical_count: 4
risk_level: "critical"
timestamp: "2026-06-12T14:37:31.023Z"
change: "codecounsil-mvp"
---

# Security Review: codecounsil-mvp

**Posture**: elevated | **Risk Level**: critical | **Findings**: 9 (4 critical)

## STRIDE Analysis

### Spoofing

#### T-001: Specialist identity spoofing through untrusted evidence and config

- **Severity**: high
- **Description**: Attacker goal: make fabricated conclusions appear to come from a trusted specialist or trusted framework component. Attack vector: place crafted repository text, fake prior .review artifacts, or repo-controlled codecounsil.yaml fields that are later surfaced verbatim in prompts or reports so the output reads as if the AppSec reviewer, challenger, or consolidator produced the statement.
- **Mitigation**: Treat repository text and repo-provided metadata as untrusted evidence only; never allow repo content to set specialist names, roles, trust labels, or adjudication status. Prefix all quoted repo content with explicit provenance, render prior findings as data not authority, and sign internally generated artifacts with framework-generated metadata separate from repo-controlled fields.
- **Affected Components**: codecounsil.yaml parser, prompt assembly, raw specialist outputs, report templates, execution-manifest.json

### Tampering

#### T-002: Pipeline tampering via repository-controlled configuration

- **Severity**: critical
- **Description**: Attacker goal: suppress reviewers, alter scope, or weaken controls. Attack vector: commit a malicious codecounsil.yaml that disables AppSec or challenger phases, changes output paths, lowers timeouts, alters tool settings, or constrains review focus so risky files are skipped while appearing policy-compliant.
- **Mitigation**: Use an allowlisted schema with strict validation, immutable security-critical defaults, and precedence rules where repository config cannot disable mandatory phases, reduce logging, change trust boundaries, or redirect outputs outside a sandboxed workspace. Record effective config and rejected options in execution-manifest.json.
- **Affected Components**: codecounsil.yaml, config loader, specialist selection, tool orchestration, output management

#### T-003: Filesystem tampering through pre-existing .review paths and symlinks

- **Severity**: critical
- **Description**: Attacker goal: overwrite arbitrary files, hide evidence, or poison future runs. Attack vector: include pre-existing .review content, symlinks, hard links, or path traversal primitives so framework writes reports or tool outputs into attacker-chosen locations or reads forged artifacts as trusted intermediate state.
- **Mitigation**: Create a fresh dedicated output directory outside repo-controlled paths or fully recreate .review with symlink/hardlink checks, O_NOFOLLOW semantics, canonical path validation, and restrictive permissions. Never trust pre-existing .review content as input unless separately verified and versioned.
- **Affected Components**: .review directory, report writer, tool result storage, consolidation stage

### Repudiation

#### T-004: Incomplete audit trail for tools and agent decisions

- **Severity**: high
- **Description**: Attacker goal: run the pipeline or trigger risky execution without durable attribution. Attack vector: exploit modes or error paths that do not record exact commands, prompts, tool versions, selected specialists, rejected findings, config provenance, or early termination causes, enabling later denial of what ran and why a finding was suppressed.
- **Mitigation**: Make execution-manifest.json append-only and mandatory for every stage, including failures and dry runs. Log effective config hash, command lines, working directory, tool versions, timestamps, artifact digests, specialist prompts/context digests, challenger decisions, and abort reasons before executing each stage.
- **Affected Components**: execution-manifest.json, adapter, tool runner, challenger, consolidator

### Information Disclosure

#### T-005: Prompt injection and tool-output injection leaking host secrets

- **Severity**: critical
- **Description**: Attacker goal: exfiltrate secrets or sensitive local context from the reviewer environment. Attack vector: embed instructions in README, comments, test fixtures, generated files, or tool output that coerce agents to reveal environment variables, hidden files, prior prompts, or challenger instructions into .review artifacts or outbound model requests.
- **Mitigation**: Enforce structured prompt boundaries, quote/escape all untrusted content, strip tool control sequences, prohibit agents from reading outside an explicit allowlist, redact secrets before prompt inclusion and before report emission, and gate outbound model context to minimal excerpts with provenance tags. Add automated prompt-injection regression tests.
- **Affected Components**: project discovery, prompt assembly, LLM adapters, tool output normalization, reports

#### T-006: Template or parser injection exposing server-side data

- **Severity**: high
- **Description**: Attacker goal: execute template expressions or trigger unsafe deserialization to expose local data. Attack vector: malicious findings, config values, or repository snippets reach Jinja2 rendering without autoescaping/strict sandboxing, or YAML is parsed with unsafe loaders allowing object construction or unexpected type coercion that changes rendering behavior.
- **Mitigation**: Render reports with Jinja2 SandboxedEnvironment or a logic-less renderer, enable autoescape for all human-readable outputs, treat all finding fields as data only, and parse YAML with safe_load plus strict schemas and scalar-only constraints where possible. Reject custom tags/anchors beyond an allowlist.
- **Affected Components**: Jinja2 templates, YAML config parser, report generation, finding normalization

### Denial of Service

#### T-007: Resource exhaustion from hostile repositories and tool workloads

- **Severity**: high
- **Description**: Attacker goal: stall or crash review execution. Attack vector: provide extremely large files, deep trees, circular symlinks, decompression bombs, huge dependency graphs, pathological regex inputs, or expensive test/tool commands that exceed CPU, memory, disk, token, or API budgets during discovery, scanning, prompt creation, or report rendering.
- **Mitigation**: Apply per-file and total repository size limits, symlink depth controls, file-count ceilings, subprocess CPU/memory/time quotas, token budgets, and cancellation thresholds. Skip or summarize oversized artifacts, and record truncation decisions explicitly in the manifest.
- **Affected Components**: project discovery, tool runner, dependency scanning, LLM context builder, reporting pipeline

### Elevation of Privilege

#### T-008: Arbitrary code execution through deterministic tool invocation on untrusted code

- **Severity**: critical
- **Description**: Attacker goal: gain code execution on the reviewer host or CI runner. Attack vector: abuse tool collection to run tests, linters, package managers, build hooks, language plugins, or repo-defined scripts that execute attacker-controlled code despite the framework's read-only intent; read-only repository access does not prevent subprocess execution side effects or network egress.
- **Mitigation**: Do not execute repo-defined scripts on the host. Run all deterministic tools inside an isolated sandbox/VM/container with read-only bind mounts, no host credentials, blocked network by default, ephemeral filesystem, and an allowlist of exact binaries/arguments. Prefer passive parsers over build/test execution for elevated posture unless explicitly approved.
- **Affected Components**: tool collection, subprocess execution, CI runners, package ecosystems, adapter invocation

#### T-009: Privilege escalation through permissive adapter and plugin extensibility

- **Severity**: high
- **Description**: Attacker goal: extend trusted execution with malicious code paths. Attack vector: exploit the framework's plugin points, adapter loading, or specialist registration so untrusted repo content, local paths, or environment variables cause loading of attacker-chosen modules, prompts, or templates with the framework's privileges.
- **Mitigation**: Keep plugins/adapters outside analyzed repos, require signed or allowlisted extension packages, disable dynamic imports from target repositories, and separate framework code from repository workspaces. Resolve templates/prompts from immutable installed assets only.
- **Affected Components**: plugin registration, adapter loading, agent definitions, template lookup, Python import path

## OWASP Top 10 Mapping

| OWASP ID | Category | Related Threats | Applicable |
|----------|----------|-----------------|------------|
| A01:2021 | Broken Access Control | T-008, T-009 | Yes |
| A03:2021 | Injection | T-005, T-006, T-008 | Yes |
| A04:2021 | Insecure Design | T-002, T-003, T-007, T-008, T-009 | Yes |
| A05:2021 | Security Misconfiguration | T-002, T-003, T-006, T-008, T-009 | Yes |
| A06:2021 | Vulnerable and Outdated Components | T-008 | Yes |
| A07:2021 | Identification and Authentication Failures | T-001 | Yes |
| A08:2021 | Software and Data Integrity Failures | T-002, T-003, T-008, T-009 | Yes |
| A09:2021 | Security Logging and Monitoring Failures | T-004 | Yes |
| A10:2021 | Server-Side Request Forgery | T-005, T-008 | Yes |

## Abuse Cases

| ID | Severity | As an attacker, I want to... | STRIDE |
|----|----------|------------------------------|--------|
| AC-001 | 🔴 critical | As an attacker, I want to execute code on the reviewer machine by getting deterministic collection to run repository-controlled tests or hooks. | Elevation of Privilege |
| AC-002 | 🔴 critical | As an attacker, I want to leak host secrets by embedding instructions in repository content that the LLM follows during analysis. | Information Disclosure |
| AC-003 | 🔴 critical | As an attacker, I want to tamper with host files by making the framework write results through repository-controlled links. | Tampering |
| AC-004 | 🟠 high | As an attacker, I want to reduce scrutiny by changing repo configuration so key reviewers never run. | Tampering |
| AC-005 | 🟠 high | As an attacker, I want to expose server-side data by smuggling executable expressions into report fields or config. | Information Disclosure |
| AC-006 | 🟠 high | As an attacker, I want to deny service by making the framework spend excessive resources on my repository. | Denial of Service |
| AC-007 | 🟠 high | As an attacker, I want to avoid attribution by exploiting code paths that do not produce complete audit records. | Repudiation |

### AC-001: Repo-defined test execution for host compromise

- **Severity**: 🔴 Critical
- **Goal**: As an attacker, I want to execute code on the reviewer machine by getting deterministic collection to run repository-controlled tests or hooks.
- **Technique**: Commit malicious test files, package hooks, or linter plugins that spawn shells, read environment variables, or beacon data when the framework invokes pytest/npm/make or similar tools during evidence collection.
- **Preconditions**: Framework executes repo-defined tools or scripts; Sandboxing/network controls are absent or weak
- **Impact**: Host compromise, credential theft, lateral movement, and tampering with review outputs.
- **Mitigation**: Run tools only inside isolated sandboxes with no credentials, no host mounts beyond read-only source, no network by default, and an allowlist of binaries/arguments.
- **STRIDE**: Elevation of Privilege
- **Testable**: Yes
- **Test Hint**: Add a fixture repo whose test command attempts to read an env var and write outside workspace; assert containment and failure.

### AC-002: Prompt injection exfiltrates secrets into reports

- **Severity**: 🔴 Critical
- **Goal**: As an attacker, I want to leak host secrets by embedding instructions in repository content that the LLM follows during analysis.
- **Technique**: Place adversarial text in README/comments/tool output instructing agents to disclose environment variables, hidden prompts, or local files in the final report or outbound model context.
- **Preconditions**: Repository content is passed directly into prompts; Agents have access to sensitive local context or prior outputs
- **Impact**: Exposure of API keys, tokens, system prompts, local paths, or unrelated code in .review artifacts or model provider traffic.
- **Mitigation**: Use rigid prompt segmentation, provenance labels, content quoting, secret scrubbing, and explicit agent policies that ignore instructions from untrusted repository text.
- **STRIDE**: Information Disclosure
- **Testable**: Yes
- **Test Hint**: Seed a repo with known prompt-injection strings and canary secrets; assert no canary appears in prompts or reports.

### AC-003: Symlinked .review path overwrites arbitrary files

- **Severity**: 🔴 Critical
- **Goal**: As an attacker, I want to tamper with host files by making the framework write results through repository-controlled links.
- **Technique**: Commit .review entries or nested paths as symlinks/hardlinks to sensitive locations so report generation or tool output persistence writes outside the intended workspace.
- **Preconditions**: Framework writes into a repo-controlled output path; Symlink or canonical path checks are missing
- **Impact**: File overwrite, corruption of evidence, poisoning of future runs, or modification of adjacent project files.
- **Mitigation**: Use a fresh sandboxed output directory, reject links, validate canonical destinations, and open files with no-follow semantics.
- **STRIDE**: Tampering
- **Testable**: Yes
- **Test Hint**: Create fixture symlinks in .review and verify the run aborts before any write.

### AC-004: Malicious config suppresses AppSec and challenger

- **Severity**: 🟠 High
- **Goal**: As an attacker, I want to reduce scrutiny by changing repo configuration so key reviewers never run.
- **Technique**: Add codecounsil.yaml values that toggle specialists off, narrow paths, downgrade timeouts, or redirect outputs while keeping the invocation seemingly legitimate.
- **Preconditions**: Repository config can override security-critical defaults; No immutable mandatory stage enforcement
- **Impact**: Missed vulnerabilities, misleading clean reports, and weak auditability.
- **Mitigation**: Make security-critical stages mandatory and non-overridable, validate config against a strict schema, and log rejected overrides in the manifest.
- **STRIDE**: Tampering
- **Testable**: Yes
- **Test Hint**: Provide a config attempting to disable mandatory stages and verify the framework rejects it and records the rejection.

### AC-005: Template/YAML injection reveals local data

- **Severity**: 🟠 High
- **Goal**: As an attacker, I want to expose server-side data by smuggling executable expressions into report fields or config.
- **Technique**: Craft finding text or metadata containing Jinja2 expressions or malicious YAML constructs that trigger unsafe rendering or object creation when reports are generated.
- **Preconditions**: Unsafe YAML loader or unsandboxed Jinja2 rendering is used; Untrusted strings are rendered as templates
- **Impact**: Disclosure of local files/configuration, corrupted reports, or potential code execution depending on parser behavior.
- **Mitigation**: Use safe YAML parsing, sandboxed Jinja2 with autoescape, and ensure user/repo content is data-only, never template source.
- **STRIDE**: Information Disclosure
- **Testable**: Yes
- **Test Hint**: Inject Jinja2/YAML payloads in fixture findings/config and confirm literal rendering or schema rejection.

### AC-006: Resource bomb stalls discovery and analysis

- **Severity**: 🟠 High
- **Goal**: As an attacker, I want to deny service by making the framework spend excessive resources on my repository.
- **Technique**: Commit huge binaries, deep trees, circular symlinks, huge lockfiles, compressed bombs, or pathological source patterns that trigger expensive scanning, parsing, or tokenization.
- **Preconditions**: Repository traversal lacks quotas; Tools and LLM context builders process unbounded input
- **Impact**: Timeouts, process crashes, exhausted API budget, and delayed or unavailable reviews.
- **Mitigation**: Apply file count/size limits, traversal guards, timeouts, memory caps, and truncation/summarization rules with explicit logging.
- **STRIDE**: Denial of Service
- **Testable**: Yes
- **Test Hint**: Use oversized and recursive fixture repos to confirm deterministic fail-closed behavior under quotas.

### AC-007: Unlogged execution path enables repudiation

- **Severity**: 🟠 High
- **Goal**: As an attacker, I want to avoid attribution by exploiting code paths that do not produce complete audit records.
- **Technique**: Trigger early exits, adapter-specific execution, or failure cases where commands, prompts, or rejected findings are not persisted to execution-manifest.json.
- **Preconditions**: Manifest creation is not atomic/mandatory for all stages; Failure paths bypass logging
- **Impact**: Inability to prove what ran, why findings changed, or whether the pipeline was policy-compliant.
- **Mitigation**: Log before execution, require manifest completion even on errors, and hash all critical artifacts and prompts.
- **STRIDE**: Repudiation
- **Testable**: Yes
- **Test Hint**: Force failures at each stage and verify manifest completeness against a schema.

## Mitigations Required

- [ ] Sandbox all deterministic tool execution with no host secrets and network disabled by default
- [ ] Strictly validate codecounsil.yaml and prevent repo config from disabling mandatory security controls
- [ ] Isolate output handling from repo-controlled .review paths and block symlink/path traversal abuse
- [ ] Implement prompt-injection-resistant context handling with secret redaction and provenance tagging
- [ ] Use safe YAML loading and sandboxed/escaped Jinja2 rendering
- [ ] Enforce complete append-only execution manifests for every stage including failures
