# vulnerable-project

A deliberately vulnerable FastAPI application for CodeCounsil evaluation.

## Known Defects (Ground Truth)

| ID | Description | File | Severity |
|----|-------------|------|----------|
| KD-001 | IDOR — /users/{id} missing ownership check | app.py:17-24 | high |
| KD-002 | Secret (DB password) hardcoded in source | app.py:8 | critical |
| KD-003 | Sensitive data (email) logged on every request | app.py:35 | medium |
| KD-004 | Non-idempotent retry — payment charged twice on retry | payments.py:28-45 | high |
| KD-005 | Database migration with no rollback | migrations/001_add_users.py:1-20 | medium |
| KD-006 | Critical flow (checkout) has zero test coverage | tests/ (missing) | medium |

## Purpose

- `precision` test: CodeCounsil should flag these 6 defects and not invent others
- `recall` test: CodeCounsil should detect ≥ 4 of the 6 known defects
