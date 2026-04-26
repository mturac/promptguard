---
name: promptguard
description: Use when auditing system prompts, agent prompts, router prompts, tool/function-call prompts, or prompts that cause inconsistent, unsafe, malformed, or surprising LLM behavior.
metadata:
  short-description: Audit prompts as executable contracts
---

# PromptGuard

Audit prompts as executable contracts, not writing style.
The core job is to compare what the prompt literally says with what the user expects the model to do.

## When Triggered

Use this skill when the user shares, writes, reviews, debugs, or asks to improve:
- system prompts
- agent/router prompts
- evaluator prompts
- tool or function-call instructions
- prompt files in a repo

## Workflow

1. Identify the surface: TUI, web chat, API, router, tool call, evaluator, or agent persona.
2. Extract contracts: role, task, input, context, output, boundaries, safety escalation, memory/state, tool schema, evaluation.
3. Flag failures: missing contract, conflicting instruction, ambiguous boundary, passive safety escalation, role drift, provider schema mismatch.
   Also flag vague intent, later-rule override, context retention illusion, and false certainty.
   For coding/build prompts, flag missing responsibility, owned surface, constraints, verification, and accountability report.
4. Return findings as:
   `Severity | Evidence | Impact | Missing/Conflicting Contract | Clarification Contract | Questions to Ask | Approval Contract | Fix Draft`

Clarification questions must be generated from the missing decision point. Do not hardcode them to one example like reports.

## Pre-Write Guard

If the user asks to add, save, insert, seed, update, or write a prompt, audit the proposed prompt before editing files.

For pasted prompt text:

```bash
printf '%s' '<prompt text>' | python3 skills/promptguard/scripts/audit_prompt.py - --format markdown
```

If high or critical findings appear, do not write yet. Show findings and ask for explicit approval or offer a fixed draft.

## Deterministic Audit

If the prompt is in a local file, run this before finalizing:

```bash
python3 skills/promptguard/scripts/audit_prompt.py path/to/prompt-file --format markdown
```

If this skill is installed into `$CODEX_HOME/skills/promptguard`, run the script from that installed path instead.

Do not stop after discovering prompt files. Discovery is not completion. If a prompt-like file exists and the script exists, running the script is mandatory.

If the user asks for a report without naming a file, run:

```bash
python3 skills/promptguard/scripts/audit_repo.py . --format markdown
```

## Severity

- `critical`: unsafe, illegal, or harmful behavior risk.
- `high`: privacy, routing, parsing, or tool-call breakage.
- `medium`: inconsistent UX or agent boundary drift.
- `low`: maintainability or clarity issue.

Prefer concrete contract fixes over generic prompt advice.
