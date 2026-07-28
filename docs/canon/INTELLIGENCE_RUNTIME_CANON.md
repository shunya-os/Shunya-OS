# Intelligence Runtime Canon

> **Canonical Document · Phase D**
> **Status: CANONICAL — Implementation Specification**
> **Version: 1.0**

---

## 1. Purpose

This document defines the SHUNYA Intelligence Runtime — a business-agnostic cognitive architecture that operates independently of any specific LLM. The Intelligence Runtime is the canonical cognitive layer: it observes, reasons, plans, decides, reflects, learns, and computes confidence entirely through deterministic engines. External AI models are invoked only when deterministic computation reaches its confidence boundary and an escalation policy triggers.

The Intelligence Runtime implements the Cognitive OS architecture defined in 07_ai_canon.md as concrete, runnable code. Every engine defined here has a corresponding specification in the Cognitive OS Canon; this document provides the implementation contract.

---

## 2. Architecture Overview

### 2.1 The Eight Engines

| # | Engine | Cognitive OS Equivalent | Responsibility |
|---|--------|----------------------|---------------|
| 1 | **Perception** | Observer (§5) | Capture raw signals, validate, enrich, classify, produce Observations |
| 2 | **Context Assembly** | Memory + Knowledge (§6-7) | Assemble relevant context from Memory, Knowledge, Timeline, Evidence |
| 3 | **Reasoning** | Reasoner (§8) | Derive conclusions from evidence via 7 reasoning types |
| 4 | **Planning** | Planner (§9) | Generate action sequences from objectives |
| 5 | **Decision** | Executive (§10) | Manage decision lifecycle: propose → evaluate → approve → execute → monitor |
| 6 | **Reflection** | Evaluator (§11) | Evaluate outcomes, detect errors, suggest improvements |
| 7 | **Learning** | Learner (§12) | Extract patterns from outcomes, consolidate into Knowledge |
| 8 | **Confidence** | (cross-cutting) | Compute, combine, and track confidence scores across all engine outputs |

### 2.2 Architecture Layers

```
┌──────────────────────────────────────────────────────────────────┐
│                  INTELLIGENCE RUNTIME                              │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │               PERCEPTION LAYER                              │  │
│  │  ┌──────────────┐  ┌───────────────────┐  ┌─────────────┐  │  │
│  │  │  Perception   │  │  Context Assembly │  │  Confidence  │  │  │
│  │  │  Engine       │  │  Engine           │  │  Engine      │  │  │
│  │  └──────────────┘  └───────────────────┘  └─────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │               COGNITIVE LAYER                               │  │
│  │  ┌──────────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │  │
│  │  │  Reasoning   │  │ Planning │  │ Decision │  │Reflect │  │  │
│  │  │  Engine      │  │ Engine   │  │ Engine   │  │Engine  │  │  │
│  │  └──────────────┘  └──────────┘  └──────────┘  └────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              ▼                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │               LEARNING LAYER                                │  │
│  │  ┌─────────────────────────────────────────────┐           │  │
│  │  │             Learning Engine                   │           │  │
│  │  │  Consolidation → Pattern Detection → Update  │           │  │
│  │  └─────────────────────────────────────────────┘           │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │               CROSS-CUTTING                                 │  │
│  │  Confidence Engine (every engine uses it)                   │  │
│  │  Escalation Policy (deterministic → AI bridge)              │  │
│  │  Tool Orchestration (agent tool interfaces)                 │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.3 Integration with Universal Runtime (core/)

```
core/kernel/   core/identity/   core/relationship/   core/timeline/
core/event/    core/evidence/   core/runtime/         core/registry/
       │              │                  │                   │
       └──────────────┴──────────────────┴───────────────────┘
                              │
                              ▼
                    core/intelligence/  (Phase D)
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
  Perception Engine    Reasoning Engine      Learning Engine
  Context Assembly     Planning Engine       Confidence Engine
  Decision Engine      Reflection Engine
