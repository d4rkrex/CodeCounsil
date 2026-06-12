# Security Checklist

- OWASP Top 10 (2021): broken access control, crypto misuse, injection, insecure design, misconfiguration, vulnerable components, auth failures, integrity failures, logging gaps, SSRF
- OWASP API Security: BOLA, BFLA, mass assignment, excessive data exposure, rate limiting, inventory gaps
- Input validation and output encoding controls
- Authentication and session management design
- Authorization on every object and action boundary
- Secret handling in code, config, CI, and documentation
- Dependency and supply-chain risk evidence
- Unsafe template, YAML, deserialization, or subprocess usage
- Cloud/IaC exposures if relevant artifacts are present
- Clearly separate confirmed evidence from probable risk
