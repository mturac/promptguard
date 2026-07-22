# PromptGuard for Hermes

Pre-write contract audit for Hermes Agent (Nous Research).

## What you got

- **Skill** → `$HERMES_HOME/skills/promptguard` — use `/promptguard` in chat
- **Plugin** → `$HERMES_HOME/plugins/promptguard` — `pre_tool_call` blocks prompt-like writes
- **AGENTS.md** block — always-on instruction for the agent
- **Optional shell hook** → `$HERMES_HOME/agent-hooks/pre_tool_promptguard.py`

`$HERMES_HOME` is the **active profile** directory (`hermes config path`), not always `~/.hermes`.

## Env

```bash
export PROMPTGUARD_PROFILE=coding-agent   # general|coding-agent|system|security
export PROMPTGUARD_FAIL_ON=high           # critical|high|medium|low|info|none
# PROMPTGUARD_HERMES_DISABLE=1            # emergency off
```

## Restart

Restart the Hermes CLI / gateway so the plugin loads.

```bash
hermes plugins list    # promptguard should show enabled
```

## Manual audit

```bash
printf '%s' 'Fix this bug and write code.' | \
  python3 "$HERMES_HOME/skills/promptguard/scripts/audit_prompt.py" - \
  --profile coding-agent --fail-on high --format markdown
```
