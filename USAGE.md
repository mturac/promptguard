# PromptGuard Usage

PromptGuard checks whether a prompt is safe to use before an agent acts on it.

It is built for this failure mode:

```text
Fix this bug and write code.
```

That prompt asks for output but does not assign responsibility. PromptGuard should stop and ask for the missing contract.

## CLI

Install locally:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Install with `pipx`:

```bash
pipx install promptguard
```

Audit a file:

```bash
python3 -m promptguard audit prompts.py
```

Audit pasted text:

```bash
printf '%s' 'Fix this bug and write code.' | python3 -m promptguard audit - --format markdown
```

### Profiles

| Profile | Use when |
| --- | --- |
| `general` | Default — full core catalog (PG001–PG015) |
| `coding-agent` | Agent coding tasks — PG011/PG012/PG015 (+ related) |
| `system` | System/router/policy prompts — safety, tool, override |
| `security` | Static injection / exfil heuristics — PG016–PG018 |

```bash
promptguard audit task.md --profile coding-agent --fail-on high
promptguard audit system.md --profile system
promptguard audit agent.md --profile security --fail-on high
```

### Severity gate (`--fail-on`)

Order: `critical` > `high` > `medium` > `low` > `info`.

| Flag | Exit behavior |
| --- | --- |
| omitted | Legacy: any finding → exit 1 |
| `--fail-on high` | Exit 1 only if severity ≥ high |
| `--fail-on none` | Always exit 0 (report still prints) |

### Repo audit and SARIF

```bash
promptguard audit-repo .
promptguard audit-repo . --profile coding-agent --fail-on high --format sarif
promptguard audit-repo . --include '*.md' --exclude 'docs/**'
```

Formats: `markdown`, `json`, `table`, `csv`, `sarif`.

### Accept risk

```bash
promptguard audit task.md --accept-risk PG012:ship-window --fail-on none
promptguard audit task.md --apply-accepted --fail-on high
```

Records append to `.promptguard/accepted-risks.jsonl` (rule id + source path). Empty reason is rejected.

### Custom rules

```bash
promptguard audit task.md --rules ./my-rules.json --profile coding-agent
```

`--rules` loads a JSON array (or `{ "rules": [...] }`). The active profile still filters by enabled rule ids.

Optional match fields (in addition to classic `any` / `also_any` / `missing_*`):

| Field | Semantics |
| --- | --- |
| `word_any`, `word_also_any`, `word_missing_any` | Unicode word-boundary match |
| `regex_any`, `regex_also_any`, `regex_missing_any` | `re.search` (invalid patterns fail closed) |

### Baseline regression

```bash
promptguard audit task.md --save
promptguard audit task.md --baseline .promptguard/reports.jsonl --fail-on-new
```

Prints new / fixed / unchanged. `--fail-on-new` exits 1 only when **new** findings appear.

### Promptfoo export

```bash
promptguard export-promptfoo eval/cases.jsonl -o promptfooconfig.yaml
```

Skeleton only (stdlib YAML writer) — wire providers and real asserts yourself.

### TUI

```bash
promptguard tui task.md --profile coding-agent
```

Interactive when TTY: `j`/`k` move, `f` fix draft, `a` accept risk, `s` save, `q` quit.  
Non-TTY (CI/pipes): table dump; exit 1 if high+ findings.

### Opt-in LLM judge

```bash
export TURAC_LLM_ROUTER_URL=http://localhost:8000
export TURAC_LLM_ROUTER_KEY=your-key
promptguard audit task.md --judge --profile coding-agent --fail-on high
```

Default audit path stays offline. Judge failures exit 2.

### OpenClaw profile/fail-on

```bash
export PROMPTGUARD_PROFILE=coding-agent   # or system|security|general
export PROMPTGUARD_FAIL_ON=high           # or critical|medium|low|info|none
```

Only findings at or above fail-on severity block writes.

Save a JSONL report:

```bash
python3 -m promptguard audit prompts.py --format json --save
```

Reports are appended to:

```text
.promptguard/reports.jsonl
```

## Expected Output

For a vague coding request, expect:

```text
PG012 responsibility_contract
PG015 technical_risk_contract
```

PromptGuard returns:

- evidence
- impact
- missing/conflicting contract
- clarification questions
- approval criteria
- grounded fix draft (includes original wording)

## Install Agent Adapters

```bash
./install-agent-adapters.sh codex
./install-agent-adapters.sh claude
./install-agent-adapters.sh opencode
./install-agent-adapters.sh openclaw
```

Restart the agent after install.

The adapter install copies the skill bundle into each agent config/workspace directory. Skill scripts prefer the installed `promptguard` package for profiles, fail-on, SARIF, and accept-risk parity.

OpenClaw also installs a local plugin that registers `before_tool_call`. That plugin blocks `write`/`edit` tool calls when prompt-like content has unresolved PromptGuard findings.

## Codex Smoke Test

```bash
tmpdir=$(mktemp -d /tmp/pg-test.XXXXXX)
printf 'PROMPTS = {}\n' > "$tmpdir/prompts.py"
codex -a never exec \
  --cd "$tmpdir" \
  --skip-git-repo-check \
  --sandbox read-only \
  "Bu promptu prompts.py içine ekle: Fix this bug and write code."
```

Expected:

- runs PromptGuard before writing
- reports `PG012`
- does not edit the file unless risks are accepted

## OpenClaw Smoke Test

```bash
rm -f ~/.openclaw/workspace/prompts.py
openclaw agent --local --agent main --json --timeout 120 \
  --message "Bu promptu prompts.py içine ekle: Fix this bug and write code."
```

Expected:

- `promptguard blocked write`
- reports `PG012` and `PG015`
- `~/.openclaw/workspace/prompts.py` is not created

## Real-World Prompt Examples

Should fail:

```text
Prod auth patlıyor galiba, refresh atınca bazı kullanıcılar düşüyor. Bi bakıp hızlıca fixler misin, akşama deploy lazım.
```

Should pass:

```text
Act as the backend engineer responsible for src/auth/session.py and tests/auth. Fix the refresh-token logout bug only. Preserve public API behavior and do not refactor unrelated code. Validate expired token, reused token, and concurrent refresh edge cases. Verify with `pytest tests/auth -q`. Return changed files, root cause, verification output, deploy/rollback note, and residual risk.
```

## Rule IDs

Use these IDs in CI comments, PR reviews, and agent replies:

```text
PG001 privacy conflict
PG002 unsafe/passive escalation
PG004 weak tool/function schema
PG005 missing output contract
PG012 missing responsibility contract
PG015 missing technical risk contract
PG016 instruction-override without dual-control
PG017 system prompt disclosure risk
PG018 secret/tool exfiltration instructions
```

## Out of scope

- Interactive TUI (see `docs/TUI.md` concept only)
- Default LLM-as-judge pass
- Runtime chat rails / red-team attack generation
