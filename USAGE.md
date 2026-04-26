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
- fix draft

## Install Agent Adapters

```bash
./install-agent-adapters.sh codex
./install-agent-adapters.sh claude
./install-agent-adapters.sh opencode
./install-agent-adapters.sh openclaw
```

Restart the agent after install.

The adapter install copies the self-contained skill bundle into each agent config/workspace directory. The agent can use the bundled audit scripts even if the `promptguard` CLI is not globally installed.

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
```
