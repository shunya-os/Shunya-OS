# Universal Perception Architecture

**Phase 11 — SHUNYA OS**
**Classification: Implementation Architecture**
**Status: PROPOSED**
**Version: 1.0**

---

## Preamble

### Authority

This document defines the implementation architecture for Universal Perception. It defines how SHUNYA observes reality. It does NOT redefine constitutional concepts — it references them.

### First principles

1. **Reality enters SHUNYA only through perception.** Everything else derives from perception. Perception is the beginning of intelligence.
2. **Perception is passive.** SHUNYA does not invent reality. It receives signals from reality and interprets them.
3. **Perception is continuous.** SHUNYA never stops observing. Observation is not a discrete operation — it is a perpetual state.
4. **Perception is universal.** The same architecture observes conversations, documents, calendar events, emails, system events, and any future source — without domain-specific logic.
5. **Perception is the first stage of the dependency chain.** Everything SHUNYA knows begins here.

### Dependency chain position

```
REALITY
  ↓
PERCEPTION (this architecture)
  ↓
Observation
  ↓
Evidence
  ↓
Object
  ↓
Relationship
  ↓
Knowledge
  ↓
Reasoning
  ↓
Prediction
  ↓
Execution
  ↓
Workspace
```

This architecture defines the first two stages: Reality → Perception → Observation.

### Constitutional sources

| Document | What it provides | How this architecture references it |
|----------|-----------------|--------------------------------------|
| UNIVERSAL_ONTOLOGY.md | Observation (§6), Evidence (§7), Event (§8), Identity (§3), Object (§1) | Defines the constitutional types that perception produces |
| COGNITIVE_WORKSPACE_RUNTIME.md | Attention Engine (§2), Event Bus (§9), Memory (§5) | Defines how perception feeds cognition |
| ADAPTIVE_INTELLIGENCE_RUNTIME.md | Confidence Engine (§2), Learning Engine (§1), Calibration (§6) | Defines how perception confidence evolves |
| UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md | Evidence Graph (§4), Temporal Graph (§5), Events (§10) | Defines how perception data is stored |

---

## 1. Perception Model

### 1.1 Ontology mapping

The Perception Model derives from the constitutional definitions in UNIVERSAL_ONTOLOGY.md §6 (Observation) and §7 (Evidence).

| Ontology concept | Perception implementation | Relationship |
|------------------|--------------------------|--------------|
| Observation (§6) | Perceived Signal | An observation is a signal that has been captured and classified |
| Evidence (§7) | Constructed Evidence | Evidence is a verified observation placed in context |
| Event (§8) | Perception Event | A change in perception state (new source, lost signal, etc.) |
| Identity (§3) | Resolved Identity | An observation is mapped to an identity during perception |
| Object (§1) | Detected Object | The real-world entity the observation refers to |

### 1.2 Perception primitives

| Primitive | Definition | Constitutional source |
|-----------|------------|----------------------|
| **Observation** | A raw signal that has been captured, validated, and classified | Ontology §6 |
| **Signal** | A raw data point from reality. Pre-observation. Pre-classification. | Ontology §6 (Observation hierarchy) |
| **Input** | A container for one or more signals from a single source interaction | — |
| **Source** | The origin of a signal. A person, system, file, or event producer. | Ontology §7 (Evidence types) |
| **Channel** | The medium through which the signal arrives. Email, API, webhook, file, voice. | — |
| **Sensor** | An abstraction that connects a Source to a Channel. A single Sensor handles one source-channel pair. | — |
| **Noise** | A signal that cannot be classified. Low confidence, incomplete, or contradictory. | — |
| **Confidence** | The reliability of an observation. Based on source trust, channel reliability, and signal clarity. | Adaptive §2 |
| **Freshness** | How recent the observation is. Used for decay and prioritisation. | Ontology §7 (Recency factor) |
| **Origin** | The provenance of the observation. How, when, and through which path it entered. | Ontology §1.2 (Provenance) |

### 1.3 Perception chain

```
Reality (external world)
  ↓
Signal (raw data point)
  ↓
Capture (sensor receives signal)
  ↓
Validation (signal is well-formed)
  ↓
Classification (signal type determined)
  ↓
Deduplication (signal is unique)
  ↓
Normalisation (signal is canonical)
  ↓
Identity Resolution (signal maps to object)
  ↓
Confidence Calculation (reliability scored)
  ↓
Evidence Generation (verified observation)
  ↓
Knowledge Graph Update (observation stored)
```

