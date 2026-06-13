# Specialist Registry

## Adding a New Specialist

1. Create `agents/{name}/agent.md` with mission, scope, checklist expectations, and output contract.
2. Add the selector key to `core/selection/selector.py` (`DOMAIN_SPECIALISTS` or `V11_SPECIALISTS`).
3. Add a condition in `SPECIALIST_CONDITIONS` when the specialist is conditional.
4. Register the specialist in `core/orchestration/orchestrator.py` (`SPECIALIST_AGENT_MAP` and `CHECKLIST_MAP`).
5. Create the Claude Code adapter in `adapters/claude-code/agents/{name}.md`.
6. Add or update tests in `tests/unit/test_selection.py`.

## Current Registry

| Specialist | Domain | Condition | MVP |
|------------|--------|-----------|-----|
| project-discovery | - | always | ✅ |
| software-architect | architecture | always | ✅ |
| senior-developer | developer | always | ✅ |
| qa-reviewer | qa | tests present | ✅ |
| appsec-reviewer | security | requested mode | ✅ |
| findings-challenger | - | always | ✅ |
| report-consolidator | - | always | ✅ |
| ux-reviewer | ux | `project_context["frontend"]["present"]` | — |
| sre-reviewer | sre | IaC or pipelines detected | — |
| finops-reviewer | finops | Terraform or CloudFormation detected | — |
| product-reviewer | product | documentation present | — |
| data-privacy-reviewer | data_privacy | always when requested | — |
| ai-reviewer | ai | AI/ML libraries detected | — |
| api-design-reviewer | api_design | `project_context["apis"]` non-empty | — |
| ai-security-reviewer | ai_security | AI/ML libraries detected | — |
| ai-quality-reviewer | ai_quality | AI/ML libraries detected | — |
