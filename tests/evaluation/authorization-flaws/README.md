# authorization-flaws

Specific authorization vulnerabilities for AppSec Reviewer evaluation.

## Known Defects

| ID | Description | OWASP | Severity |
|----|-------------|-------|----------|
| KD-AUTH-001 | BOLA — data retrieved before ownership check | API1:2023 | high |
| KD-AUTH-002 | BFLA — role from request param, not verified JWT | API5:2023 | critical |
| KD-AUTH-003 | Bulk export without scope restriction | API3:2023 | high |