---

## 2. Perception Sources

### 2.1 Universal source types

Every source type maps to one or more constitutional types. Sources are defined by what they produce, not by their technology.

| Source | Produces | Constitutional type | Example signal |
|--------|----------|---------------------|----------------|
| **Conversation** | Messages, intents, commitments | Event::Communication, Commitment | "Send the proposal to Rahul" |
| **Documents** | Text, structure, metadata | Entity::Document, Knowledge | A PDF, a spreadsheet, a contract |
| **Calendar** | Events, meetings, deadlines | Entity::Meeting, Commitment::Deadline | Calendar invite, due date |
| **Email** | Messages, threads, attachments | Event::Communication, Entity::Document | Email thread, PDF attachment |
| **Voice** | Speech, tone, intent | Event::Communication | Voicemail, phone call transcript |
| **Video** | Visual content, subtitles, metadata | Entity::Document | Meeting recording, presentation |
| **Images** | Visual content, metadata | Entity::Document | Photo, screenshot, diagram |
| **Structured systems** | Records, transactions, status | Event::Creation, Event::Modification | API response, database row, webhook payload |
| **Unstructured systems** | Raw text, files, logs | Observation | Log line, chat message, forum post |
| **Manual input** | Direct founder observation | Event::Creation | Founder types "Rahul is the CEO" |
| **Future connectors** | Any future source | Observation | Defined by adapter contract |

### 2.2 Source independence

Every source operates independently. A failure in one source does not affect others. Sources are:

- **Hot-pluggable** — new sources can be added without modifying existing sources
- **Self-describing** — each source provides its own metadata, type, and confidence baseline
- **Rate-limited** — each source has a configurable maximum observation rate
- **Observable** — each source reports its health, latency, and error rate

### 2.3 Source confidence baseline

| Source type | Baseline confidence | Reasoning |
|-------------|---------------------|-----------|
| Conversation | 0.8 | Direct human communication |
| Documents | 0.7 | Asynchronous, may be outdated |
| Calendar | 0.9 | Structured, intentional |
| Email | 0.7 | Asynchronous, may be misdirected |
| Voice | 0.6 | Prone to transcription error |
| Video | 0.6 | Prone to interpretation error |
| Images | 0.5 | Prone to misinterpretation |
| Structured systems | 0.9 | Machine-verified |
| Unstructured systems | 0.4 | Noisy, unverified |
| Manual input | 1.0 | Founder-confirmed |

---

## 3. Observation Pipeline

### 3.1 Purpose

The Observation Pipeline transforms raw signals into structured observations ready for the Evidence Graph and Knowledge Graph.

### 3.2 Pipeline stages

```
Signal arrives from source
  ↓
(1) CAPTURE
  Raw signal received, timestamped, source tagged
  ↓
(2) VALIDATION
  Signal is well-formed, complete, and from a known source
  ↓
(3) CLASSIFICATION
  Signal type determined (message, event, document, etc.)
  ↓
(4) DEDUPLICATION
  Signal is compared against recent observations. Duplicates discarded.
  ↓
(5) NORMALISATION
  Signal is transformed to canonical format (timestamps, identifiers, text)
  ↓
(6) IDENTITY RESOLUTION
  Entities in the signal are resolved to known identities
  ↓
(7) CONFIDENCE CALCULATION
  Confidence score computed from source, channel, and signal quality
  ↓
(8) EVIDENCE GENERATION
  Observation promoted to Evidence with full provenance
  ↓
(9) KNOWLEDGE GRAPH UPDATE
  Evidence added to Evidence Graph, Knowledge Graph updated
  ↓
Structured observation ready for consumption
```

### 3.3 Stage definitions

