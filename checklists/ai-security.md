# AI Security Checklist

- Can direct user input change system prompts, hidden instructions, or model tool-selection logic?
- Can indirect content from RAG, files, tickets, docs, or web pages inject instructions into the model context?
- Are tool invocations authorized per user/action and constrained to least privilege?
- Are model outputs sanitized before triggering code execution, workflow automation, or user-visible rendering?
- Are models, embeddings, vector stores, and retrieved corpora trusted, versioned, and protected from poisoning?
- Can prompts or completions leak secrets, tokens, PII, or sensitive business data to logs or downstream systems?
- Are jailbreak attempts, prompt overrides, or policy bypasses detected or mitigated?
- Does the AI system have excessive agency, background actions, or privilege escalation paths through connectors or tools?
- Are prompts, traces, and tool-call logs scrubbed to avoid storing sensitive input or output data?
- Are execution controls, human approvals, or allowlists present for sensitive tool actions?
