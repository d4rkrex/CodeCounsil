# CodeCounsil × appsec-plugins Integration

This adapter bridges **CodeCounsil** (multi-domain review framework) with the **appsec-plugins** (specialized security skills) to produce deeper, non-duplicated security coverage.

## Why both?

| | CodeCounsil | appsec-plugins |
|---|---|---|
| **Strength** | Multi-domain orchestration, challenger, baseline, SARIF, dedup | Deep threat modeling (STRIDE+DREAD), OWASP API point-by-point, SCA, Cloud/Container |
| **Gap** | No DREAD scoring, no SCA exploitability, no container/cloud | No multi-domain consolidation, no challenger, no baseline |

They are **complementary, not redundant**.

## Integration patterns

### Pattern 1 — Deep dive after full review (recommended)

Run CodeCounsil first for the full picture, then use appsec-plugins for deeper security analysis:

```bash
# Step 1: Full multi-domain review
project-review full --repo .

# Step 2: Deep AppSec threat modeling
# (In Claude Code / Copilot CLI)
@appsec-tm        # STRIDE+DREAD threat model
@appsec-owasp     # OWASP Top 10 detailed pass

# Step 3: Merge findings back and re-consolidate
# Copy appsec-plugins output to .review/raw/security-deep.json
project-review --consolidate-only
```

### Pattern 2 — Pre-release with differential security

```bash
# Fast security gate on PR changes
project-review --profile pre-release --diff main --fail-on high

# If gate passes, run deep diff security review
@appsec-diff      # Blast radius + regression analysis
```

### Pattern 3 — Specialist replacement for high-criticality projects

Use the combined skill (`appsec-codecounsil`) to run both in one invocation. See `SKILL.md`.

## Finding format bridge

When using appsec-plugins output as input to CodeCounsil consolidation, convert findings to the CodeCounsil schema format:

```json
{
  "id": "CC-SEC-001",
  "title": "[from appsec-plugins finding title]",
  "domains": ["security"],
  "category": "injection",
  "classification": "confirmed_finding",
  "severity": "high",
  "priority": "P2",
  "confidence": "high",
  "status": "pending",
  "observation": "[appsec-plugins observation]",
  "impact": "[appsec-plugins impact]",
  "evidence": [{"file": "src/api.py", "start_line": 42, "end_line": 48, "description": "..."}],
  "assumptions": [],
  "missing_evidence": [],
  "recommendation": "[appsec-plugins remediation]",
  "effort": "medium",
  "external_source": "appsec-plugins/appsec-tm"
}
```

Save this to `.review/raw/security-plugins.json` and run `project-review --consolidate-only`.

## Capability matrix

| Capability | Use | Tool |
|-----------|-----|------|
| STRIDE + DREAD threat model | Always on high-criticality | `@appsec-tm` |
| OWASP API Security (API1-API10) | When APIs detected | `@appsec-owasp` or `owasp-api` skill |
| Dependency SCA with exploitability | Always | `dependency-sca` skill |
| Cloud / IaC security | When Terraform/CF detected | `cloud-security` skill |
| Container security | When Dockerfile/K8s detected | `container-security` skill |
| MITRE ATT&CK enrichment | For pentest-grade reports | `mitre-attack` skill |
| OWASP LLM (2025) | When AI libraries detected | `owasp-llm` skill (or CC `ai-security-reviewer`) |
| Multi-domain consolidation | Always | CodeCounsil |
| Challenger / debate | For critical/low-confidence | CodeCounsil `selective_debate` |
| Baseline & incrementals | CI/CD | CodeCounsil `--new-findings-only` |
| SARIF output | GitHub/GitLab CI | CodeCounsil `--output-format sarif` |