| Stage | Input | Output | Failure behaviour |
|-------|-------|--------|-------------------|
| **CAPTURE** | Raw signal | Tagged signal | Log source error, retry |
| **VALIDATION** | Tagged signal | Validated signal | Reject malformed signal, log validation failure |
| **CLASSIFICATION** | Validated signal | Classified signal | Default to Observation type, flag for review |
| **DEDUPLICATION** | Classified signal | Unique signal | Discard duplicate, increment duplicate counter |
| **NORMALISATION** | Unique signal | Canonical signal | Retain original as fallback |
| **IDENTITY RESOLUTION** | Canonical signal + identities | Resolved signal | Flag unresolved identity, proceed with placeholder |
| **CONFIDENCE** | Resolved signal + source | Confidence-scored observation | Default to source baseline |
| **EVIDENCE** | Confidence-scored observation | Evidence object | Retain as observation if evidence fails |
| **KG UPDATE** | Evidence object | Graph update | Queue for retry, log failure |

### 3.4 Pipeline invariants

1. Every observation has a provenance chain (source → capture → classification → normalisation).
2. Every observation has a confidence score.
3. Every observation is timestamped at capture time.
4. Duplicate observations are discarded, not stored.
5. The pipeline never blocks on a single source — each source has an independent pipeline.

---

## 4. Reality Detection

### 4.1 Purpose

Reality Detection determines what change an observation represents. It answers: "What just happened in reality?"

### 4.2 Detection types

| Change type | Definition | Detection method | Action |
|-------------|------------|------------------|--------|
| **New object** | An observation that does not match any existing Object | Identity resolution returns no match | Create new Object in Knowledge Graph |
| **Updated object** | An observation that matches an existing Object with new information | Identity resolution returns match, attributes differ | Update Object attributes, add new evidence |
| **Deleted object** | An observation that indicates an Object no longer exists | Explicit deletion signal, or prolonged absence of updates | Mark Object as ARCHIVED, preserve evidence |
| **Conflicting object** | Two observations of the same Object with contradictory information | Identity resolution returns same Object, attributes contradict | Flag for conflict resolution (§9) |
| **Duplicate object** | Two observations that represent the same Entity but have different identities | Identity resolution finds strong match between two different Identities | Flag for merge (§3.5 of Ontology) |
| **Unknown object** | An observation that cannot be classified into any known type | Classification fails or returns UNKNOWN | Store as Observation, flag for manual classification |

### 4.3 Detection pipeline

```
Observation arrives
  ↓
Attempt identity resolution
  ↓
If identity found → check if observation adds new information
  │   Yes → UPDATED object
  │   No → DUPLICATE observation, discard
  │
If identity not found → check if observation is a deletion signal
  │   Yes → DELETED object
  │   No → NEW object
  │
If classification failed → UNKNOWN object
  │
If attributes contradict known information → CONFLICTING object
```

### 4.4 Detection invariants

1. Every observation produces exactly one detection result.
2. Detection results are deterministic — same observation + same graph state → same result.
3. Detection NEVER creates a false Object. If identity resolution is uncertain, the observation is held in a pending state.

---

## 5. Continuous Observation

### 5.1 Purpose

SHUNYA never stops observing. Continuous Observation defines how perception operates across time.

### 5.2 Observation modes

| Mode | Trigger | Frequency | Use case |
|------|---------|-----------|----------|
| **Event-driven** | External event (webhook, API call, message) | Real-time | Conversations, emails, system events |
| **Polling** | Scheduled check of a source | Configurable interval (30s – 24h) | Calendar, file systems, external APIs |
| **Scheduled** | Fixed time schedule | Cron-like | Daily reports, weekly summaries |
| **Manual** | Founder explicitly triggers observation | On demand | Document upload, manual input |
| **Streaming** | Continuous data flow | Real-time | Voice, video, real-time feeds |
| **Incremental** | Polling that only checks for changes since last check | Each poll | File systems, databases |

### 5.3 Observation frequency

| Source type | Default mode | Default frequency | Performance consideration |
|-------------|-------------|-------------------|--------------------------|
| Conversation | Event-driven | Real-time | Low volume, high value |
| Documents | Event-driven + Polling | Every 60s (polling) | Variable volume |
| Calendar | Polling | Every 300s | Low volume |
| Email | Event-driven | Real-time | Medium volume |
| Voice | Streaming | Real-time | High volume, requires filtering |
| Video | Event-driven | On upload | Low volume |
| Images | Event-driven | On upload | Low volume |
| Structured systems | Event-driven | Real-time | Variable volume |
| Unstructured systems | Polling | Every 600s | High volume, noise |
| Manual input | Manual | On demand | Very low volume |

### 5.4 Observation decay

Observations that are not promoted to Evidence within a configurable window are archived:

