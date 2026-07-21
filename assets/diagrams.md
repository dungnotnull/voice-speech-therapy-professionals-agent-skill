# System Architecture Diagrams

Visual representations of the skill architecture and data flow.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INPUT                                   │
│                    (Query in EN or VI)                               │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    main.md (Harness)                                │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Pre-Flight: Language Detection                                │  │
│  │ ├─ Detect Vietnamese characters                               │  │
│  │ ├─ Identify domain-specific words                            │  │
│  │ └─ Store LANG (en/vi)                                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Hook Emission: skill.pre_invoke                               │  │
│  │ ├─ Audit logging                                              │  │
│  │ ├─ State initialization                                        │  │
│  │ └─ Performance monitoring                                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  sub-gather  │    │   sub-evid    │    │  sub-core    │
│ requirements │    │   collector   │    │   analysis    │
│              │    │              │    │              │
│ • 14-field   │    │ • Per-query  │    │ • CAPE-V     │
│   intake     │    │   search     │    │ • GRBAS      │
│ • 6-subtype  │    │ • Recency    │    │ • Acoustic   │
│   class      │    │   thresholds │    │   norms      │
│ • Red-flag   │    │ • Fallback   │    │ • Exercise   │
│   detect     │    │   chain      │    │   library    │
└──────────────┘    └──────────────┘    │ • Diff dx    │
                                       │ • Triage     │
                                       └──────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ sub-knowledge│    │  sub-advisor │    │ Quality Gate │
