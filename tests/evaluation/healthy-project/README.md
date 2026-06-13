# healthy-project

A well-written FastAPI application for CodeCounsil false-positive evaluation.

## Expected Findings

**0 confirmed_findings** — this code is intentionally written correctly.

Acceptable outputs:
- At most 1-2 `improvement` or `design_weakness` findings
- No `confirmed_finding` with severity > low
- No `probable_risk` with severity > medium

## What is correct here

- No hardcoded secrets (uses environment variables)
- Ownership check before returning user data (no IDOR)
- Idempotent payment endpoint with idempotency key
- Logging without PII
- Constant-time token comparison
- Auth dependency on every protected endpoint
- Tests exist for critical flows
