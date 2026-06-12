# Contributing

Thanks for contributing to CodeCounsil.

## Development Setup

1. Use Python 3.11 or 3.12.
2. Create and activate a virtual environment.
3. Install dependencies with `pip install -e ".[dev]"`.
4. Copy `codecounsil.example.yaml` to `codecounsil.yaml` only if you need local overrides.

## Running Tests

- Full test suite: `pytest --tb=short -q`
- Coverage check: `pytest --cov=core --cov-report=term-missing --cov-fail-under=70`
- Focused selector tests: `pytest tests/unit/test_selection.py -q`

## Adding a New Specialist

1. Add `agents/{name}/agent.md` with mission, scope, exclusions, security rules, and output contract.
2. Add the specialist selector key and selection condition in `core/selection/selector.py`.
3. Register the agent and checklist in `core/orchestration/orchestrator.py`.
4. Create the Claude Code adapter in `adapters/claude-code/agents/{name}.md` and a checklist in `checklists/` when needed.
5. Add selection coverage in `tests/unit/test_selection.py` and any discovery/config tests required by the new condition.

## Code Style

- Keep changes small and evidence-oriented.
- Preserve VT-Spec security controls and comments.
- Prefer explicit conditions and deterministic behavior over implicit heuristics.
- Run `ruff check core/ tests/ --ignore E501` before opening a PR when possible.

## Pull Request Process

1. Create a focused branch.
2. Add or update tests with the change.
3. Run the test suite locally.
4. Summarize the specialist, schema, or workflow impact in the PR description.
5. Request review only after CI is green.

## Security Reporting

Do not open public issues for sensitive vulnerabilities. Report security concerns privately to the maintainers and include reproduction steps, affected paths, impact, and suggested remediation.