│   updater    │    │              │    │   System     │
│              │    │ • Decision   │    │              │
│ • Query KB   │    │   tree       │    │ • U1-U6      │
│ • Surface    │    │ • Risk       │    │ • G1-G4      │
│   citations  │    │   matrix     │    │ • Auto-fix   │
│ • Assess     │    │ • Evidence   │    │ • Retry      │
│   coverage   │    │   chain      │    │ • Enforce    │
│ • Flag gaps  │    │ • Scenarios  │    │ • Degrade    │
└──────────────┘    │ • Remediate │    └──────────────┘
                   └──────────────┘             │
                                                 │
                                                 ▼
                                      ┌──────────────────┐
                                      │  Final Output    │
                                      │  (Bilingual)     │
                                      │                  │
                                      │ • Structured     │
                                      │   report         │
                                      │ • Gate footer    │
                                      │ • Disclosure      │
                                      └──────────────────┘
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Data Sources                               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │   ArXiv    │  │Semantic    │  │   RSS      │  │SECOND-     │  │
│  │(cs.CL,     │  │Scholar     │  │Feeds       │  │KNOWLEDGE-  │  │
│  │ eess.AS)   │  │            │  │            │  │BRAIN.md    │  │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Knowledge Pipeline                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ knowledge_updater.py                                          │  │
│  │ ├─ Async fetch (httpx)                                        │  │
│  │ ├─ Rate limiting (TokenBucket)                                │  │
│  │ ├─ SHA256 dedup                                                │  │
│  │ ├─ Composite scoring (recency + relevance + citations)         │  │
│  │ ├─ Atomic writes (temp + rename)                               │  │
│  │ └─ File locking (portalocker)                                  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Output: Appended to SECOND-KNOWLEDGE-BRAIN.md                  │  │
│  │ ├─ New papers with DOIs                                       │  │
│  │ ├─ Tier labels (1-4)                                          │  │
│  │ └─ Update log entry                                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Skill Execution                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │sub-gather  │→ │sub-evid    │→ │sub-core    │→ │sub-knowledge│  │
│  │   reqs     │  │   collector│  │   analysis │  │   updater   │  │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘  │
│                                                                   │
│  Shared State: StateManager                                        │
│  ├─ user_profession                                               │
│  ├─ symptoms                                                      │
│  ├─ medical_history                                               │
│  ├─ collected_evidence                                            │
│  ├─ assessment_scores                                             │
│  └─ knowledge_citations                                           │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Quality Gate System                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Universal Gates (U1-U6)                                       │  │
│  │ U1: ≥3 sources, ≥1 academic                                   │  │
│  │ U2: Disclosure before recommendations                         │  │
│  │ U3: Evidence hierarchy tiers (1-4)                            │  │
│  │ U4: Language match (en/vi)                                    │  │
│  │ U5: Template compliance (all sections)                         │  │
│  │ U6: Claims traceable to sources                               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Domain Gates (G1-G4)                                          │  │
│  │ G1: Measurable voice dimensions (CAPE-V + GRBAS)              │  │
│  │ G2: Evidence-based exercises with dosage                     │  │
│  │ G3: Red-flag referral with urgency                           │  │
│  │ G4: Measurable articulation targets                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Enforcement Logic:                                                │
│  ├─ Check condition                                                │
│  ├─ Run auto-fix if failed                                        │
│  ├─ Retry up to 2×                                                │
│  └─ Block or flag limitation                                      │
└────────────────────────┬───────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Output                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Structured Report (bilingual)                                  │  │
│  │ ├─ Executive Summary                                           │  │
│  │ ├─ Inputs & Scope                                              │  │
│  │ ├─ Evidence Collected (with tiers)                             │  │
│  │ ├─ Analysis (CAPE-V, GRBAS, Acoustic, Diff dx)               │  │
│  │ ├─ Action Plan (Exercise protocol with dosage)                 │  │
│  │ ├─ Academic Evidence (3-5 citations)                          │  │
│  │ ├─ Disclosure (mandatory)                                      │  │
│  │ ├─ Conclusion (one of 5 categories)                             │  │
│  │ ├─ Scenarios (Best/Base/Worst)                                 │  │
│  │ ├─ Risk Matrix (≥3 risks)                                     │  │
│  │ ├─ Evidence Chain (claim ← source)                             │  │
│  │ ├─ Remediation (immediate to long-term)                        │  │
│  │ └─ Gate Checklist footer                                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Hook Manager                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Registered Hooks                                               │  │
│  │ ├─ audit-log (skill.pre_invoke, priority: HIGH)              │  │
│  │ ├─ state-init (skill.pre_invoke, priority: NORMAL)            │  │
│  │ ├─ perf-monitor (skill.post_invoke, priority: LOW)            │  │
│  │ └─ error-handler (error.on_failure, priority: CRITICAL)      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Event Types:                                                        │
│  ├─ skill.pre_invoke                                               │
│  ├─ skill.post_invoke                                              │
│  ├─ tool.pre_execute                                               │
│  ├─ tool.post_execute                                              │
│  ├─ quality_gate.pre_check                                         │
│  ├─ quality_gate.post_check                                        │
│  └─ error.on_failure                                               │
└──────────────┬──────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      State Manager                                  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Shared State (versioned)                                      │  │
│  │ ├─ user_profession: "podcaster"                               │  │
│  │ ├─ symptoms: ["hoarseness", "fatigue"]                        │  │
│  │ ├─ assessment: {capev: {...}, grbas: {...}}                 │  │
│  │ ├─ collected_evidence: [{source, tier, date}, ...]           │  │
│  │ └─ knowledge_citations: [{citation, tier, year}, ...]        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Operations:                                                         │
│  ├─ get(key, default=None)                                         │
│  ├─ set(key, value) → increments version                           │
│  ├─ delete(key)                                                     │
│  └─ get_version()                                                   │
└──────────────┬──────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Tool Executor                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Registered Tools                                               │  │
│  │ ├─ knowledge_query (timeout: 10s, retry: yes)                │  │
│  │ ├─ evidence_fetch (timeout: 30s, retry: yes)                  │  │
│  │ ├─ capev_assess (timeout: 5s, retry: no)                     │  │
│  │ ├─ grbas_assess (timeout: 5s, retry: no)                     │  │
│  │ └─ exercise_prescribe (timeout: 10s, retry: no)               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Execution Flow:                                                     │
│  ├─ Input validation (against schema)                               │
│  ├─ Handler invocation (with timeout)                               │
│  ├─ Retry logic (if enabled)                                        │
│  ├─ Output validation (against schema)                              │
│  └─ Result return with execution time                               │
└─────────────────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Error Detection                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Error Types                                                    │  │
│  │ ├─ Source timeout (no response in 30s)                       │  │
│  │ ├─ Invalid input (schema mismatch)                            │  │
│  │ ├─ Missing input (required field absent)                      │  │
│  │ ├─ Stale reading (timestamp > threshold)                      │  │
│  │ ├─ KB miss (no matches in knowledge base)                     │  │
│  │ ├─ Conflicting actions (mutually exclusive)                    │  │
│  │ ├─ Envelope unavailable (no setpoint for object)               │  │
│  │ └─ Object/class ambiguous (classification unclear)              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Error Recovery                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Recovery Actions                                              │  │
│  │ ├─ Retry alternate source (up to 3×)                          │  │
│  │ ├─ Ask user to confirm (up to 2×)                            │  │
│  │ ├─ Proceed with available + flag                             │  │
│  │ ├─ Flag stale, request refresh (1×)                           │  │
│  │ ├─ WebSearch gap-fill + queue crawl (2×)                     │  │
│  │ ├─ Apply stated precedence                                   │  │
│  │ ├─ Use genus/category fallback + flag (1×)                   │  │
│  │ └─ Ask user to confirm classification (2×)                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Graceful Degradation                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Degradation Levels                                             │  │
│  │ Level 0: All sources reachable → Full analysis                │  │
│  │ Level 1: Some sources fail → Use secondary + flag             │  │
│  │ Level 2: Most live sources fail → KB only + "historical"      │  │
│  │ Level 3: Input missing → Mark unavailable + no fabrication     │  │
│  │ Level 4: All sources + KB fail → "DATA UNAVAILABLE" notice     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  LIMITATION banner template:                                         │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ ⚠️ LIMITATION NOTICE                                          │  │
│  │ This output was generated with reduced data availability      │  │
│  │ (Level {N}). Cross-check with current data before acting.     │  │
│  │ Substituted/missing sources are flagged inline.                │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```
