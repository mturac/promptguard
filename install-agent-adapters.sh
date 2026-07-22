#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install_block() {
  local src="$1"
  local dest="$2"
  local name="$3"
  mkdir -p "$(dirname "$dest")"
  touch "$dest"
  python3 - "$src" "$dest" "$name" <<'PY'
from pathlib import Path
import sys

src = Path(sys.argv[1])
dest = Path(sys.argv[2])
name = sys.argv[3]
start = f"<!-- BEGIN {name} -->"
end = f"<!-- END {name} -->"
block = f"{start}\n{src.read_text(encoding='utf-8').strip()}\n{end}\n"
text = dest.read_text(encoding="utf-8")
if start in text and end in text:
    before = text.split(start, 1)[0]
    after = text.split(end, 1)[1]
    text = before.rstrip() + "\n\n" + block + after.lstrip()
else:
    text = text.rstrip() + "\n\n" + block
dest.write_text(text, encoding="utf-8")
PY
}

install_block_prepend() {
  local src="$1"
  local dest="$2"
  local name="$3"
  mkdir -p "$(dirname "$dest")"
  touch "$dest"
  python3 - "$src" "$dest" "$name" <<'PY'
from pathlib import Path
import sys

src = Path(sys.argv[1])
dest = Path(sys.argv[2])
name = sys.argv[3]
start = f"<!-- BEGIN {name} -->"
end = f"<!-- END {name} -->"
block = f"{start}\n{src.read_text(encoding='utf-8').strip()}\n{end}\n"
text = dest.read_text(encoding="utf-8")
if start in text and end in text:
    before = text.split(start, 1)[0]
    after = text.split(end, 1)[1]
    text = before.rstrip() + "\n" + after.lstrip()
text = block + "\n" + text.lstrip()
dest.write_text(text, encoding="utf-8")
PY
}

install_codex() {
  mkdir -p "$HOME/.codex/skills" "$HOME/.codex"
  rm -rf "$HOME/.codex/skills/promptguard"
  cp -R "$ROOT/skills/promptguard" "$HOME/.codex/skills/promptguard"
  install_block "$ROOT/adapters/codex/AGENTS.md" "$HOME/.codex/AGENTS.md" "PROMPTGUARD"
  echo "Installed PromptGuard for Codex. Restart Codex."
}

install_claude() {
  mkdir -p "$HOME/.claude/skills" "$HOME/.claude/commands"
  rm -rf "$HOME/.claude/skills/promptguard"
  cp -R "$ROOT/skills/promptguard" "$HOME/.claude/skills/promptguard"
  cp "$ROOT/adapters/claude/commands/prompt-audit.md" "$HOME/.claude/commands/prompt-audit.md"
  install_block "$ROOT/adapters/claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md" "PROMPTGUARD"
  echo "Skill and command installed for Claude."
  echo "Merge adapters/claude/settings.promptguard.json into ~/.claude/settings.json to enable automatic hooks."
}

install_opencode() {
  mkdir -p "$HOME/.config/opencode/commands" "$HOME/.config/opencode/skills"
  rm -rf "$HOME/.config/opencode/skills/promptguard"
  cp -R "$ROOT/skills/promptguard" "$HOME/.config/opencode/skills/promptguard"
  cp "$ROOT/adapters/opencode/commands/prompt-audit.md" "$HOME/.config/opencode/commands/prompt-audit.md"
  install_block "$ROOT/adapters/opencode/AGENTS.md" "$HOME/.config/opencode/AGENTS.md" "PROMPTGUARD"
  echo "Installed PromptGuard rules, skill, and command for OpenCode."
}

install_openclaw() {
  mkdir -p "$HOME/.openclaw/workspace/skills" "$HOME/.openclaw/skills"
  rm -rf "$HOME/.openclaw/workspace/skills/promptguard" "$HOME/.openclaw/skills/promptguard"
  cp -R "$ROOT/skills/promptguard" "$HOME/.openclaw/workspace/skills/promptguard"
  cp -R "$ROOT/skills/promptguard" "$HOME/.openclaw/skills/promptguard"
  install_block_prepend "$ROOT/adapters/openclaw/AGENTS.md" "$HOME/.openclaw/workspace/AGENTS.md" "PROMPTGUARD"
  if command -v openclaw >/dev/null 2>&1; then
    openclaw plugins uninstall promptguard >/dev/null 2>&1 || true
    openclaw plugins install --link "$ROOT/adapters/openclaw/plugin" >/dev/null
    openclaw plugins enable promptguard >/dev/null || true
    echo "Installed PromptGuard rules, skill, and pre-write plugin for OpenClaw."
  else
    echo "Installed PromptGuard rules and skill for OpenClaw. Install the plugin later with: openclaw plugins install --link adapters/openclaw/plugin"
  fi
}

