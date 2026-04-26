# PromptGuard Agent Rule

When the user shares, edits, reviews, or asks why an LLM/system prompt fails:

1. Treat the prompt as a contract.
2. Check: role, task, input data, output format, boundaries, safety escalation, tool schema, memory/state, evaluation criteria.
3. Report findings as: `Severity | Evidence | Impact | Missing/Conflicting Contract | Fix Draft`.
4. Do not only rewrite the prompt; explain what behavior can break and why.
5. If a repository has PromptGuard installed, run `promptguard audit <prompt-file>`.
