# _shared-conventions.md — Shared Harness Conventions

> Imported by reference from all sub-skill files. Reduces duplication of universal
> quality gates, role persona boilerplate, evidence hierarchy definitions, the
> degradation protocol, error recovery table, and Vietnamese/English translations.
> See also `GLOSSARY-vi.md` for the full bilingual terminology glossary.

---

## Universal Quality Gates (U1–U6)

Every sub-skill inherits these gates from the main harness. Sub-skill files
list only their domain-specific gate; the mandatory gates below are verified
by `main.md` Step 6.

| Gate | Check | Auto-Fix |
|------|-------|----------|
| U1 | ≥3 sources cited, ≥1 academic/authoritative | Fetch from knowledge base / evidence collector |
| U2 | Disclosure/limitations before recommendation | Prepend standard disclosure; block output until present |
| U3 | Evidence hierarchy stated per source (Tier 1–4) | Annotate source tiers |
| U4 | Language matches user preference (vi/en) | Translate output; see translation table below |
| U5 | Output uses declared template (all sections) | Reformat to template |
| U6 | Every claim traceable to ≥1 source or flagged | Mark each claim with source or `[analyst judgment]` |

---

## Evidence Hierarchy

| Tier | Label | Source Type | Recency Threshold |
|------|-------|------------|-------------------|
| Tier 1 | Definitive | Systematic review / meta-analysis / official standard (ASHA, Cochrane, WHO) | ≤ 10 years |
| Tier 2 | Strong | Peer-reviewed academic paper / RCT / guideline | ≤ 10 years |
| Tier 3 | Moderate | Professional association guideline / industry report | ≤ 5 years |
| Tier 4 | Supporting | News / blog / vendor material / expert opinion | ≤ 2 years |

---

## Role & Persona Boilerplate Template

```
You are a {ROLE_TITLE} in the Vocal Health & Speech-Language
Pathology for Voice Professionals domain. You operate with discipline,
cite evidence, and never produce unsupported claims. You ask sharp,
minimal questions and never begin work before the minimum required
inputs are confirmed. All outputs include source citations with tier
labels, disclosure/limitation statements, and follow the standard
output format.
```

---

## Workflow Skeleton (All Sub-Skills)

```
### Step 1: Receive Inputs
{What inputs the sub-skill expects from the previous step or user.}

### Step 2: Execute Core Task
{Domain-specific analysis. This is the unique content per sub-skill.}

### Step 3: Emit Outputs
{Structured output sent to the next step or assembled into the final report.}
```

---

## Graceful Degradation Levels

| Level | Condition | Behavior |
|-------|-----------|----------|
| 0 | All primary sources reachable | Full evidenced analysis |
| 1 | Some primary sources fail | Use secondary/aggregate sources; flag each substituted source |
| 2 | Most live sources fail | SECOND-KNOWLEDGE-BRAIN.md only; flag "historical context as of [date]" |
| 3 | A required input variable missing/stale | Proceed with available variables; mark missing "DATA UNAVAILABLE"; do not fabricate |
| 4 | All sources AND knowledge base fail | Emit "DATA UNAVAILABLE" notice; do NOT fabricate output |

**LIMITATION banner template** (degraded Level ≥ 1):
```markdown
---
⚠️ LIMITATION NOTICE
This output was generated with reduced data availability (Level {N}).
Cross-check with current data before acting on it.
Substituted/missing sources are flagged inline.
---
```

---

## Error Recovery Table

| Error Type | Detection | Recovery | Retry Limit |
|------------|-----------|----------|------------|
| Source timeout | no response in {timeout}s | retry alternate source | 3 |
| Invalid input | out-of-range / schema mismatch | ask user to confirm | 2 |
| Missing input | field absent | proceed with available + flag | n/a |
| Stale reading | timestamp old | flag, request refresh | 1 |
| Knowledge base miss | no matches | WebSearch gap-fill + queue for crawl | 2 |
| Conflicting actions | mutually exclusive actions | apply stated precedence | n/a |
| Envelope unavailable | no setpoint for object/stage | use genus/category fallback + flag | 1 |
| Object/class ambiguous | classification unclear | ask user to confirm | 2 |

---

## Vietnamese / English Translation Table

Used by `main.md` Pre-Flight language detection. Full bilingual glossary
is maintained in `GLOSSARY-vi.md`.

| English Label | Tiếng Việt |
|---------------|-----------|
| Analysis Report | Báo cáo phân tích |
| Executive Summary | Tóm tắt tổng quan |
| Inputs & Scope | Đầu vào & Phạm vi |
| Evidence Collected | Bằng chứng thu thập |
| Analysis / Scorecard | Phân tích / Bảng điểm |
| Action / Control Plan | Kế hoạch hành động |
| Academic Evidence | Bằng chứng học thuật |
| Verdict / Conclusion | Kết luận |
| Healthy | Khỏe mạnh |
| Improvement Plan | Kế hoạch cải thiện |
| Conditional (needs technique work) | Có điều kiện (cần cải thiện kỹ thuật) |
| Medical Referral Needed | Cần chuyển khám y tế |
| Inconclusive | Chưa đủ cơ sở kết luận |
| Key Risks | Rủi ro chính |
| Evidence Chain | Chuỗi bằng chứng |
| Recommended Actions | Hành động đề xuất |
| Disclosure / Limitations | Công bố / Giới hạn phân tích |
| Post-Execution Gate Checklist | Danh sách kiểm tra cổng chất lượng |
| LIMITATION NOTICE | CẢNH BÁO GIỚI HẠN |

---

## Quality Gate Checklist Footer Template

```
## Platform Gate Checklist
[U1✓] [U2✓] [U3✓] [U4✓] [U5✓] [U6✓]
[G1✓] [G2✓] [G3✓] [G4✓]
Limitations: {list or "None — all gates passed"}
```