| Observation type | Max age before archive | Promotion path |
|-----------------|----------------------|----------------|
| High confidence (≥ 0.8) | 24 hours | Immediate evidence |
| Medium confidence (0.5 – 0.79) | 7 days | Requires verification |
| Low confidence (< 0.5) | 30 days | Requires additional signals |
| Unclassified | 7 days | Requires manual classification |
| Contradictory | 30 days | Requires conflict resolution |

---

## 6. Attention Trigger Engine

### 6.1 Purpose

The Attention Trigger Engine determines which observations deserve the founder's attention. It is the perception-level analogue of the Cognitive Runtime's Attention Engine (CWR §2) — but operates at the signal level, before cognition.

### 6.2 Trigger factors

| Factor | Definition | Weight | Source |
|--------|------------|--------|--------|
| **Priority** | The source-defined importance of the observation | 0.3 | Source metadata |
| **Urgency** | The time-sensitivity of the observation | 0.25 | Temporal analysis |
| **Importance** | The relevance of the observation to the current workspace context | 0.2 | Context Engine |
| **Novelty** | How different this observation is from previous observations | 0.15 | Pattern matching |
| **Risk** | The risk level detected in the observation | 0.1 | Risk analysis |

### 6.3 Trigger formula

```
trigger_score = (priority × 0.3) + (urgency × 0.25) + (importance × 0.2) + (novelty × 0.15) + (risk × 0.1)
```

### 6.4 Trigger thresholds

| Score | Behaviour |
|-------|-----------|
| ≥ 0.8 | Immediate attention — surface to founder, interrupt current focus |
| 0.5 – 0.79 | Moderate attention — add to attention queue, do not interrupt |
| 0.2 – 0.49 | Low attention — log for periodic review |
| < 0.2 | Ignore — archive without surfacing |

### 6.5 Attention queue

Observations that score ≥ 0.5 are added to the Attention Queue. The queue is:

- **Ordered by trigger_score** (highest first)
- **Capped at 100 items** (oldest evicted)
- **Consumed by the Attention Engine** (CWR §2) when the founder is ready
- **Persisted to Relationship Memory** (Ontology §17) for pattern analysis

### 6.6 Trigger invariants

1. Every observation is scored for attention.
2. The trigger formula is deterministic — same observation → same trigger score.
3. The trigger formula is configurable — factor weights can be adjusted by policy.
4. Observations below the ignore threshold are archived, not deleted.

---

## 7. Context Extraction

### 7.1 Purpose

Every observation inherits context from the Cognitive Runtime and Knowledge Graph. Context Extraction ensures that observations are understood in their full context before they are consumed.

### 7.2 Context inheritance

| Context | Inherited from | Inherited by observation |
|---------|----------------|--------------------------|
| **Identity** | The resolved identity of entities in the observation | All subsequent processing |
| **Timeline** | The timeline of the resolved identities | Temporal ordering, conflict detection |
| **Relationships** | The 1-hop relationships of resolved identities | Relevance scoring, priority calculation |
| **Workspace** | The current workspace context (if observation is founder-initiated) | Priority, importance |
| **Execution** | Any active execution related to the observation | Execution context for governance |
| **Memory** | Working Memory and Session Memory | Deduplication, novelty detection |
| **Policy** | Applicable policies from the Policy hierarchy | Permission checks, governance routing |
| **Knowledge** | Existing knowledge about the resolved identities | Confidence adjustment, contradiction detection |

### 7.3 Context resolution

```
Observation arrives
  ↓
Resolve identities in observation
  ↓
Load timeline for each resolved identity
  ↓
Load 1-hop relationships
  ↓
Load applicable policies
  ↓
Load relevant knowledge
  ↓
Check current workspace context
  ↓
Check active executions
  ↓
Attach resolved context to observation
  ↓
Observation + context ready for processing
```

### 7.4 Context invariants

1. Context is resolved at observation time, not at consumption time.
2. Context is immutable once attached to the observation.
3. If context cannot be fully resolved, the observation proceeds with partial context.
4. Context resolution is bounded (max 10 identities, max 2-hop depth).

---

## 8. Evidence Construction

### 8.1 Purpose

Evidence Construction is the process by which observations become evidence. No shortcuts are permitted. Every piece of evidence must pass through the constitutional chain: Observation → Evidence → Knowledge → Prediction → Execution.

