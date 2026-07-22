# Changelog

## 0.4.1

- Hermes Agent adapter (first-class): skill + `pre_tool_call` plugin + shell hook + AGENTS.md.
- Installer resolves **active Hermes profile** via `hermes config path` (not only `~/.hermes`).
- Hermes skill frontmatter tags for Skills Hub / `/promptguard` discovery.
- Docs: Hermes elevated alongside Claude/Codex/OpenClaw as a primary agent surface.
- Installer: `./install-agent-adapters.sh hermes` (also included in `all`).

## 0.4.0

- OpenClaw plugin: `PROMPTGUARD_PROFILE` (default `coding-agent`) and `PROMPTGUARD_FAIL_ON` (default `high`); pack-aware rule filter.
- Skill pack metadata under `skills/promptguard/references/packs/`.
- Claude hook script uses package auditor with coding-agent profile.
- `promptguard tui PATH` minimal interactive review (non-TTY table fallback).
- Opt-in `--judge` second pass via turac-llm-router (`TURAC_LLM_ROUTER_URL` / `TURAC_LLM_ROUTER_KEY`).

## 0.3.0

- Baseline regression: `--baseline PATH` and `--fail-on-new` on audit/audit-repo.
- Match modes: `word_any` / `word_also_any` / `word_missing_any` and `regex_*` rule fields.
- `promptguard export-promptfoo` converts eval JSONL to a promptfoo YAML skeleton.
- Classic substring rule fields remain backward compatible.

## 0.2.0

- Profiles: `general`, `coding-agent`, `system`, `security` (`--profile`).
- Severity exit gate: `--fail-on` (legacy any-finding when omitted).
- Rule packs under `promptguard/packs/` plus `--rules PATH`.
- Multi-surface extractors: SKILL/AGENTS/CLAUDE.md, JSON/YAML prompt keys, fenced blocks.
- `promptguard audit-repo` with include/exclude globs.
- SARIF 2.1.0 report format (`--format sarif`).
- Grounded fix drafts (preserve original wording + contract checklist).
- Accept-risk trail: `--accept-risk ID:reason`, `--apply-accepted`.
- Security pack rules PG016–PG018 + `eval/security_cases.jsonl`.
- Skill scripts delegate to package CLI for flag parity.

## 0.1.0

- Initial CLI: `promptguard audit`.
- Stdin audit support with `promptguard audit -`.
- JSON/markdown/table reports.
- JSONL report store at `.promptguard/reports.jsonl`.
- Installable Codex/Claude/OpenCode/OpenClaw skill bundle.
- Pre-write guard for prompt-like edits.
- Responsibility contract checks for coding prompts.
- Technical risk contract checks for real-world engineering requests.
- Daily-life and real-world eval suites.
