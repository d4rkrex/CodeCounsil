# SRE Checklist

- Are logs structured, actionable, and present for startup, shutdown, request handling, and failures?
- Are core metrics defined for latency, errors, throughput, saturation, retries, and queue depth?
- Are traces or correlation IDs propagated across service boundaries and async jobs?
- Are liveness, readiness, and startup health checks explicit and meaningful?
- Does the service handle graceful shutdown, connection draining, and signal handling safely?
- Are retry/backoff policies bounded and paired with idempotency or circuit-breaker protections?
- Are deployment strategies, rollback steps, and migration sequencing documented and safe?
- Are resource requests/limits, autoscaling signals, and capacity assumptions defined?
- Are SLO/SLA targets, alert thresholds, or error-budget expectations visible?
- Are incident runbooks or operational response notes available for common failure modes?