### 8.2 Construction pipeline

```
Observation (validated, classified, resolved)
  ↓
(1) VERIFICATION
  Cross-check observation against existing knowledge
  ↓
(2) CONTEXTUALISATION
  Place observation in context of related evidence
  ↓
(3) CONFIDENCE ASSIGNMENT
  Apply confidence formula from source, channel, verification
  ↓
(4) EVIDENCE CREATION
  Create Evidence object with full provenance
  ↓
(5) KNOWLEDGE INTEGRATION
  Update Knowledge Graph with new evidence
  ↓
(6) RELATIONSHIP UPDATE
  Create or update relationships based on evidence
  ↓
Evidence ready for consumption
```

### 8.3 Evidence structure

```
Evidence {
  evidence_id: Identity
  source: SourceRef
  observation: ObservationRef
  confidence: float  (0.0 – 1.0)
  context: EvidenceContext
  provenance: ProvenanceChain
  created_at: Timestamp
  verification: VerificationResult
}
```

### 8.4 Evidence invariants

1. Every evidence object references exactly one observation.
2. Every evidence object has a confidence score.
3. Every evidence object has a complete provenance chain.
4. Evidence is immutable once created (per Ontology O-03).
5. Evidence cannot be created without passing through the Observation Pipeline.

---

## 9. Conflict Resolution

### 9.1 Purpose

Conflict Resolution handles contradictory observations, multiple sources, stale information, uncertain information, and missing information.

### 9.2 Conflict types

| Conflict type | Definition | Detection | Resolution |
|---------------|------------|-----------|------------|
| **Contradictory observations** | Two observations of the same Object with opposite attributes | Both observations exist, attributes differ beyond tolerance | Present both with confidence scores; do not resolve automatically |
| **Multiple sources** | The same information from different sources with different confidence | Identity resolution returns same Object, same attributes | Accept highest-confidence source; store all as evidence |
| **Stale information** | An observation that contradicts recent updates | Timestamp of observation is older than existing evidence | Discard stale observation; log for audit |
| **Uncertain information** | An observation with low confidence that cannot be verified | Confidence < 0.5 | Store as observation, do not promote to evidence |
| **Missing information** | An expected observation that has not arrived | Expected source has not produced a signal within expected window | Log as missing; flag for investigation |

### 9.3 Resolution hierarchy

```
1. Temporal precedence: newer observations override older ones (within same confidence band)
2. Confidence precedence: higher-confidence observations override lower (within same time window)
3. Source precedence: structured > conversational > document > unstructured (at same confidence)
4. Founder precedence: manual input overrides all other sources
5. Escalation: if none of the above resolves, present to founder
```

### 9.4 Conflict invariants

1. Conflicting evidence is preserved (per Ontology §7.4 — conflicting evidence is preserved).
2. Automatic resolution follows the resolution hierarchy exactly.
3. Conflicts that reach escalation are presented to the founder with both evidence chains.
4. The founder's resolution is recorded as a governance action.

---

## 10. Confidence Model

### 10.1 Purpose

Perception-level confidence feeds into the constitutional Confidence Engine (Adaptive §2). This section defines the perception-specific confidence calculations.

### 10.2 Confidence layers

| Layer | Definition | Formula | Range |
|-------|------------|---------|-------|
| **Observation confidence** | Confidence in a single observation | Source baseline × channel reliability × signal clarity | 0.0 – 1.0 |
| **Source confidence** | Confidence in a source's reliability | Historical accuracy of the source | 0.0 – 1.0 |
| **Evidence confidence** | Confidence in evidence constructed from observations | Observation confidence × verification factor | 0.0 – 1.0 |
| **Knowledge confidence** | Confidence in knowledge derived from evidence | Per Adaptive §2 (Confidence Engine) | 0.0 – 1.0 |
| **Prediction confidence** | Confidence in a prediction based on knowledge | Per Adaptive §2.2 | 0.0 – 1.0 |
| **Execution confidence** | Confidence that an execution will succeed | Per Adaptive §2.2 | 0.0 – 1.0 |

### 10.3 Observation confidence formula

```
observation_confidence = source_baseline × channel_reliability × signal_clarity
```

