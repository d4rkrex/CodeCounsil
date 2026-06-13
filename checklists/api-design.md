# API Design Checklist

- Do HTTP methods match their intended semantics (safe, idempotent, cacheable, partial update, delete semantics)?
- Are resource names, URL hierarchies, and path parameters consistent, predictable, and consumer-friendly?
- Is the versioning strategy explicit (path/header/media type), documented, and compatible with deprecation/sunset flows?
- Are pagination, filtering, sorting, and maximum page-size limits defined and consistent across list endpoints?
- Are retried writes safe through idempotent semantics or explicit idempotency keys?
- Are status codes and error payloads consistent, actionable, and aligned with RFC 7807 Problem Details where relevant?
- Are rate limits and quota headers documented (`X-RateLimit-*`, `Retry-After`) and enforced proportionally?
- Is the OpenAPI/AsyncAPI specification complete, current, and aligned with implementation?
- Do contract changes introduce breaking behavior for existing consumers, SDKs, or webhooks?
- Are webhook endpoints authenticated, replay-safe, versioned, and documented for delivery retries and failure handling?
- Are compatibility, schema evolution, and deprecation notices sufficient for downstream consumers?
- Are contract tests or schema-validation checks present for critical API workflows?
