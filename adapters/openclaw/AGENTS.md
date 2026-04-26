# PromptGuard Mandatory Pre-Write Gate

This rule is mandatory and takes priority over general helpfulness.

Automatically apply PromptGuard when the user shares, writes, edits, reviews, or debugs any LLM prompt, system prompt, agent instruction, router prompt, evaluator prompt, or tool/function-call prompt.

Do not wait for the user to type a command.

If the user asks to add, save, insert, seed, update, or write a prompt:

1. Stop before reading or editing destination files.
2. Audit the pasted/proposed prompt first.
3. Use:

```bash
printf '%s' '<prompt text>' | python3 ~/.openclaw/workspace/skills/promptguard/scripts/audit_prompt.py - --format markdown
```

4. If the audit returns high or critical findings, do not write the prompt.
5. Report the findings and ask for explicit approval or offer a fixed draft.
6. Only write after the prompt passes audit or the user explicitly accepts the listed risks.

For prompt work:
- Treat the prompt as an executable contract.
- Compare what the prompt literally says with what the user likely expects the model to do.
- Check role, task, input, context, output, boundaries, safety escalation, memory/state, tool schema, and evaluation criteria.
- Flag vague intent, conflicting rules, later overrides, context retention illusions, false certainty, missing responsibility, and missing technical risk controls.
- Include approval criteria: state exactly what must be true before the prompt should be accepted.
- If high or critical findings appear, do not write yet. Show findings and ask for explicit approval or provide a fixed draft.
- Do not stop after locating files. Discovery is not completion.

Preferred commands:

```bash
python3 skills/promptguard/scripts/audit_prompt.py <file> --format markdown
python3 ~/.openclaw/workspace/skills/promptguard/scripts/audit_prompt.py <file> --format markdown
python3 ~/.openclaw/skills/promptguard/scripts/audit_prompt.py <file> --format markdown
python3 skills/promptguard/scripts/audit_repo.py . --format markdown
```