| Factor | Source | Range |
|--------|--------|-------|
| **Source baseline** | §2.3 (Source confidence baseline) | 0.4 – 1.0 |
| **Channel reliability** | Channel type (e.g., direct API: 0.95, webhook: 0.9, email: 0.7, voice: 0.6) | 0.5 – 0.95 |
| **Signal clarity** | Completeness and coherence of the signal | 0.0 – 1.0 |

### 10.4 Confidence promotion

Observation confidence is promoted to evidence confidence when:

1. The observation is verified against existing knowledge (confidence += 0.05)
2. The observation is independently confirmed by a second source (confidence += 0.1)
3. The observation is explicitly confirmed by the founder (confidence = 1.0)

---

## 11. Perception Event Bus

### 11.1 Purpose

The Perception Event Bus is a domain-specific event bus for perception events. It feeds into the Cognitive Event Bus (CWR §9) and the Knowledge Graph Events (KG §10).

### 11.2 Canonical perception events

| Event | Emitter | Payload | Consumers |
|-------|---------|---------|-----------|
| `ObservationReceived` | Source Sensor | signal_id, source, channel, timestamp | Observation Pipeline, Metrics |
| `ObservationValidated` | Observation Pipeline | observation_id, validation_result, confidence | Evidence Engine, Attention Trigger |
| `ObservationRejected` | Observation Pipeline | observation_id, rejection_reason | Metrics, Source Health |
| `ObjectDetected` | Reality Detection | object_id, detection_type (NEW/UPDATED/DELETED/CONFLICT) | Knowledge Graph, Attention Engine |
| `RelationshipDetected` | Observation Pipeline | source_id, target_id, relationship_type, confidence | Relationship Graph, Memory |
| `EvidenceCreated` | Evidence Construction | evidence_id, observation_id, confidence | Knowledge Graph, Confidence Engine |
| `KnowledgeUpdated` | Knowledge Graph | object_id, changed_attributes | Attention Engine, Projection Engine |
| `AttentionTriggered` | Attention Trigger Engine | observation_id, trigger_score, factor_breakdown | Workspace, Cognitive Runtime |
| `ConflictDetected` | Conflict Resolution | observation_id, conflicting_evidence_id, conflict_type | Governance, Founder |
| `ObservationArchived` | Continuous Observation | observation_id, archive_reason | Memory, Metrics |

### 11.3 Event propagation

All perception events are:

1. Published to the Cognitive Event Bus (CWR §9)
2. Stored in the Knowledge Graph as Event nodes (KG §2)
3. Consumed by the Workspace Projection Engine for real-time updates
4. Used by the Adaptive Runtime for calibration and learning

---

## 12. Workspace Projection

### 12.1 Purpose

The Founder Workspace receives perception projections. These are structured views of perception state — never raw signal data.

### 12.2 Projection types

| Projection | Content | Source | Consumer |
|------------|---------|--------|----------|
| **Recent Observations** | Last N observations relevant to current context | Observation Pipeline | Workspace Intelligence Panel |
| **Reality Changes** | Recent object creations, updates, deletions | Reality Detection | Workspace Center panel |
| **Attention Queue** | Observations awaiting founder attention | Attention Trigger Engine | Workspace Left Panel |
| **Conflicts** | Unresolved contradictory observations | Conflict Resolution | Workspace Intelligence Panel |
| **Evidence** | Evidence constructed from recent observations | Evidence Construction | Workspace Evidence panel |
| **Signals** | Raw signal volume, source health, pipeline latency | Observation Pipeline | Workspace Intelligence Panel |
| **Confidence** | Confidence distribution across perception sources | Confidence Model | Workspace Intelligence Panel |
| **Timeline** | Chronological perception events | Perception Event Bus | Workspace Timeline component |

### 12.3 Projection rules

1. Projections are read-only — the workspace never writes to perception state.
2. Projections are filtered by workspace context — only observations relevant to the current focus are shown.
3. Projections are assembled by the Workspace Projection Engine (CWR §3).

---

## 13. Scalability

### 13.1 Assumptions

The architecture supports: continuous perception, millions of observations, high-frequency updates, distributed sources, and incremental graph updates.

### 13.2 Scaling strategies

