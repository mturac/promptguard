import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";

function definePluginEntry(factory) {
  return factory;
}

const WRITE_TOOLS = new Set([
  "write",
  "edit",
  "patch",
  "apply_patch",
  "create_file",
  "update_file",
  "replace",
]);

const PROMPT_HINTS = [
  "prompt",
  "system prompt",
  "agent",
  "router",
  "orchestrator",
  "evaluator",
  "instruction",
  "instructions",
  "claude.md",
  "agents.md",
  "skill.md",
  "prompts.py",
];

const CONTENT_KEYS = new Set([
  "content",
  "text",
  "prompt",
  "instruction",
  "instructions",
  "system",
  "message",
  "new_string",
  "newString",
  "replacement",
  "value",
]);

const SEVERITY_RANK = {
  critical: 5,
  high: 4,
  medium: 3,
  low: 2,
  info: 1,
};

function norm(value) {
  return String(value ?? "").toLowerCase().replaceAll("ı", "i");
}

function hasPromptHint(text) {
  const lowered = norm(text);
  return PROMPT_HINTS.some((hint) => lowered.includes(norm(hint)));
}

function collectContent(value, parentKey = "", out = []) {
  if (typeof value === "string") {
    if (CONTENT_KEYS.has(parentKey) || value.length > 80 || hasPromptHint(value)) {
      out.push(value);
    }
    return out;
  }
  if (Array.isArray(value)) {
    for (const item of value) collectContent(item, parentKey, out);
    return out;
  }
  if (value && typeof value === "object") {
    for (const [key, item] of Object.entries(value)) collectContent(item, key, out);
  }
  return out;
}

function resolveSkillDirs() {
  return [
    join(homedir(), ".openclaw", "workspace", "skills", "promptguard"),
    join(homedir(), ".openclaw", "skills", "promptguard"),
  ].filter((path) => existsSync(path));
}

function resolveRulesPath() {
  for (const dir of resolveSkillDirs()) {
    const candidate = join(dir, "references", "rules.json");
    if (existsSync(candidate)) return candidate;
  }
  return undefined;
}

