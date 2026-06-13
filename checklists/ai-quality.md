# AI Quality Checklist

- Are evaluation harnesses defined with representative tasks, regression suites, and success thresholds?
- Are benchmark datasets versioned, documented, and matched to real user scenarios?
- Is ground truth explicit and are quality metrics defined (accuracy, factuality, refusal quality, task completion)?
- Are hallucination risks mitigated with fallback paths, abstention behavior, or escalation to humans?
- Are latency and cost measured, budgeted, and reviewed per model, route, or feature?
- Is model routing documented with clear criteria for version selection and rollback?
- Are outputs reproducible enough through prompt/model/version tracking and stable evaluation inputs?
- Are prompt, answer, and error categories observable through logs, feedback loops, or dashboards?
- Are human-correction rates, rejection rates, and failure categories measured?
- Are bias limitations, known blind spots, and intended-use boundaries documented?
