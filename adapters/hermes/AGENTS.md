# PromptGuard

Automatically apply PromptGuard when the user shares, writes, edits, reviews, or debugs any LLM prompt, system prompt, agent instruction, router prompt, evaluator prompt, or tool/function-call prompt.

Do not wait for the user to type `/promptguard`.

For prompt work:
- Treat the prompt as an executable contract.
- Compare what the prompt literally says with what the user likely expects the model to do.
- Check role, task, input, context, output, boundaries, safety escalation, memory/state, tool schema, and evaluation criteria.
- Flag vague intent, conflicting rules, later overrides, context retention illusions, and false certainty.
- Flag prompts that ask for code/output without assigning responsibility, owned surface, constraints, verification, and accountability report.
- Report as `Severity | Evidence | Impact | Missing/Conflicting Contract | Clarification Contract | Questions to Ask | Fix Draft`.
- Include an approval contract: state exactly what must be true before the prompt should be accepted.
- Clarification questions must be generic to the missing decision point, not hardcoded to reports.
- If the user asks to add, save, insert, seed, update, or write a prompt, you MUST audit the proposed prompt before editing files.
- Prefer the Hermes skill install:
  `printf '%s' '<prompt text>' | python3 ~/.hermes/skills/promptguard/scripts/audit_prompt.py - --profile coding-agent --fail-on high --format markdown`
- Or the package CLI when available:
  `promptguard audit - --profile coding-agent --fail-on high --format markdown`
- If the pre-write audit returns high or critical findings, do not write the prompt yet. Show the findings and ask for explicit approval or provide a fixed draft.
- Only write after the prompt passes audit or the user explicitly accepts the listed risks.
- If a prompt-like file is present, you MUST run the PromptGuard audit script before giving the final answer.
- Do not stop after locating files. Discovery is not completion.
- Repo-level audit:
  `python3 ~/.hermes/skills/promptguard/scripts/audit_repo.py . --profile coding-agent --fail-on high --format markdown`
- If no script is available, explicitly say the script is unavailable and perform a manual audit in the same report format.

The Hermes plugin (`pre_tool_call`) can block prompt-like `write_file` / `patch` / `edit` tool calls when findings meet `PROMPTGUARD_FAIL_ON` (default `high`). Profile defaults to `coding-agent` via `PROMPTGUARD_PROFILE`.
