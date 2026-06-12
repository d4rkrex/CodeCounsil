# QA Checklist

- Are unit, integration, and end-to-end tests present where appropriate?
- Do tests cover negative paths, boundaries, and regression-prone flows?
- Are test fixtures realistic and deterministic?
- Are flaky patterns or hidden dependencies visible in the suite?
- Is CI configured to run the right test depth for the project?
- Are important contracts validated with assertions instead of smoke checks only?
- Are missing tests traceable to concrete product or security risks?
- Is setup and teardown isolated enough to avoid cross-test pollution?
- Are manual verification steps documented when automation is missing?
