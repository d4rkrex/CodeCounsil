# Tasks: codecounsil-mvp

**Created**: 2026-06-12T14:40:14.678Z
**Based on**: spec.md + review.md

This task list was generated from the specification with security mitigations injected from the mandatory review.

## Implementation Tasks

*The agent should break the specification into concrete implementation tasks below.*

## Security Mitigations

The following mitigations were identified in the security review and MUST be addressed:

- [ ] [T-001] Treat repository text and repo-provided metadata as untrusted evidence only; never allow repo content to set specialist names, roles, trust labels, or adjudication status. Prefix all quoted repo content with explicit provenance, render prior findings as data not authority, and sign internally generated artifacts with framework-generated metadata separate from repo-controlled fields.
- [ ] [T-002] Use an allowlisted schema with strict validation, immutable security-critical defaults, and precedence rules where repository config cannot disable mandatory phases, reduce logging, change trust boundaries, or redirect outputs outside a sandboxed workspace. Record effective config and rejected options in execution-manifest.json.
- [ ] [T-003] Create a fresh dedicated output directory outside repo-controlled paths or fully recreate .review with symlink/hardlink checks, O_NOFOLLOW semantics, canonical path validation, and restrictive permissions. Never trust pre-existing .review content as input unless separately verified and versioned.
- [ ] [T-004] Make execution-manifest.json append-only and mandatory for every stage, including failures and dry runs. Log effective config hash, command lines, working directory, tool versions, timestamps, artifact digests, specialist prompts/context digests, challenger decisions, and abort reasons before executing each stage.
- [ ] [T-005] Enforce structured prompt boundaries, quote/escape all untrusted content, strip tool control sequences, prohibit agents from reading outside an explicit allowlist, redact secrets before prompt inclusion and before report emission, and gate outbound model context to minimal excerpts with provenance tags. Add automated prompt-injection regression tests.
- [ ] [T-006] Render reports with Jinja2 SandboxedEnvironment or a logic-less renderer, enable autoescape for all human-readable outputs, treat all finding fields as data only, and parse YAML with safe_load plus strict schemas and scalar-only constraints where possible. Reject custom tags/anchors beyond an allowlist.
- [ ] [T-007] Apply per-file and total repository size limits, symlink depth controls, file-count ceilings, subprocess CPU/memory/time quotas, token budgets, and cancellation thresholds. Skip or summarize oversized artifacts, and record truncation decisions explicitly in the manifest.
- [ ] [T-008] Do not execute repo-defined scripts on the host. Run all deterministic tools inside an isolated sandbox/VM/container with read-only bind mounts, no host credentials, blocked network by default, ephemeral filesystem, and an allowlist of exact binaries/arguments. Prefer passive parsers over build/test execution for elevated posture unless explicitly approved.
- [ ] [T-009] Keep plugins/adapters outside analyzed repos, require signed or allowlisted extension packages, disable dynamic imports from target repositories, and separate framework code from repository workspaces. Resolve templates/prompts from immutable installed assets only.
- [ ] [T-009] Run tools only inside isolated sandboxes with no credentials, no host mounts beyond read-only source, no network by default, and an allowlist of binaries/arguments.
- [ ] [T-009] Use rigid prompt segmentation, provenance labels, content quoting, secret scrubbing, and explicit agent policies that ignore instructions from untrusted repository text.
- [ ] [T-009] Use a fresh sandboxed output directory, reject links, validate canonical destinations, and open files with no-follow semantics.
- [ ] [T-009] Make security-critical stages mandatory and non-overridable, validate config against a strict schema, and log rejected overrides in the manifest.
- [ ] [T-009] Use safe YAML parsing, sandboxed Jinja2 with autoescape, and ensure user/repo content is data-only, never template source.
- [ ] [T-009] Apply file count/size limits, traversal guards, timeouts, memory caps, and truncation/summarization rules with explicit logging.
- [ ] [T-009] Log before execution, require manifest completion even on errors, and hash all critical artifacts and prompts.
- [ ] Sandbox all deterministic tool execution with no host secrets and network disabled by default
- [ ] Strictly validate codecounsil.yaml and prevent repo config from disabling mandatory security controls
- [ ] Isolate output handling from repo-controlled .review paths and block symlink/path traversal abuse
- [ ] Implement prompt-injection-resistant context handling with secret redaction and provenance tagging
- [ ] Use safe YAML loading and sandboxed/escaped Jinja2 rendering
- [ ] Enforce complete append-only execution manifests for every stage including failures

### Review Findings Reference

- [T-001] Specialist identity spoofing through untrusted evidence and config
- [T-002] Pipeline tampering via repository-controlled configuration
- [T-003] Filesystem tampering through pre-existing .review paths and symlinks
- [T-004] Incomplete audit trail for tools and agent decisions
- [T-005] Prompt injection and tool-output injection leaking host secrets
- [T-006] Template or parser injection exposing server-side data
- [T-007] Resource exhaustion from hostile repositories and tool workloads
- [T-008] Arbitrary code execution through deterministic tool invocation on untrusted code
- [T-009] Privilege escalation through permissive adapter and plugin extensibility