| Strategy | Applied to | Description |
|----------|------------|-------------|
| **Independent pipelines** | Observation Pipeline | Each source has its own pipeline instance. Sources do not share pipelines. |
| **Stateless capture** | All sensors | Sensors are stateless. Captured signals are written to a queue, not held in memory. |
| **Batched deduplication** | Deduplication stage | Deduplication uses a sliding window (last N observations), not a full history scan. |
| **Temporal observation expiry** | Observation storage | Observations below confidence threshold are archived after 30 days. |
| **Incremental graph updates** | Knowledge Graph updates | Only changed nodes and edges are updated, not the entire graph. |
| **Partitioned attention queue** | Attention Trigger Engine | Attention queue is partitioned by workspace context, not global. |

### 13.3 Latency targets

| Operation | Target | Degraded threshold |
|-----------|--------|-------------------|
| Signal capture | < 10ms | > 50ms |
| Observation validation | < 50ms | > 200ms |
| Classification | < 100ms | > 500ms |
| Deduplication | < 50ms | > 200ms |
| Normalisation | < 50ms | > 200ms |
| Identity resolution | < 200ms | > 500ms |
| Confidence calculation | < 50ms | > 200ms |
| Evidence creation | < 100ms | > 500ms |
| Full pipeline (event-driven) | < 500ms | > 2s |
| Full pipeline (polling) | < 5s | > 15s |
| Attention scoring | < 50ms | > 200ms |
| Conflict detection | < 200ms | > 500ms |

---

## 14. Implementation Roadmap

### Phase 11A — Observation Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the core Observation Engine: capture, validation, classification, deduplication, normalisation |
| **Dependencies** | UNIVERSAL_ONTOLOGY.md (§6 Observation, §8 Event), UNIVERSAL_KNOWLEDGE_GRAPH_ARCHITECTURE.md (§1 Nodes, §2 Node Families) |
| **Deliverables** | Signal capture interface, validation rules, classification registry, deduplication engine, normalisation pipeline |
| **Validation criteria** | 1000 signals captured in < 1s. All signals validated. No duplicates. All signals classified. |

### Phase 11B — Identity Resolution

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement identity resolution for perception: entity extraction, identity matching, resolution confidence |
| **Dependencies** | Phase 11A, UNIVERSAL_ONTOLOGY.md (§3 Identity, §3.5 Identity Governance) |
| **Deliverables** | Entity extraction, identity matching, resolution confidence, unresolved identity queue |
| **Validation criteria** | 95% identity resolution accuracy. Unresolved identities do not block pipeline. Resolution is deterministic. |

### Phase 11C — Evidence Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement evidence construction: verification, contextualisation, confidence assignment, evidence creation |
| **Dependencies** | Phase 11A, Phase 11B, UNIVERSAL_ONTOLOGY.md (§7 Evidence), KG §4 (Evidence Graph) |
| **Deliverables** | Verification pipeline, contextualisation engine, confidence assignment, evidence creation, Knowledge Graph integration |
| **Validation criteria** | Every observation → evidence. Evidence is immutable. Evidence has full provenance. |

### Phase 11D — Attention Trigger Engine

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement the Attention Trigger Engine: trigger factors, scoring, attention queue, threshold evaluation |
| **Dependencies** | Phase 11A, Phase 11B, COGNITIVE_WORKSPACE_RUNTIME.md (§2 Attention Engine) |
| **Deliverables** | Trigger scoring, attention queue, threshold evaluation, priority assignment |
| **Validation criteria** | Trigger scores are deterministic. Queue is bounded. Above-threshold observations trigger attention. |

### Phase 11E — Conflict Resolution

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement conflict resolution: contradictory observations, multiple sources, stale information, uncertain information, missing information |
| **Dependencies** | Phase 11A – Phase 11C, UNIVERSAL_ONTOLOGY.md (§7 Evidence), ADAPTIVE_INTELLIGENCE_RUNTIME.md (§13 Human Governance) |
| **Deliverables** | Conflict detection, resolution hierarchy, escalation path, founder resolution interface |
| **Validation criteria** | All 5 conflict types detected. Resolution hierarchy followed. Escalation works. Founder resolution is recorded. |

### Phase 11F — Continuous Observation

