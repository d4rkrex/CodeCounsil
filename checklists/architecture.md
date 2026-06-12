# Architecture Checklist

- Are responsibilities clearly separated across modules or layers?
- Are components highly cohesive and minimally coupled?
- Are boundaries between transport, domain, and persistence explicit?
- Are APIs consistent in shape, naming, versioning, and error semantics?
- Are scalability assumptions documented and technically plausible?
- Are shared utilities avoiding god-object or service-locator drift?
- Are synchronous dependencies acceptable for the expected load profile?
- Is state management localized and predictable?
- Are extension points clear without introducing excessive abstraction?
- Are architectural constraints visible in code rather than implicit tribal knowledge?
