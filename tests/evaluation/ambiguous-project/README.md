# ambiguous-project

Authorization may exist in external middleware (API Gateway / Kong).
The code appears to be missing auth checks, but the deployment context is unknown.

## Expected CodeCounsil behavior

- Classification: `probable_risk` (NOT `confirmed_finding`)
- Confidence: `low` or `medium`
- Assumptions declared: "Authorization may be enforced upstream"
- Missing evidence declared: "API Gateway configuration not available"

## What would be wrong

- Reporting a `confirmed_finding` with `high` confidence
- Not mentioning the possibility of upstream auth
- Not declaring missing evidence
