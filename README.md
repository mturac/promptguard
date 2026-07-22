<p align="center">
  <img src="docs/assets/promptguard.png" alt="PromptGuard" width="720">
</p>

# PromptGuard

**Offline, deterministic prompt contract auditor for agent workflows.**

PromptGuard treats prompts as behavioral contracts — not writing style tips. It is built for the moment an agent is about to edit files, seed a system prompt, or ship code from a vague instruction:

```text
Fix this bug and write code.
Build this endpoint.
Give me the report.
Add this system prompt.
```

Most advice says “write better prompts.” PromptGuard turns that into an **executable check**:

- Is the task actually specified?
- Is the agent responsible for a clear surface?
- Are output format, constraints, risks, and verification explicit?
- Are safety boundaries contradicted later in the prompt?
- Should the agent ask for missing data instead of hallucinating a deliverable?

It does not only say “bad prompt.” It reports:

- what decision is missing  
- what question to ask  
- what contract is required  
- what must be true before approval  
- a **grounded** rewrite draft (keeps your wording + injects the missing contract)

**No network. No model API. Zero runtime dependencies.** Safe for hooks, CI, and air-gapped agents.

![PromptGuard TUI concept](docs/assets/tui-mockup.svg)

---

## Features

### Profiles & severity gates

Ship different rule packs for different jobs without editing Python.

| Profile | Best for | Highlights |
| --- | --- | --- |
| `general` | Default full catalog | Core PG001–PG015 |
| `coding-agent` | Coding agents | Responsibility, task scope, technical risk (PG011/012/015…) |
| `system` | System / router / policy prompts | Safety, conflict, tool schema, override |
| `security` | Instruction hardening | Static injection / exfil heuristics (PG016–PG018) |

```bash
promptguard audit task.md --profile coding-agent --fail-on high
promptguard audit system.md --profile system --fail-on high
promptguard audit agent.md --profile security --fail-on high
```

- **`--fail-on`**: exit `1` only when severity ≥ threshold (`critical` > `high` > `medium` > `low` > `info`)
- **`--fail-on none`**: always exit `0` (still prints the report)
- **Omitted `--fail-on`**: legacy behavior — any finding → exit `1`
- **`--rules PATH`**: load a custom JSON rules array (profile still filters enabled ids)

### Multi-surface extractors

Not only plain files:

- Python `PROMPTS = {...}` dicts  
- `SKILL.md` / `AGENTS.md` / `CLAUDE.md` (whole file + headed / fenced sections)  
- YAML / JSON string values under `system`, `prompt`, `instructions`, …  
- Markdown fenced blocks labeled system / prompt / instructions  

### Repo audit + CI formats

```bash
promptguard audit-repo . --profile coding-agent --fail-on high
promptguard audit-repo . --format sarif --include '*.md' --exclude 'docs/**'
```

- Walks prompt-like paths (skips `.git`, venv, `node_modules`, …)  
- Formats: `markdown` · `json` · `table` · `csv` · **`sarif`** (2.1.0)  

### Baseline regression

Compare today’s findings to a previous report (new / fixed / unchanged):

```bash
promptguard audit task.md --profile coding-agent --save
promptguard audit task.md --profile coding-agent \
  --baseline .promptguard/reports.jsonl --fail-on-new
```

`--fail-on-new` fails CI only when **new** findings appear.

### Accept-risk trail

Record intentional overrides; re-apply them later:

```bash
promptguard audit task.md --accept-risk PG012:ship-window --fail-on none
promptguard audit task.md --apply-accepted --fail-on high
```

Stored under `.promptguard/accepted-risks.jsonl` (rule id + source path + reason).

### Grounded fix drafts

Findings include a rewrite draft that **preserves the operator’s wording** and injects the missing contract checklist — not only a generic one-liner.

### Richer rule matching

Rules still use classic `any` / `also_any` / `missing_*` substring fields (backward compatible). Optionally:

| Field | Semantics |
| --- | --- |
| `word_any`, `word_also_any`, `word_missing_any` | Unicode word-boundary match |
| `regex_any`, `regex_also_any`, `regex_missing_any` | `re.search` (invalid patterns fail closed) |

### Promptfoo export

Bridge static eval JSONL into a promptfoo YAML skeleton (you wire providers/asserts):

```bash
promptguard export-promptfoo eval/cases.jsonl -o promptfooconfig.yaml
```

### Interactive TUI

```bash
promptguard tui task.md --profile coding-agent
```

- TTY: `j`/`k` navigate · `f` fix draft · `a` accept risk · `s` save · `q` quit  
- Non-TTY / CI: table dump; exit `1` on high+ findings  

### Agent-native pre-write guard

Same contract gate across popular coding agents:

| Agent | Install | Automatic behavior |
| --- | --- | --- |
| **Hermes** | `$HERMES_HOME/skills/promptguard` + `plugins/promptguard` | `pre_tool_call` blocks prompt-like writes; `/promptguard` skill |
| OpenClaw | workspace skill + plugin | `before_tool_call` blocks unsafe prompt writes |
| Claude | skill + `CLAUDE.md` + optional hook | Findings injected before the turn |
| Codex | skill + `AGENTS.md` | Audits prompt-like write requests before editing |
| OpenCode | skill + `AGENTS.md` | Audits prompt-like write requests before editing |

```bash
./install-agent-adapters.sh hermes
./install-agent-adapters.sh claude
./install-agent-adapters.sh codex
./install-agent-adapters.sh opencode
./install-agent-adapters.sh openclaw
./install-agent-adapters.sh all
```

Shared env for Hermes / OpenClaw hard-block plugins:

```bash
export PROMPTGUARD_PROFILE=coding-agent
export PROMPTGUARD_FAIL_ON=high
```

Restart the agent/gateway after install. Installer copies a self-contained skill bundle so audits work when the package is importable (or via skill scripts).

---

## What It Catches

### Core contracts

- `PG001` privacy conflicts  
- `PG002` unsafe/passive escalation  
- `PG003` agent boundary drift  
- `PG004` weak tool/function schema  
- `PG005` missing output contract  
- `PG006` long prompt without section tags  
- `PG007` vague deliverable intent  
- `PG008` later rule overriding earlier boundary  
- `PG009` long context without state retention  
- `PG010` false certainty without sources  
- `PG011` broad task without acceptance criteria  
- `PG012` coding prompt without responsibility  
- `PG013` recommendation without decision context  
- `PG014` high-stakes advice without safety/source contract  
- `PG015` technical change without risk/verification contract  

### Security pack (`--profile security`)

- `PG016` instruction-override without dual-control  
- `PG017` system-prompt / hidden-instruction disclosure risk  
- `PG018` secret / tool exfiltration style instructions  

---

## Quick Start

Run without installing:

```bash
python3 -m promptguard audit prompts.py
printf '%s' 'Fix this bug and write code.' | python3 -m promptguard audit - --format markdown
```

Install as a local CLI:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
promptguard audit prompts.py --profile coding-agent --fail-on high
```

Install with `pipx`:

```bash
pipx install promptguard
# or from GitHub:
pipx install "git+https://github.com/mturac/promptguard.git"
```

Save reports:

```bash
promptguard audit prompts.py --format json --save
# → .promptguard/reports.jsonl
```

---

## Hermes (first-class)

```bash
./install-agent-adapters.sh hermes
# Resolves active profile home via `hermes config path`
export PROMPTGUARD_PROFILE=coding-agent
export PROMPTGUARD_FAIL_ON=high
# Chat: /promptguard
# Plugin blocks prompt-like write_file / patch / edit
```

Emergency off: `PROMPTGUARD_HERMES_DISABLE=1`.

---

## Examples

**Bad:**

```text
Prod auth patlıyor galiba, refresh atınca bazı kullanıcılar düşüyor. Bi bakıp hızlıca fixler misin, akşama deploy lazım.
```

Expected: `PG012` · `PG015` (with `--profile coding-agent`).

**Better:**

```text
Act as the backend engineer responsible for src/auth/session.py and tests/auth.
Fix the refresh-token logout bug only. Preserve public API behavior and do not refactor unrelated code.
Validate expired token, reused-token, and concurrent-refresh edge cases.
Verify with `pytest tests/auth -q`.
Return changed files, root cause, verification output, deploy/rollback note, and residual risk.
```

---

## Development

```bash
python3 -m pytest -q
```

Package smoke:

```bash
tmpdir=$(mktemp -d /tmp/pg-package.XXXXXX)
python3 -m venv "$tmpdir/venv"
"$tmpdir/venv/bin/python" -m pip install -e .
printf '%s' 'Fix this bug and write code.' | \
  "$tmpdir/venv/bin/promptguard" audit - --profile coding-agent --fail-on high --format table
```

Eval sets:

```text
eval/cases.jsonl
eval/daily_life_cases.jsonl
eval/technical_cases.jsonl
eval/real_world_usage_cases.jsonl
eval/security_cases.jsonl
```

More detail: [USAGE.md](USAGE.md) · [EXAMPLES.md](EXAMPLES.md) · [CHANGELOG.md](CHANGELOG.md) · [docs/TUI.md](docs/TUI.md)

---

## Non-goals

- Network LLM calls / remote model judges (product stays offline)  
- Full curses two-pane TUI polish (minimal `promptguard tui` is shipped)  
- Runtime chat rails or red-team attack generation  

---

## Part of [mturac/tools](https://github.com/mturac/tools)

Open-source toolkit for AI-augmented engineering — Claude Code plugins, MCP servers, security scanners, schedulers, and dev-productivity utilities.

```text
/plugin marketplace add mturac/claude-plugin-marketplace
/plugin install promptguard
```
