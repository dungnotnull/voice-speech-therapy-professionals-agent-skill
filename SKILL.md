---
name: voice-speech-therapy-professionals
description: Voice & Speech Therapy & Articulation Coach for Voice Professionals (MC, Podcaster, Teacher) — Vocal Health & Speech-Language Pathology for Voice Professionals evidence-backed analysis harness. Use this skill when the user asks about voice health, speech therapy, vocal exercises, articulation drills, voice professional care, or needs analysis of voice/speech conditions. This skill applies to voice teachers, podcasters, MCs, actors, singers, call center workers, and anyone who uses their voice professionally.
version: 2.0.0
author: 972026 Skill Library
tags: [voice, speech, therapy, vocal-health, speech-language-pathology, articulation, voice-professionals, esl, vietnamese]
dependencies: []
---

# SKILL.md — Skill Registry & Execution Specification

This document defines the complete contract for the `voice-speech-therapy-professionals` skill, including registration, resolution, execution, validation, and the flexible agent/skill architecture.

## Skill Registration

### Registry Entry

```yaml
name: voice-speech-therapy-professionals
version: 2.0.0
description: Vocal Health & Speech-Language Pathology analysis harness
author: 972026 Skill Library
tags: [voice, speech, therapy, vocal-health, speech-language-pathology]
```

### Registration Protocol

Skills are auto-discovered from the `skills/` directory at runtime. Each skill must:

1. **Export a `SKILL.md` file** at its root with YAML frontmatter
2. **Define input/output schemas** in `config/schemas.py`
3. **Implement quality gates** in `skills/_shared-conventions.md`
4. **Provide handler functions** for all declared tools

### Skill Resolution

When a user query is received, the harness:

1. **Computes relevance scores** for each registered skill based on:
   - Semantic similarity between query and skill description
   - Tag matching (weighted higher)
   - Dependency satisfaction (if skill depends on others)

2. **Selects top skill** if score > threshold (default: 0.7)

3. **Invokes skill** with structured context

### Skill Execution Model

#### Phase 1: Pre-Invocation

```
USER QUERY → Language Detection → Context Assembly → Hook Emission
```

1. **Language Detection**: Analyze input for Vietnamese characters (àáảãạăâđèéêìíòóôơùúưý) or domain-specific Vietnamese words. Store as `LANG` (default: "en").

2. **Context Assembly**:
   ```python
   context = SkillExecutionContext(
       skill_name="voice-speech-therapy-professionals",
       session_id=generate_uuid(),
       user_id=None,  # Could be from auth
       language=LANG,
       inputs=user_inputs,
       state={},
       metadata={"timestamp": iso_now()}
   )
   ```

3. **Hook Emission**: Emit `skill.pre_invoke` event to registered hooks.

#### Phase 2: Skill Execution

```
main.md → sub-gather-requirements → sub-evidence-collector →
sub-core-analysis → sub-knowledge-updater → sub-advisor → QUALITY GATE
```

Each sub-skill is invoked sequentially with:

- **Inputs**: Output from previous step
- **State**: Shared state via `StateManager`
- **Hooks**: Pre/post execution events
- **Retry**: On failure with degradation protocol

#### Phase 3: Quality Gate Review

```
Apply U1-U6 + G1-G4 → Auto-fix on failure → Retry up to 2× →
Enforce or flag limitation
```

Each gate:
1. Checks condition
2. Runs auto-fix if failed
3. Retries if auto-fix attempted
4. Enforces (blocks) or flags (continues with warning)

#### Phase 4: Post-Invocation

```
Format Output → Hook Emission → Return to User
```

1. **Format Output**: Apply bilingual template per language
2. **Hook Emission**: Emit `skill.post_invoke` event
3. **Return**: Final output with gate checklist footer

## Input/Output Schemas

### Skill Input Schema

```json
{
  "type": "object",
  "properties": {
    "profession": {
      "type": "string",
      "enum": ["teacher", "podcaster", "mc-host", "actor", "singer", "call-center", "other"],
      "description": "Voice professional subtype"
    },
    "symptoms": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Current vocal symptoms or complaints"
    },
    "duration": {
      "type": "string",
      "description": "Duration of symptoms (e.g., '2 weeks')"
    },
    "medical_history": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Relevant medical history"
    },
    "lifestyle": {
      "type": "object",
      "properties": {
        "hydration": {"type": "string"},
        "vocal_load": {"type": "string"},
        "smoking": {"type": "boolean"},
        "caffeine": {"type": "string"}
      }
    },
    "language": {
      "type": "string",
      "enum": ["en", "vi"],
      "description": "Output language preference"
    },
    "red_flags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Red flags for medical escalation"
    }
  },
  "required": ["profession", "symptoms"]
}
```