| Aspect | Detail |
|--------|--------|
| **Objectives** | Implement continuous observation: event-driven, polling, scheduled, streaming, incremental, observation decay, archiving |
| **Dependencies** | Phase 11A – Phase 11E, COGNITIVE_WORKSPACE_RUNTIME.md (§9 Event Bus), KG §5 (Temporal Graph) |
| **Deliverables** | Event-driven observation, polling engine, scheduled observation, streaming handler, incremental observation, observation decay, archiving |
| **Validation criteria** | All 6 observation modes work. Observations decay correctly. Archived observations are recoverable. |

---

## Appendix A: Perception Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       UNIVERSAL PERCEPTION ARCHITECTURE                       │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  SOURCE LAYER                                                         │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐  │   │
│  │  │Conv. │ │ Docs │ │ Cal. │ │Email │ │Voice │ │System│ │Manual│  │   │
│  │  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘  │   │
│  │     │        │        │        │        │        │        │       │   │
│  └─────┼────────┼────────┼────────┼────────┼────────┼────────┼───────┘   │
│        │        │        │        │        │        │        │           │
│  ┌─────┴────────┴────────┴────────┴────────┴────────┴────────┴───────┐   │
│  │  OBSERVATION PIPELINE (§3)                                        │   │
│  │  Capture → Validate → Classify → Deduplicate → Normalise          │   │
│  │  → Identity Resolution → Confidence → Evidence → KG Update       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌────────────────────────────────┼─────────────────────────────────┐   │
│  │  PERCEPTION LAYER              │                                  │   │
│  │  ┌────────────────┐  ┌────────┴────────┐  ┌──────────────────┐  │   │
│  │  │  Reality       │  │  Context        │  │  Evidence        │  │   │
│  │  │  Detection     │  │  Extraction     │  │  Construction    │  │   │
│  │  └────────────────┘  └─────────────────┘  └──────────────────┘  │   │
│  │                                                                  │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐  │   │
│  │  │  Attention     │  │  Conflict      │  │  Confidence      │  │   │
│  │  │  Trigger       │  │  Resolution    │  │  Model           │  │   │
│  │  └────────────────┘  └────────────────┘  └──────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌────────────────────────────────┼─────────────────────────────────┐   │
│  │  INTEGRATION LAYER             │                                  │   │
│  │  ┌────────────────┐  ┌────────┴────────┐  ┌──────────────────┐  │   │
│  │  │  Perception    │  │  Workspace      │  │  Constitutional  │  │   │
│  │  │  Event Bus     │  │  Projections    │  │  References      │  │   │
│  │  └────────────────┘  └─────────────────┘  └──────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌────────────────────────────────┼─────────────────────────────────┐   │
│  │  CONSTITUTIONAL CONSUMERS      │                                  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──┴───────┐ ┌──────────┐ ┌──────┐  │   │
│  │  │ Evidence │ │Knowledge │ │Cognitive │ │Adaptive  │ │Exec. │  │   │
│  │  │ Graph    │ │ Graph    │ │ Runtime  │ │Runtime   │ │Intel. │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────┘  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Appendix B: Constitutional Cross-References

| Subsystem | Constitutional references |
|-----------|--------------------------|
| Perception Model (§1) | Ontology §6 (Observation), §7 (Evidence), §8 (Event) |
| Perception Sources (§2) | Ontology §6 (Observation hierarchy), §7 (Evidence types) |
| Observation Pipeline (§3) | Ontology §6 (Observation properties), §1.2 (Provenance) |
| Reality Detection (§4) | Ontology §1 (Object), §3 (Identity), §3.5 (Merge rules) |
| Continuous Observation (§5) | KG §5 (Temporal Graph), CWR §5 (Memory decay) |
| Attention Trigger Engine (§6) | CWR §2 (Attention Engine), Adaptive §2 (Confidence) |
| Context Extraction (§7) | Ontology §13 (Context), CWR §8 (Context Transition) |
| Evidence Construction (§8) | Ontology §7 (Evidence), KG §4 (Evidence Graph) |
| Conflict Resolution (§9) | Ontology §7.4 (Evidence invariants), Adaptive §13 (Governance) |
| Confidence Model (§10) | Adaptive §2 (Confidence Engine), Ontology §7.3 (Evidence confidence) |
| Perception Event Bus (§11) | CWR §9 (Cognitive Event Bus), KG §10 (Graph Events) |
| Workspace Projection (§12) | CWR §3 (Projection Engine), KG §8 (Graph Projections) |
| Scalability (§13) | KG §11 (Scalability Strategy) |