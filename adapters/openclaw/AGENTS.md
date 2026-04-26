# PromptGuard

Automatically apply PromptGuard when the user shares, writes, edits, reviews, or debugs any LLM prompt, system prompt, agent instruction, router prompt, evaluator prompt, or tool/function-call prompt.

Do not wait for the user to type a command.

For prompt work:
- Treat the prompt as an executable contract.
- Compare what the prompt literally says with what the user likely expects the model to do.
- Check role, task, input, context, output, boundaries, safety escalation, memory/state, tool schema, and evaluation criteria.
- Flag vague intent, conflicting rules, later overrides, context retention illusions, false certainty, missing responsibility, and missing technical risk controls.
- Include approval criteria: state exactly what must be true before the prompt should be accepted.
- If the user asks to add, save, insert, seed, update, or write a prompt, audit the pasted/proposed prompt before choosing an insertion point or editing files.
- If high or critical findings appear, do not write yet. Show findings and ask for explicit approval or provide a fixed draft.
- Do not stop after locating files. Discovery is not completion.

Preferred commands:

```bash
python3 skills/promptguard/scripts/audit_prompt.py <file> --format markdown
python3 ~/.config/openclaw/skills/promptguard/scripts/audit_prompt.py <file> --format markdown
python3 skills/promptguard/scripts/audit_repo.py . --format markdown
```