function loadJson(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

function resolveActiveRules(rulesPath) {
  const profile = process.env.PROMPTGUARD_PROFILE || "coding-agent";
  let rules = loadJson(rulesPath);
  if (!Array.isArray(rules)) rules = [];

  const skillDir = dirname(dirname(rulesPath));
  const packPath = join(skillDir, "references", "packs", `${profile}.json`);
  if (!existsSync(packPath)) {
    // unknown pack → use full catalog (general-like)
    return rules;
  }
  const pack = loadJson(packPath);
  if (pack.extra_rules) {
    const extraPath = join(skillDir, "references", "packs", pack.extra_rules);
    if (existsSync(extraPath)) {
      const extra = loadJson(extraPath);
      if (Array.isArray(extra)) {
        const byId = new Map(rules.map((r) => [r.id, r]));
        for (const rule of extra) byId.set(rule.id, rule);
        rules = [...byId.values()];
      }
    }
  }
  if (Array.isArray(pack.rule_ids)) {
    const allowed = new Set(pack.rule_ids);
    rules = rules.filter((r) => allowed.has(r.id));
  }
  // rule_ids null → all rules (general)
  return rules;
}

function failOnRank() {
  const failOn = (process.env.PROMPTGUARD_FAIL_ON || "high").toLowerCase();
  if (failOn === "none") return Infinity; // never block by severity
  return SEVERITY_RANK[failOn] ?? SEVERITY_RANK.high;
}

function isBlocking(finding) {
  const threshold = failOnRank();
  if (!Number.isFinite(threshold)) return false;
  const rank = SEVERITY_RANK[norm(finding.severity)] ?? 0;
  return rank >= threshold;
}

function truncate(text, max = 3500) {
  if (text.length <= max) return text;
  return `${text.slice(0, max)}\n\n[PromptGuard report truncated]`;
}

function shouldAudit(toolName, params) {
  if (!WRITE_TOOLS.has(norm(toolName))) return false;
  const haystack = JSON.stringify(params ?? {});
  return hasPromptHint(haystack);
}

function hasAny(text, terms = []) {
  return terms.some((term) => text.includes(norm(term)));
}

function matches(rule, text, original) {
  if (rule.min_chars && original.length < Number(rule.min_chars)) return false;
  if (rule.any && !hasAny(text, rule.any)) return false;
  if (rule.also_any && !hasAny(text, rule.also_any)) return false;
  if (rule.missing_any && hasAny(text, rule.missing_any)) return false;
  if (rule.missing_groups && rule.missing_groups.every((group) => hasAny(text, group))) return false;
  return true;
}

function evidence(rule, content) {
  for (const term of [...(rule.any ?? []), ...(rule.also_any ?? [])]) {
    const idx = content.toLowerCase().indexOf(term.toLowerCase());
    if (idx >= 0) {
      return content
        .slice(Math.max(0, idx - 80), Math.min(content.length, idx + 160))
        .replace(/\s+/g, " ");
    }
  }
  return "Rule matched by absence.";
}

function auditText(rules, content) {
  const text = norm(content);
  return rules
    .filter((rule) => matches(rule, text, content))
    .map((rule) => ({
      id: rule.id,
      severity: rule.severity,
      category: rule.category,
      title: rule.title,
      evidence: evidence(rule, content),
      impact: rule.impact,
      contract: rule.contract,
      fix: rule.fix_draft,
      ask: (rule.clarifying_questions ?? []).join(" | ") || "No clarification needed; apply the contract fix.",
      approval: rule.approval_contract || "Approve only when the missing contract is explicit enough to verify.",
    }));
}

function renderMarkdown(findings, meta = {}) {
  const lines = [
    "# PromptGuard Audit",
    "",
    "Source: OpenClaw before_tool_call",
    `Profile: ${meta.profile || "coding-agent"}`,
    `Fail-on: ${meta.failOn || "high"}`,
    `Findings: ${findings.length}`,
    `Blocking: ${findings.filter(isBlocking).length}`,
  ];
  for (const finding of findings) {
    lines.push(
      "",
      `## ${finding.severity.toUpperCase()} · ${finding.category} · ${finding.id}`,
      `Evidence: ${finding.evidence}`,
      `Impact: ${finding.impact}`,
      `Contract: ${finding.contract}`,
      `Ask: ${finding.ask}`,
      `Approval: ${finding.approval}`,
      `Fix draft: ${finding.fix}`,
    );
  }
  return lines.join("\n");
}

export default definePluginEntry((api = {}) => {
  api.on?.(
    "before_tool_call",
    async (event) => {
      if (process.env.PROMPTGUARD_OPENCLAW_DISABLE === "1") return;
      if (!shouldAudit(event?.toolName, event?.params)) return;

      const rulesPath = resolveRulesPath();
      if (!rulesPath) {
        return {
          block: true,
          blockReason:
            "PromptGuard blocked this prompt write because rules.json is not installed in the OpenClaw skill directory.",
        };
      }

      const content = collectContent(event?.params).join("\n\n---\n\n").trim();
      if (!content) return;

      const profile = process.env.PROMPTGUARD_PROFILE || "coding-agent";
      const failOn = process.env.PROMPTGUARD_FAIL_ON || "high";
      const rules = resolveActiveRules(rulesPath);
      const findings = auditText(rules, content);
      const blocking = findings.filter(isBlocking);
      if (blocking.length === 0) return;

      const output = renderMarkdown(findings, { profile, failOn });
      api.logger?.warn?.(
        `promptguard blocked ${event?.toolName}: ${blocking.length} blocking / ${findings.length} total (profile=${profile} fail-on=${failOn})`,
      );
      return {
        block: true,
        blockReason:
          "PromptGuard blocked this prompt write. Report the findings to the user and ask for approval or provide a fixed draft before writing.\n\n" +
          truncate(output),
      };
    },
    { priority: 10000 },
  );

  return {
    name: "promptguard",
  };
});
