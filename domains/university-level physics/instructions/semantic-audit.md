# University-level physics semantic-audit extension

Audit each activity for physics consistency across the prompt, answer key, distractors, explanation, visual plan/specification, units/symbols, direction/sign, before/after state, graph relation, and declared simulation invariants. Check whether any conservation law or simplifying assumption is actually justified. Treat generated contextual imagery as non-authoritative.

When a high-value relation benefits from independent symbolic/numerical verification, require evidence according to `verification/verification-policy.json`. Flag contradictions or unsupported assumptions rather than repairing them silently during audit.
