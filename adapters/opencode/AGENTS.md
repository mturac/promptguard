# PromptGuard

Automatically apply PromptGuard when the user shares, writes, edits, reviews, or debugs any LLM prompt, system prompt, agent instruction, router prompt, evaluator prompt, or tool/function-call prompt.

Do not wait for the user to type a command.

For prompt work:
- Treat the prompt as an executable contract.
- Compare what the prompt literally says with what the user likely expects the model to do.
- Check role, task, input, context, output, boundaries, safety escalation, memory/state, tool schema, and evaluation criteria.
- Flag vague intent, conflicting rules, later overrides, context retention illusions, and false certainty.
- Flag prompts that ask for code/output without assigning responsibility, owned surface, constraints, verification, and accountability report.
- Report as `Severity | Evidence | Impact | Missing/Conflicting Contract | Clarification Contract | Questions to Ask | Fix Draft`.
- Include an approval contract: state exactly what must be true before the prompt should be accepted.
- Clarification questions must be generic to the missing decision point, not hardcoded to reports.
- If the user asks to add, save, insert, seed, update, or write a prompt, you MUST audit the pasted/proposed prompt before choosing an insertion point or editing files.
- For pasted prompt text, run it through stdin before writing:
  `printf '%s' '<prompt text>' | python3 ~/.config/opencode/skills/promptguard/scripts/audit_prompt.py - --format markdown`
- If the pre-write audit returns high or critical findings, do not write the prompt yet. Show the findings and ask for explicit approval or provide a fixed draft.
- Only write after the prompt passes audit or the user explicitly accepts the listed risks.
- If a prompt-like file is present, you MUST run the PromptGuard audit script before giving the final answer.
- Do not stop after locating files. Discovery is not completion.
- Preferred command from repo root: `python3 skills/promptguard/scripts/audit_prompt.py <file> --format markdown`.
- If that path does not exist, try `python3 ~/.config/opencode/skills/promptguard/scripts/audit_prompt.py <file> --format markdown`, then `python3 ~/.claude/skills/promptguard/scripts/audit_prompt.py <file> --format markdown`.
- If the user asks for "the report" or does not name a specific file, you MUST run repo-level audit immediately:
  `python3 skills/promptguard/scripts/audit_repo.py . --format markdown`
- If no script is available, explicitly say the script is unavailable and perform a manual audit in the same report format.