### Skill Output Schema

```json
{
  "type": "object",
  "properties": {
    "conclusion": {
      "type": "string",
      "enum": ["Healthy", "Improvement Plan", "Conditional", "Medical Referral Needed", "Inconclusive"]
    },
    "capev_scores": {
      "type": "object",
      "properties": {
        "overall_severity": {"type": "number", "minimum": 0, "maximum": 100},
        "roughness": {"type": "number", "minimum": 0, "maximum": 100},
        "breathiness": {"type": "number", "minimum": 0, "maximum": 100},
        "strain": {"type": "number", "minimum": 0, "maximum": 100},
        "pitch": {"type": "number", "minimum": 0, "maximum": 100},
        "loudness": {"type": "number", "minimum": 0, "maximum": 100},
        "projection": {"type": "number", "minimum": 0, "maximum": 100}
      }
    },
    "grbas_scores": {
      "type": "object",
      "properties": {
        "grade": {"type": "integer", "minimum": 0, "maximum": 3},
        "roughness": {"type": "integer", "minimum": 0, "maximum": 3},
        "breathiness": {"type": "integer", "minimum": 0, "maximum": 3},
        "asthenia": {"type": "integer", "minimum": 0, "maximum": 3},
        "strain": {"type": "integer", "minimum": 0, "maximum": 3}
      }
    },
    "exercise_protocol": {
      "type": "object",
      "properties": {
        "warm_up": {"type": "array"},
        "technique": {"type": "array"},
        "articulation": {"type": "array"},
        "cool_down": {"type": "array"}
      }
    },
    "risk_matrix": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "risk": {"type": "string"},
          "probability": {"type": "string"},
          "impact": {"type": "string"},
          "level": {"type": "string"},
          "mitigation": {"type": "string"}
        }
      }
    },
    "sources": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "citation": {"type": "string"},
          "tier": {"type": "integer", "minimum": 1, "maximum": 4},
          "year": {"type": "integer"},
          "relevance": {"type": "string"}
        }
      }
    },
    "disclosure": {
      "type": "string",
      "description": "Mandatory disclosure/limitations notice"
    },
    "language": {
      "type": "string",
      "enum": ["en", "vi"]
    },
    "gate_status": {
      "type": "object",
      "properties": {
        "U1": {"type": "boolean"},
        "U2": {"type": "boolean"},
        "U3": {"type": "boolean"},
        "U4": {"type": "boolean"},
        "U5": {"type": "boolean"},
        "U6": {"type": "boolean"},
        "G1": {"type": "boolean"},
        "G2": {"type": "boolean"},
        "G3": {"type": "boolean"},
        "G4": {"type": "boolean"}
      }
    }
  },
  "required": ["conclusion", "disclosure", "sources", "language"]
}
```

## Tool Definitions

### Available Tools

| Tool Name | Description | Handler Path | Timeout | Retry |
|-----------|-------------|--------------|---------|-------|
| `knowledge_query` | Query SECOND-KNOWLEDGE-BRAIN.md | `tools.knowledge_updater.query` | 10s | Yes |
| `evidence_fetch` | Fetch from external sources | `tools.knowledge_updater.fetch` | 30s | Yes |
| `capev_assess` | CAPE-V perceptual assessment | Internal | 5s | No |
| `grbas_assess` | GRBAS scaling assessment | Internal | 5s | No |
| `exercise_prescribe` | Generate exercise protocol | Internal | 10s | No |

### Tool Execution Schema

Each tool execution follows:

1. **Input Validation**: Against `input_schema`
2. **Handler Invocation**: With timeout enforcement
3. **Output Validation**: Against `output_schema`
4. **Error Handling**: Graceful fallback on failure

## Quality Gates

### Universal Gates (U1-U6)

Defined in `skills/_shared-conventions.md`:

| Gate | Check | Auto-Fix | Enforcement |
|------|-------|----------|-------------|
| U1 | ≥3 sources, ≥1 academic | Fetch from KB | Append before delivery |
| U2 | Disclosure before recs | Prepend disclosure | Block until present |
| U3 | Evidence tier labels | Annotate tiers | Tag each source |
| U4 | Language match | Translate | Re-run detection |
| U5 | Template compliance | Reformat | Check sections |
| U6 | Claims traceable | Flag unsupported | Mark or fix |

### Domain Gates (G1-G4)

| Gate | Check | Auto-Fix | Enforcement |
|------|-------|----------|-------------|
| G1 | Measurable voice dimensions | Add CAPE-V/GRBAS | Append assessment |
| G2 | Evidence-based exercises | Use library | Reference ASHA/VF |
| G3 | Red-flag referral | Add triage flags | Escalate urgency |
| G4 | Measurable articulation targets | Add drills | Specify targets |

### Gate Enforcement Logic

```python
def enforce_gate(gate_id: str, check: callable, auto_fix: callable, max_retries: int = 2) -> GateResult:
    for attempt in range(max_retries + 1):
        result = check()
        if result.passed:
            return GateResult(gate_id=gate_id, passed=True)

        if attempt < max_retries:
            auto_fix_result = auto_fix()
            if not auto_fix_result.successful:
                break

    return GateResult(gate_id=gate_id, passed=False, limitation="Max retries exceeded")
```

## Flexible Agent & Skill Architecture

### Architecture Pattern

This skill implements a **Sequential Sub-Skill Orchestration** pattern:

```
main.md (Harness)
    │
    ├── [Agent Chain]
    │   ├── sub-gather-requirements (Intake Agent)
    │   ├── sub-evidence-collector (Data Librarian Agent)
    │   ├── sub-core-analysis (Domain Expert Agent)
    │   ├── sub-knowledge-updater (Research Librarian Agent)
    │   └── sub-advisor (Senior Advisor Agent)
    │
    └── [Quality Gate System]
        ├── Gate Validators
        ├── Auto-Fix Handlers
        └── Enforcement Logic
```

### Agent Specialization

Each sub-skill is a **specialized agent** with:

- **Role & Persona**: Domain-specific identity
- **Workflow**: 3-step process (Receive → Execute → Emit)
- **Tools**: Domain-specific tool access
- **Quality Gate**: Local validation before handoff

### Alternative Architectures Supported

The modular design allows refactoring to:

1. **Chain-of-Thought Router**: Add routing agent that dispatches to specialized sub-agents based on query analysis
2. **Skill-Registry Pattern**: Dynamic skill loading from registry
3. **Parallel Execution**: Independent sub-skills (e.g., evidence collection + knowledge query) can run concurrently

## Hooks System

### Hook Types

| Event Type | Trigger | Payload |
|------------|---------|---------|
| `skill.pre_invoke` | Before skill execution | `{context, inputs}` |
| `skill.post_invoke` | After skill execution | `{context, outputs, execution_time}` |
| `tool.pre_execute` | Before tool execution | `{tool_name, inputs}` |
| `tool.post_execute` | After tool execution | `{tool_name, outputs, execution_time}` |
| `quality_gate.pre_check` | Before gate check | `{gate_id, context}` |
| `quality_gate.post_check` | After gate check | `{gate_id, result}` |
| `error.on_failure` | On any error | `{error, context}` |

### Hook Registration

```python
from scripts.hooks import hook, HookEventType

@hook(HookEventType.SKILL_PRE_INVOKE, "audit-log", priority=HookPriority.HIGH)
async def audit_skill_invocation(event: HookEvent):
    await write_audit_log(event.to_dict())
```

### State Synchronization

```python
from scripts.hooks import get_state_manager

state_mgr = get_state_manager()
await state_mgr.set("user_profession", "podcaster")
profession = await state_mgr.get("user_profession")
```

## Error Handling & Graceful Degradation

### Degradation Levels

| Level | Condition | Behavior |
|-------|-----------|----------|
| 0 | All sources reachable | Full analysis |
| 1 | Some sources fail | Use secondary, flag substitutions |
| 2 | Most live sources fail | KB only, flag historical |
| 3 | Input variable missing | Mark unavailable, no fabrication |
| 4 | All sources + KB fail | Emit UNAVAILABLE notice |

### Error Recovery

