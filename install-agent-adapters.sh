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
  mkdir -p "$HOME/.config/openclaw/skills"
  rm -rf "$HOME/.config/openclaw/skills/promptguard"
  cp -R "$ROOT/skills/promptguard" "$HOME/.config/openclaw/skills/promptguard"
  install_block "$ROOT/adapters/openclaw/AGENTS.md" "$HOME/.config/openclaw/AGENTS.md" "PROMPTGUARD"
  echo "Installed PromptGuard rules and skill for OpenClaw."
}

case "${1:-all}" in
  codex) install_codex ;;
  claude) install_claude ;;
  opencode) install_opencode ;;
  openclaw) install_openclaw ;;
  all) install_codex; install_claude; install_opencode; install_openclaw ;;
  *) echo "Usage: $0 [all|codex|claude|opencode|openclaw]" >&2; exit 2 ;;
esac
