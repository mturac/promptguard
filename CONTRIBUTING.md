# Contributing

PromptGuard is rule-driven. Contributions should include tests.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest -q
```

## Adding Rules

1. Add or update a rule in `promptguard/rules.json`.
2. Copy it to the installable skill:

```bash
cp promptguard/rules.json skills/promptguard/references/rules.json
```

3. Add eval coverage in one of:

```text
eval/cases.jsonl
eval/daily_life_cases.jsonl
eval/technical_cases.jsonl
eval/real_world_usage_cases.jsonl
```

4. Add or update tests.

## Rule Quality

Good rules produce:

- evidence
- impact
- missing/conflicting contract
- clarification questions
- approval criteria
- fix draft

Avoid rules that only say "this is vague." The user should know what decision is missing and what to ask next.