install_hermes() {
  # Prefer active Hermes profile home (hermes config path → …/config.yaml).
  local HERMES_HOME="${HERMES_HOME:-}"
  if [[ -z "$HERMES_HOME" ]] && command -v hermes >/dev/null 2>&1; then
    local cfg_path
    cfg_path="$(hermes config path 2>/dev/null || true)"
    if [[ -n "$cfg_path" && -f "$cfg_path" ]]; then
      HERMES_HOME="$(cd "$(dirname "$cfg_path")" && pwd)"
    fi
  fi
  HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

  mkdir -p "$HERMES_HOME/skills" "$HERMES_HOME/plugins" "$HERMES_HOME/agent-hooks"

  # Skill (agentskills.io / Hermes skills dir)
  rm -rf "$HERMES_HOME/skills/promptguard"
  cp -R "$ROOT/skills/promptguard" "$HERMES_HOME/skills/promptguard"

  # Python pre_tool_call plugin (CLI + gateway)
  rm -rf "$HERMES_HOME/plugins/promptguard"
  cp -R "$ROOT/adapters/hermes/plugin" "$HERMES_HOME/plugins/promptguard"

  # Optional shell-hook script (manual config.yaml wiring)
  cp "$ROOT/adapters/hermes/agent-hooks/pre_tool_promptguard.py" \
    "$HERMES_HOME/agent-hooks/pre_tool_promptguard.py"
  chmod +x "$HERMES_HOME/agent-hooks/pre_tool_promptguard.py"

  # Workspace / home AGENTS.md instruction block
  if [[ -f "$HERMES_HOME/workspace/AGENTS.md" ]]; then
    install_block_prepend "$ROOT/adapters/hermes/AGENTS.md" "$HERMES_HOME/workspace/AGENTS.md" "PROMPTGUARD"
  elif [[ -f "$HERMES_HOME/AGENTS.md" ]]; then
    install_block_prepend "$ROOT/adapters/hermes/AGENTS.md" "$HERMES_HOME/AGENTS.md" "PROMPTGUARD"
  else
    mkdir -p "$HERMES_HOME"
    install_block_prepend "$ROOT/adapters/hermes/AGENTS.md" "$HERMES_HOME/AGENTS.md" "PROMPTGUARD"
  fi

  if command -v hermes >/dev/null 2>&1; then
    # Enable against the same profile home we just installed into
    if HERMES_HOME="$HERMES_HOME" hermes plugins enable promptguard 2>/dev/null; then
      :
    else
      # Fallback: append allow-list entry without rewriting whole config
      python3 - "$HERMES_HOME/config.yaml" <<'PY'
from pathlib import Path
import sys
cfg = Path(sys.argv[1])
if not cfg.exists():
    sys.exit(0)
text = cfg.read_text(encoding="utf-8")
if "promptguard" in text and "enabled:" in text:
    sys.exit(0)
if "\nplugins:" not in text and not text.startswith("plugins:"):
    cfg.write_text(text.rstrip() + "\n\nplugins:\n  enabled:\n    - promptguard\n", encoding="utf-8")
else:
    cfg.write_text(
        text.rstrip()
        + "\n  # promptguard (install-agent-adapters)\n  # ensure plugins.enabled includes promptguard\n",
        encoding="utf-8",
    )
PY
    fi
    echo "Installed PromptGuard skill + pre_tool_call plugin for Hermes ($HERMES_HOME)."
    echo "Restart hermes / gateway. Env: PROMPTGUARD_PROFILE=coding-agent PROMPTGUARD_FAIL_ON=high"
    echo "Optional shell hook (if you prefer config.yaml hooks):"
    echo "  hooks.pre_tool_call → $HERMES_HOME/agent-hooks/pre_tool_promptguard.py"
  else
    echo "Installed PromptGuard under $HERMES_HOME (hermes CLI not on PATH)."
    echo "Enable plugin later with: HERMES_HOME=$HERMES_HOME hermes plugins enable promptguard"
  fi
}

case "${1:-all}" in
  codex) install_codex ;;
  claude) install_claude ;;
  opencode) install_opencode ;;
  openclaw) install_openclaw ;;
  hermes) install_hermes ;;
  all) install_codex; install_claude; install_opencode; install_openclaw; install_hermes ;;
  *) echo "Usage: $0 [all|codex|claude|opencode|openclaw|hermes]" >&2; exit 2 ;;
esac