Each error type has defined recovery:

| Error | Detection | Recovery | Retry Limit |
|-------|-----------|----------|-------------|
| Source timeout | No response | Alternate source | 3 |
| Invalid input | Schema mismatch | Ask user | 2 |
| Missing input | Field absent | Proceed + flag | N/A |
| Stale reading | Old timestamp | Flag, refresh | 1 |
| KB miss | No matches | WebSearch + queue | 2 |
| Conflict | Mutually exclusive | Apply precedence | N/A |

## Bilingual Support

### Language Detection

Automatic detection based on:
- Vietnamese characters: àáảãạăâđèéêìíòóôơùúưý
- Domain-specific Vietnamese words
- User preference override

### Translation Tables

Full bilingual terminology in `GLOSSARY-vi.md` (140+ terms)

Report labels in `_shared-conventions.md` translation table

## Testing & Validation

### Test Scenarios

5 end-to-end scenarios in `tests/test-scenarios.md`:

1. **Standard**: Full inputs, English
2. **Minimal**: Minimum required inputs
3. **Comparison**: Multiple profession types
4. **Risk**: Red flags present
5. **Degraded**: Limited data availability

### Domain Tests

25 tests in `tests/test_domain.py`:

- CAPE-V calculation (5 tests)
- GRBAS scaling (5 tests)
- Exercise dosage (5 tests)
- Red-flag triage (5 tests)
- Conclusion logic (5 tests)

### Unit Tests

42 tests in `tools/test_knowledge_updater.py`:

- Hashing (5 tests)
- Scoring (5 tests)
- Config (5 tests)
- Rate limiting (8 tests)
- Retry logic (6 tests)
- API mocks (7 tests)
- Integration (6 tests)

## Performance & Token Optimization

### Context Window Management

- **Progressive Disclosure**: Load sub-skills on-demand
- **Reference Files**: Load only relevant sections
- **State Compression**: Store minimal state between skills

### RTK Integration

All shell commands prefixed with `rtk` for 60-90% token savings.

### Caching Strategy

- **Prompt Caching**: Enable for repeated contexts (configurable)
- **KB Caching**: In-memory cache for knowledge queries
- **Result Caching**: Cache gate results within session

## Deployment

### Local Development

```bash
# Install dependencies
make install

# Run tests
make test

# Lint
make lint

# Type check
make typecheck
```

### Docker

```bash
# Build image
docker build -t vstp .

# Run with cron
docker run --rm -v $(pwd):/app vstp

# News-only update
docker run --rm -v $(pwd):/app vstp --news-only
```

### Cron Schedule

```cron
# Weekly academic (Mondays 8:00 AM)
0 8 * * 1 python tools/knowledge_updater.py

# Daily news (Daily 7:00 AM)
0 7 * * * python tools/knowledge_updater.py --news-only
```

## Extension Points

### Adding New Sub-Skills

1. Create `skills/sub-<name>.md` with frontmatter
2. Implement workflow and tools
3. Add to `main.md` harness execution
4. Add quality gate if needed
5. Update tests

### Adding New Tools

1. Define tool in `scripts/tools.py` with `@tool` decorator
2. Implement handler function
3. Add to `SKILL.md` tool definitions
4. Add input/output schemas

### Adding New Quality Gates

1. Define gate check function
2. Define auto-fix function
3. Add to `_shared-conventions.md`
4. Update enforcement logic in `main.md`

## Maintenance

### Knowledge Base Updates

- **Academic**: Weekly via ArXiv/Semantic Scholar
- **News**: Daily via RSS feeds
- **Manual**: `python tools/knowledge_updater.py --keywords <terms>`

### Versioning

Semantic versioning:
- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes

### Changelog

Maintained in `CHANGELOG.md` with:
- Added features
- Changed behavior
- Fixed issues
- Removed/deprecated

## References

- `PROJECT-detail.md` — Full technical specification
- `PROJECT-DEVELOPMENT-PHASE-TRACKING.md` — Build roadmap
- `SECOND-KNOWLEDGE-BRAIN.md` — Living knowledge base
- `GLOSSARY-vi.md` — Bilingual terminology
- `skills/_shared-conventions.md` — Universal conventions
- `config/schemas.py` — JSON schemas
- `scripts/hooks.py` — Hooks system
- `scripts/tools.py` — Tools execution
