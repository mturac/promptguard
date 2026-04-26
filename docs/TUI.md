# TUI Concept

PromptGuard can grow into a focused terminal UI for reviewing prompt contracts.

## Goals

- show findings without dumping long logs
- make missing decisions obvious
- provide rewrite drafts
- let users accept risks intentionally
- support repo-level audits and pasted prompt audits

## Layout

```text
┌─ PromptGuard ───────────────────────────────────────────────────────────────┐
│ Source: prompts.py                       Findings: 4    Blocking: 2         │
├───────────────────────────────┬─────────────────────────────────────────────┤
│ Findings                      │ Detail                                      │
│                               │                                             │
│ HIGH PG012 responsibility     │ Evidence                                    │
│ HIGH PG015 technical risk     │   "Fix this bug and write code..."          │
│ MED  PG005 output contract    │                                             │
│ LOW  PG006 maintainability    │ Missing Contract                            │
│                               │   Role, owned surface, verification,        │
│                               │   changed-files report, residual risk.      │
│                               │                                             │
│                               │ Questions To Ask                            │
│                               │   1. Which module/files are owned?          │
│                               │   2. What behavior must be preserved?       │
│                               │   3. How should success be verified?        │
├───────────────────────────────┴─────────────────────────────────────────────┤
│ [F] Fix draft  [A] Accept risk  [S] Save report  [Q] Quit                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Interaction Model

- `j/k`: move between findings
- `enter`: expand finding detail
- `f`: copy or write fix draft
- `a`: accept risk with reason
- `s`: save report to `.promptguard/reports.jsonl`
- `/`: filter by rule id or severity

## Visual Direction

- dark terminal background
- dense two-pane review layout
- severity badges using red/yellow/blue
- no decorative dashboard cards
- optimized for repeated engineering use
