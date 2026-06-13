# SRE Checklist

- Are logs structured, actionable, and present for startup, shutdown, request handling, and failures?
- Are core metrics defined for latency, errors, throughput, saturation, retries, and queue depth?
- Are traces, distributed tracing spans, and correlation IDs propagated across service boundaries and async jobs?
- Are liveness, readiness, and startup health checks explicit, distinct, and meaningful for orchestrators?
- Does the service handle graceful shutdown, connection draining, and signal handling safely?
- Are retry/backoff policies bounded and paired with idempotency, circuit-breaker, or backpressure protections?
- Are feature flags, deployment strategies, rollback steps, and migration sequencing documented and safe?
- Are database migrations reversible or paired with an operational rollback/fix-forward plan?
- Are resource requests/limits, autoscaling signals, and capacity assumptions defined?
- Are disaster-recovery expectations, backup coverage, and RTO/RPO targets defined?
- Are SLO/SLA targets, alert thresholds, or error-budget expectations visible?
- Are incident runbooks complete enough to cover detection, triage, rollback, escalation, and recovery for common failure modes?