```

The Intelligence Runtime imports from `core/*` modules but never from `app/`. Strangler-fig isolation is preserved.

---

## 3. Engine Contract

Every Intelligence Engine implements this interface:

```python
class IntelligenceEngine:
    engine_id: str
    engine_type: str

    async def process(self, input: EngineInput) -> EngineOutput:
        """Process an input and return output. Always deterministic unless
        escalation is triggered, in which case process() calls escalate()."""

    def escalate(self, input: EngineInput) -> EscalationResult:
        """Bridge to external AI inference. Called when deterministic
        computation yields confidence below threshold."""

    def get_capabilities(self) -> list[str]:
        """Return list of capability strings."""

    def health_check(self) -> dict:
        """Return engine health status."""
```

### 3.1 Engine Input/Output Contract

```python
@dataclass
class EngineInput:
    input_type: str                    # e.g. "observation", "query", "action_result"
    payload: dict                      # structured input data
    context: dict | None = None        # assembled context (if available)
    trace_id: str = ""                 # correlation ID
    confidence_threshold: float = 0.7  # minimum confidence before escalation

@dataclass
class EngineOutput:
    output_type: str                   # e.g. "conclusion", "plan", "decision"
    payload: dict                      # structured output data
    confidence: float                  # computed confidence
    confidence_factors: dict           # breakdown of confidence computation
    deterministic: bool                # True = computed locally, False = AI-assisted
    trace_id: str
    escalation_used: bool = False
    processing_time_ms: float = 0.0
```

---

## 4. Deterministic vs AI-Assisted Boundaries

### 4.1 Boundary Rules

| Computation Type | Handled By | When |
|-----------------|-----------|------|
| **Identity resolution** | `core/identity/` | Always deterministic |
| **Relationship traversal** | `core/relationship/` | Always deterministic |
| **Timeline reconstruction** | `core/timeline/` | Always deterministic |
| **Evidence chain traversal** | `core/evidence/` | Always deterministic |
| **Event emission/routing** | `core/event/` | Always deterministic |
| **Lifecycle state validation** | UniversalObject | Always deterministic |
| **Permission checks** | UniversalObject ACL | Always deterministic |
| **Protocol compliance** | `core/registry/` | Always deterministic |
| **Pattern detection (stats)** | Learning Engine | Deterministic (stats-based) |
| **Path finding (graph)** | RelationshipEngine | Deterministic (BFS) |
| **Confidence computation** | Confidence Engine | Deterministic (formula-based) |
| **Context assembly** | Context Engine | Deterministic (query-based) |
| **Text classification** | Reasoning Engine | AI-assisted (LLM) |
| **Intent extraction** | Reasoning Engine | AI-assisted (LLM) |
| **Plan generation** | Planning Engine | AI-assisted (LLM) |
| **Open-ended reasoning** | Reasoning Engine | AI-assisted (LLM) |
| **Summarization** | Context Assembly | AI-assisted (LLM) |

### 4.2 Escalation Policy

```
Engine.process(input)
    │
    ├── 1. Compute deterministically
    │
    ├── 2. Compute confidence of result
    │
    ├── 3. If confidence >= threshold:
    │       └── Return result (deterministic=True)
    │
    └── 4. If confidence < threshold:
            ├── Call escalate(input)
            ├── AI inference provider processes
            ├── Result confidence re-computed
            └── Return result (deterministic=False, escalation_used=True)
```

### 4.3 Escalation Thresholds

| Engine | Default Threshold | Rationale |
|--------|-----------------|-----------|
| Perception | 0.85 | Observations must be reliable |
| Context Assembly | 0.75 | Context can tolerate some uncertainty |
| Reasoning | 0.70 | Reasoning often deals with ambiguity |
| Planning | 0.65 | Plans are iterative, can be refined |
| Decision | 0.80 | Decisions require high confidence |
| Reflection | 0.60 | Reflection is about improvement, safety |
| Learning | 0.90 | Learning requires high certainty |
| Confidence | 1.0 (always deterministic) | Formula-based |

---

## 5. Perception Engine

### 5.1 Purpose

Capture raw signals from the world (events, messages, state changes) and transform them into structured Observations consumable by the rest of the Intelligence Runtime.

### 5.2 Data Flow

```
Input ──► Perception Engine
              │
              ├── 1. Validate input schema
              ├── 2. Enrich with source metadata
              ├── 3. Classify input type
              ├── 4. Attach initial confidence
              ├── 5. Route to Context Assembly (via event bus)
              └── 6. Record Observation
```

### 5.3 Deterministic Work

- Input schema validation
- Source metadata extraction
- Input classification (by type rules)
- Priority assignment

### 5.4 AI-Assisted Work

- Free-text intent extraction (if input is unstructured)
- Entity recognition from text

---

## 6. Context Assembly Engine

### 6.1 Purpose

Assemble the complete context relevant to an input by querying all Universal Runtime data stores: Memory, Knowledge, Timeline, Evidence, Relationships.

### 6.2 Data Flow

```
Input + Observation ──► Context Assembly Engine
                           │
                           ├── 1. Query Memory for related records
                           ├── 2. Query Knowledge for facts
                           ├── 3. Query Timeline for recent events
                           ├── 4. Query Evidence for supporting data
                           ├── 5. Query Relationships for graph context
                           ├── 6. Merge into unified Context
                           └── 7. Return Context → Reasoning Engine
```

### 6.3 Deterministic Work

- All data store queries (Memory, Knowledge, Timeline, Evidence, Relationship)
- Context merging and deduplication
- Relevance scoring
- Recency filtering

### 6.4 AI-Assisted Work

- Summarization of large context sets
- Relevance ranking of unstructured data

---

## 7. Reasoning Engine

### 7.1 Purpose

Derive conclusions from evidence, observations, and context using 7 reasoning types. The Reasoning Engine is the inference core of the Intelligence Runtime.

### 7.2 Reasoning Types

| Type | Deterministic? | Method |
|------|---------------|--------|
| Deductive | ✓ Always | Rule-based inference engine |
| Inductive | ✓ Pattern-based | Statistical pattern matching |
| Abductive | ✗ AI-assisted | Best explanation from LLM |
| Analogical | ✓ Rule-based | Similarity scoring |
| Causal | ✓ Rule-based | Evidence chain traversal |
| Counterfactual | ✗ AI-assisted | LLM simulation |
| Probabilistic | ✓ Formula-based | Confidence-weighted aggregation |

### 7.3 Data Flow

```
Context ──► Reasoning Engine
               │
               ├── 1. Apply deductive rules (deterministic)
               ├── 2. Check inductive patterns (deterministic)
               ├── 3. If confidence >= threshold: return
               ├── 4. Escalate for abductive/counterfactual (AI)
               └── 5. Combine results, compute final confidence
```

---

## 8. Planning Engine

### 8.1 Purpose

Transform objectives into actionable plans — sequences of steps with dependencies, resources, risks, and success criteria.

### 8.2 Plan Structure

```python
@dataclass
class Plan:
    objective: str
    steps: list[PlanStep]
    dependencies: dict[str, list[str]]  # step_id -> [dependency_step_ids]
    estimated_duration: str
    risks: list[Risk]
    success_criteria: list[str]
    confidence: float
```

### 8.3 Deterministic Work

- Dependency graph validation (acyclic check)
- Step ordering (topological sort)
- Resource conflict detection
- Risk classification by type

### 8.4 AI-Assisted Work

- Step generation from objective
- Duration estimation
- Risk identification

---

## 9. Decision Engine

### 9.1 Purpose

Manage the complete decision lifecycle: from candidate decision through evaluation, approval, execution, and outcome capture.

### 9.2 Decision Lifecycle

```
CANDIDATE ──► POLICY_EVALUATION ──► UNDER_REVIEW ──► APPROVED
    │               │                    │               │
    ▼               ▼                    ▼               ▼
 REJECTED       BLOCKED              SENT_BACK       EXECUTING
                                                       │
                                                       ▼
                                                  COMPLETED
                                                       │
                                                       ▼
                                                  FAILED
```

### 9.3 Deterministic Work

- Policy rule evaluation
- Valid transition enforcement
- Permission checking
- Evidence sufficiency validation
- Outcome measurement

### 9.4 AI-Assisted Work

- Decision option generation
- Trade-off analysis
- Risk assessment text

---

## 10. Reflection Engine

### 10.1 Purpose

Evaluate outcomes of decisions and actions, detect errors, assess quality, and generate improvement signals for the Learning Engine.

### 10.2 Data Flow

```
Outcome ──► Reflection Engine
               │
               ├── 1. Compare outcome vs expected
               ├── 2. Detect anomalies
               ├── 3. Compute success score
               ├── 4. Identify improvement signals
               ├── 5. Log reflection record
               └── 6. Route signals → Learning Engine
```

### 10.3 Deterministic Work

- Outcome vs expected comparison
- Success score computation
- Anomaly detection (threshold-based)
- Improvement signal categorization

---

## 11. Learning Engine

### 11.1 Purpose

Extract patterns from outcomes and reflections, consolidate them into Knowledge, and improve future reasoning.

### 11.2 Learning Types

| Type | Method | Description |
|------|--------|-------------|
| Pattern detection | Statistical | Identify recurring patterns in outcomes |
| Confidence adjustment | Formula-based | Adjust confidence weights based on accuracy |
| Knowledge consolidation | Deduplication | Merge confirmed patterns into Knowledge |
| Knowledge decay | Time-based | Reduce weight of stale knowledge |

### 11.3 Deterministic Work

- All learning is deterministic

---

## 12. Confidence Engine

### 12.1 Purpose

Compute, combine, and track confidence scores across all engine outputs. The Confidence Engine is the single source of truth for confidence in the Intelligence Runtime.

### 12.2 Confidence Computation

```
Confidence = f(source_reliability, evidence_strength, consistency, recency, certainty)

Where:
  source_reliability ∈ [0, 1]  — How reliable is the data source?
  evidence_strength  ∈ [0, 1]  — How strong is the supporting evidence?
  consistency        ∈ [0, 1]  — How consistent with existing knowledge?
  recency            ∈ [0, 1]  — How recent is the information?
  certainty          ∈ [0, 1]  — How certain is the inference method?

Combined = W_s * source_reliability + W_e * evidence_strength
           + W_c * consistency + W_r * recency + W_t * certainty

Weights: W_s=0.25, W_e=0.30, W_c=0.20, W_r=0.10, W_t=0.15
```

---

## 13. Escalation Policy

### 13.1 When to Escalate

The escalation policy is a deterministic gate that decides when to invoke an external AI model. It is triggered when:

1. **Confidence below threshold** — deterministic computation yields confidence < engine threshold
2. **Unrecognized input type** — input cannot be classified by Perception
3. **Open-ended request** — input type is flagged as requiring AI
4. **Human request for AI** — user explicitly requests AI assistance

### 13.2 Escalation Flow

```
Deterministic Processing ──► Confidence Check
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              Confidence >= Threshold     Confidence < Threshold
                    │                           │
                    ▼                           ▼
            Return Result              Escalation Bridge
                                              │
                                              ▼
                                      AI Inference Provider
                                        (LLM, symbolic, etc.)
                                              │
                                              ▼
                                      Post-process Result
                                              │
                                              ▼
                                      Recompute Confidence
                                              │
                                              ▼
                                      Return Result
```

---

## 14. Tool Orchestration

### 14.1 Tool Interface

```python
@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    output_schema: dict
    deterministic: bool  # True = no AI needed for this tool

    async def execute(self, params: dict, context: dict) -> dict:
        ...
```

### 14.2 Registered Tools

| Tool | Engine | Deterministic |
|------|--------|---------------|
| `resolve_identity` | Identity Engine | Yes |
| `find_relationship_path` | Relationship Engine | Yes |
| `reconstruct_timeline` | Timeline Engine | Yes |
| `get_evidence_chain` | Evidence Engine | Yes |
| `check_protocol_compliance` | Object Registry | Yes |
| `get_confidence_score` | Confidence Engine | Yes |
| `emit_event` | Event Engine | Yes |
| `validate_lifecycle` | UniversalObject | Yes |
| `reason_deductive` | Reasoning Engine | Yes |
| `reason_abductive` | Reasoning Engine | No (AI) |
| `generate_plan` | Planning Engine | No (AI) |
| `classify_text` | Reasoning Engine | No (AI) |

---

## 15. Multi-Agent Coordination

### 15.1 Agent Definition

```python
@dataclass
class Agent:
    agent_id: str
    role: str                    # "perception", "reasoning", "planning", "execution"
    engines: list[str]           # which intelligence engines this agent controls
    allowed_tools: list[str]     # which tools this agent may call
    governance_scope: str        # which policies apply
```

### 15.2 Coordination Protocol

Agents communicate via the Event Engine (core/event/):

```
Agent A ──emit(event)──► Event Engine ──route(event)──► Agent B
    │                                                       │
    │  ┌──────────────────────────────────────────────┐    │
    └──┤ AgentMessage {                              │◄───┘
       │   source_agent: str                         │
       │   target_agent: str                         │
       │   message_type: str  # request | response   │
       │   payload: dict                             │
       │   trace_id: str                             │
       │   confidence: float                         │
       │   requires_governance: bool                 │
       │ }                                           │
       └──────────────────────────────────────────────┘
```

---

## 16. Integration Map

| Intelligence Engine | Consumes From (core/) | Produces For |
|-------------------|----------------------|-------------|
| Perception | `core/event/`, UniversalObject | Observations |
| Context Assembly | `core/identity/`, `core/relationship/`, `core/timeline/`, `core/evidence/` | Context objects |
| Reasoning | Context, Knowledge, Evidence | Conclusions, options |
| Planning | Reasoning outputs | Plans |
| Decision | Plans, Policies | Decisions, Commitments |
| Reflection | Outcomes, Timelines | Reflection records |
| Learning | Reflection records | Pattern updates |
| Confidence | All engines | Confidence scores |

---

## 17. Relationship to Canonical Documents

| Document | Relationship |
|----------|-------------|
| **00_universal_ontology.md** | Implements Event→Observation, Decision→Action→Outcome pipeline |
| **03_business_canon.md** | All business objects are processed by these engines |
| **04_universal_object_protocol.md** | Engines use the AIContext section of every object |
| **05_runtime_canon.md** | Engines run as runtime-managed components |
| **07_ai_canon.md** | **Implements** the Cognitive OS architecture in code |
| **09_repository_canon.md** | Engines live in `core/intelligence/` |
| **11_engineering_canon.md** | All engines pass protocol compliance checks |
