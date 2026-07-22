<p align="center">
  <img src="docs/assets/promptguard.png" alt="PromptGuard" width="640">
</p>

<p align="center">
  <strong>Prompt contracts for agent workflows.</strong><br>
  <em>Offline · deterministic · zero dependencies</em>
</p>

---

Agents do what you ask — even when what you ask is incomplete.

```text
Fix this bug and write code.
```

PromptGuard treats that line as a **contract**, not a wish. It checks whether role, surface, constraints, verification, and safety are explicit enough to execute — and stops vague instructions before they become a bad write.

```bash
printf '%s' 'Fix this bug and write code.' \
  | promptguard audit - --profile coding-agent --fail-on high
```

---

## Install

```bash
pipx install "git+https://github.com/mturac/promptguard.git"
# or: pip install -e .
```

```bash
promptguard audit path/to/prompt.md --profile coding-agent --fail-on high
```

---

## What you get

| | |
|---|---|
| **Findings** | Evidence, impact, missing contract, questions, approval criteria |
| **Fix draft** | Rewrite that keeps your wording and fills the gaps |
| **Profiles** | `coding-agent` · `system` · `security` · `general` |
| **CI** | Severity gates, repo walk, SARIF, baseline diffs |
| **Agents** | Pre-write guard for Hermes, Claude, Codex, OpenCode, OpenClaw |

No model calls. No network. Safe in hooks and air-gapped machines.

---

## Profiles

Use the pack that matches the work:

```bash
promptguard audit task.md   --profile coding-agent --fail-on high
promptguard audit system.md --profile system       --fail-on high
promptguard audit agent.md  --profile security     --fail-on high
```

| Profile | When |
|---------|------|
| `coding-agent` | Implementation prompts — ownership, scope, verification |
| `system` | System / router / policy text — safety and precedence |
| `security` | Instruction hardening — override and exfil patterns |
| `general` | Full core catalog (default) |

`--fail-on high` fails only on high or critical. Omit it to fail on any finding (legacy). Use `--fail-on none` to report without failing.

---

## CI

```bash
promptguard audit-repo . --profile coding-agent --fail-on high --format sarif
promptguard audit task.md --baseline .promptguard/reports.jsonl --fail-on-new
```

Walk a tree of prompt-like files, export SARIF, or gate on **new** findings only. Reports can be saved to `.promptguard/reports.jsonl`.

Intentional exceptions:

```bash
promptguard audit task.md --accept-risk PG012:deadline --apply-accepted
```

---

## Agents

Same contract gate across popular coding agents:

```bash
./install-agent-adapters.sh hermes    # active Hermes profile + pre_tool_call plugin
./install-agent-adapters.sh claude
./install-agent-adapters.sh codex
./install-agent-adapters.sh opencode
./install-agent-adapters.sh openclaw
./install-agent-adapters.sh all
```

Restart after install. Hard-block plugins honor:

```bash
export PROMPTGUARD_PROFILE=coding-agent
export PROMPTGUARD_FAIL_ON=high
```

| | |
|---|---|
| **Hermes** | Skill + `pre_tool_call` plugin · `/promptguard` |
| **OpenClaw** | Skill + `before_tool_call` plugin |
| **Claude** | Skill + `CLAUDE.md` · optional hook |
| **Codex / OpenCode** | Skill + `AGENTS.md` |

---

## Review

```bash
promptguard tui task.md --profile coding-agent
```

Navigate findings, open a fix draft, record accept-risk, save. In non-interactive environments it prints a table and exits non-zero on high+ findings.

---

## Example

**Vague**

```text
Prod auth patlıyor, refresh’te kullanıcı düşüyor. Hızlıca fixler misin, akşama deploy.
```

→ typically `PG012` (responsibility) and `PG015` (technical risk).

**Contracted**

```text
Act as the backend engineer for src/auth/session.py and tests/auth.
Fix the refresh-token logout bug only; preserve public API behavior.
Verify with `pytest tests/auth -q`.
Return changed files, root cause, verification output, and residual risk.
```

---

## Rules (selection)

| ID | Concern |
|----|---------|
| `PG012` | Coding without ownership / surface / verification |
| `PG015` | Technical change without risk / rollback / tests |
| `PG008` | Later exception weakens an earlier hard boundary |
| `PG004` | Tool / function call without a real schema |
| `PG016–018` | Security pack: override, system-prompt leak, exfil |

Full list and eval fixtures: [`eval/`](eval/) · details: [USAGE.md](USAGE.md)

---

## Develop

```bash
python3 -m pytest -q
```

Further reading: [USAGE.md](USAGE.md) · [EXAMPLES.md](EXAMPLES.md) · [CHANGELOG.md](CHANGELOG.md)

---

<p align="center">
  <sub>Part of <a href="https://github.com/mturac/tools">mturac/tools</a></sub>
</p>
