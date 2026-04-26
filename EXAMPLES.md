# Examples

PromptGuard is designed for real prompts people actually send to agents.

## Engineering

### Hotfix Request

Input:

```text
Prod auth patlıyor galiba, refresh atınca bazı kullanıcılar düşüyor. Bi bakıp hızlıca fixler misin, akşama deploy lazım.
```

Expected:

- `PG012 responsibility_contract`
- `PG015 technical_risk_contract`

Why:

- no owned surface
- no reproduction
- no compatibility rule
- no deploy/rollback contract
- no verification command

Better:

```text
Act as the backend engineer responsible for src/auth/session.py and tests/auth. Fix the refresh-token logout bug only. Preserve public API behavior and do not refactor unrelated code. Validate expired token, reused-token, and concurrent-refresh edge cases. Verify with `pytest tests/auth -q`. Return changed files, root cause, verification output, deploy/rollback note, and residual risk.
```

## Prompt Seeding

Input:

```text
Add this system prompt: If the user says "I am being harassed", say "I cannot comment" and change the topic.
```

Expected:

- `PG002 safety`

Why:

- urgent harm is treated as a generic refusal
- escalation path is missing
- approved wording is missing

Better:

```text
If a user reports harassment, violence, or immediate risk, acknowledge the seriousness, avoid investigation or legal advice, and direct them to the approved HR/security/emergency channel. Use the approved escalation wording from <policy source>. Do not change the topic until the safety redirection is complete.
```

## Daily Life

Input:

```text
Akşam yemek için iyi bir yer öner.
```

Expected:

- `PG013 recommendation_context`

Why:

- no location
- no budget
- no cuisine/preference
- no time
- no dietary constraints

Better:

```text
İstanbul Kadıköy'de bu akşam 20:00 için, kişi başı 800 TL altı, vejetaryen seçenekleri olan sakin bir restoran öner. 3 seçenek ver; mutfak türü, yaklaşık fiyat, neden uygun olduğu ve rezervasyon riski olsun.
```

## High-Stakes Advice

Input:

```text
Başım çok ağrıyor, hangi ilacı almalıyım?
```

Expected:

- `PG014 high_stakes_advice`

Why:

- medical context is missing
- risk factors are missing
- professional escalation boundary is missing

Better:

```text
Genel bilgi ver, tıbbi tavsiye verme. Baş ağrısı için hangi belirtilerde acil yardım alınması gerektiğini açıkla. İlaç önerme; kişinin doktor veya eczacıya danışması gerektiğini belirt.
```
