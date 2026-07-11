# Shunya Personal Agent — Architecture

> Every user gets a persistent AI agent that knows them, has tools, and acts across channels.
> The goal: feels like a god-like friend — omniscient (knows everything relevant),
> omnipotent (can do anything within governance), omnipresent (across all channels),
> and warm (remembers who you are, how you feel, what you prefer).

## Table of Contents
1. [Current State](#1-current-state-today)
2. [Target State](#2-target-state)
3. [Layers](#3-layers)
4. [Phase 1 Enhanced — Scalable & God-Like](#4-phase-1-enhanced--scalable--god-like)
5. [Build Order](#5-build-order)
6. [Key Design Decisions](#6-key-design-decisions)

## 1. Current State (Today)

```
User → Bird Widget → /api/ai/query → Knowledge Pipeline → Text Response
         (stateless)      (or /ai/action)   (or create entity)
```

- Bird is a chat bubble — no session, no memory, no tools
- Each query is independent — no carry-over
- No proactive behavior

## 2. Target State

```
User (Web / Telegram / WhatsApp / Voice)
                  │
          ┌───────┴───────┐
          │    Channel     │
          │   Adapter      │  ← normalizes input, tracks identity
          └───────┬───────┘
                  │
          ┌───────┴───────┐
          │   Personal     │
          │  Agent Loop    │  ← persistent, per-user session
          │                │     Think → Pick Tool → Execute → Observe → Respond
          └───────┬───────┘
                  │
     ┌────────────┼────────────┐
     │            │            │
┌────┴────┐ ┌─────┴─────┐ ┌───┴────┐
│ Memory  │ │ Tool      │ │ Proact.│
│ Layer   │ │ Registry  │ │ Engine │
├─────────┤ ├───────────┤ ├────────┤
│ Honcho  │ │ Create    │ │ Cron   │
│ per-user│ │ Search    │ │ Trig-  │
│ context │ │ Send Msg  │ │ gers   │
│ + pref  │ │ Finance   │ │ Events │
│ + hist. │ │ Ops       │ │        │
└─────────┘ │ Module    │ └────────┘
            │ Builder   │
            │ Govern.   │
            │ Ingest    │
            │ Analytics │
            └───────────┘
```

## 3. Layers

### A. Channel Adapters

Each channel normalizes input to a uniform `AgentRequest`:

```python
@dataclass
class AgentRequest:
    user_id: str          # persistent user identity
    tenant_id: int
    channel: str          # "web", "telegram", "whatsapp", "voice"
    text: str
    attachments: list
    metadata: dict
    thread_id: str        # for continuous conversations
```

Registered adapters:
- **Web** — Bird widget (already done)
- **Telegram** — existing webhook, redirect to agent loop
- **WhatsApp** — existing webhook, redirect to agent loop
- **Voice** — existing STT pipeline, redirect to agent loop

### B. Personal Agent Loop

```
┌─────────────────────────────────────────────────────┐
│                   Agent Session                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────┐ │
│  │ User     │  │ Think    │  │ Pick     │  │Execute│ │
│  │ Context  │→ │(LLM      │→ │ Tool     │→ │ Tool │→│
│  │ (memory, │  │ decides  │  │ from     │  │ with  │ │
│  │  prefs,  │  │ intent + │  │ Registry │  │ params│ │
│  │  history)│  │ plan)    │  │          │  │       │ │
│  └──────────┘  └──────────┘  └──────────┘  └───┬───┘ │
│                                                 │     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │     │
│  │ Respond  │← │ Observe  │← │ Learn    │◄─────┘     │
│  │ (text/   │  │ (result) │  │ (store in│           │
│  │  card/   │  │          │  │  memory) │           │
│  │  action) │  │          │  │          │           │
│  └──────────┘  └──────────┘  └──────────┘           │
│                                                     │
│  Session State: conversation history (last N turns) │
│  Persisted: Honcho (long-term), Redis (short-term)  │
└─────────────────────────────────────────────────────┘
```

The loop replaces the current single-shot `/api/ai/query` endpoint.

### C. Tool Registry

Every Shunya capability is registered as a tool with a schema:

```python
@dataclass
class AgentTool:
    name: str
    description: str          # LLM reads this to decide when to use the tool
    parameters: list[ToolParam]  # JSON Schema for LLM to fill
    required_auth: str        # "any", "admin", "manager"
    governance_level: str     # "auto", "draft", "govern"
    handler: callable         # the actual function

@dataclass
class ToolParam:
    name: str
    type: str                 # "string", "number", "boolean", "array"
    description: str
    required: bool
    enum: list[str] | None    # for select-type params
```

**Initial tool set:**

| Tool | What it does | Auth |
|------|-------------|------|
| `create_entity` | Creates a record from parsed data | agent |
| `search_knowledge` | Searches company knowledge base | agent |
| `search_web` | Searches the internet | agent |
| `list_entities` | Lists records of a type with filters | agent |
| `get_entity` | Gets a single record | agent |
| `update_entity` | Updates record fields | agent |
| `send_message` | Sends message via WhatsApp/Telegram/Email | manager |
| `run_finance_report` | Generates P&L, invoice summary | admin |
| `generate_invoice` | Creates an invoice | manager |
| `create_module` | Builds a new entity type | govern |
| `search_memory` | Queries Honcho per-user memory | agent |

### D. Memory Layer (per-user, not just per-tenant)

Honcho already has per-user context. We surface it to the agent:

```
For each user session:
  1. Honcho context → injected as "who this user is"
  2. Conversation history (last 20 turns) → injected as context
  3. Entity data they own → searchable
```

### E. Proactive Engine

Time-based and event-based triggers that wake the agent up:

```
Agent Cron:
  "Check for leads in 'new' status > 3 days" → Agent sends proactive message
  "Scan for unpaid invoices due in 2 days" → Agent notifies user
  "Learning Engine proposals pending" → Agent suggests review
```

## 4. Phase 1 Enhanced — Scalable & God-Like

Phase 1 is the foundation. It must be built so that every subsequent phase compounds without rewrites.
These additions make the agent feel omniscient, omnipotent, omnipresent, and warm from day one.

### A. User Personality Profile (the "Friend" Foundation)

Every user gets a `UserProfile` that the agent reads before every interaction:

```python
@dataclass
class UserProfile:
    # Identity
    user_id: str
    name: str
    role: str
    tenant_id: int

    # Communication style (auto-learned + manually set)
    communication_style: str = "casual"   # "formal" | "casual" | "direct" | "coaching"
    preferred_language: str = "en"        # ISO code — code-switching respected
    verbosity: str = "balanced"          # "concise" | "balanced" | "detailed"
    emoji_style: str = "moderate"        # "none" | "moderate" | "expressive"

    # Behavioral patterns (auto-learned)
    preferred_working_hours: tuple = (9, 18)  # 9 AM - 6 PM
    common_actions: dict = field(default_factory=dict)  # {"create_lead": 47, "search_web": 12}
    last_active_hour: int = 0
    average_response_time_minutes: int = 0

    # Relationship (auto-updated)
    session_count: int = 0
    first_seen: str = ""
    last_seen: str = ""
    correction_count: int = 0          # how many times user corrected the agent
    trust_score: float = 0.5           # 0-1, increases with successful actions

    # Pet peeves (learned from corrections + explicit)
    pet_peeves: list[str] = field(default_factory=list)
    # e.g. ["don't suggest calls before 10 AM", "always show budget as ₹ not INR"]
```

**Why this makes it god-like:** The agent doesn't treat every user the same. It knows your name, your rhythm, your pet peeves. It adjusts tone, verbosity, and suggestions to fit YOU.

### B. Graceful Fallback Chain (the "God" reliability)

When any tool fails, the agent does NOT say "I couldn't do that." It falls back through a chain:

```
Attempt Tool → Failed?
   → Analyze error (missing param? auth? data issue?)
   → Attempt with corrected params
   → Still fails?
       → Offer alternatives within the same domain
       → Still no?
           → Say EXACTLY why in human terms, with a specific fixable next step
```

**Pattern — every tool wraps in a SafeTool:**

```python
class SafeTool:
    def execute_with_fallback(self, params, user_prefs):
        try:
            result = self.handler(params)
            return AgentToolResult(success=True, data=result, message="")
        except MissingParamError as e:
            return AgentToolResult(
                success=False,
                message=f"I need {e.param} to continue.",
                suggested_fix={"action": "ask_user", "question": f"What's the {e.param}?"}
            )
        except AuthError:
            return AgentToolResult(
                success=False,
                message="This needs admin approval. I've queued it for review.",
                suggested_fix={"action": "queue_for_approval"}
            )
        except DataError as e:
            return AgentToolResult(
                success=False,
                message=f"I found the data but it's incomplete. {e.detail}",
                suggested_fix={"action": "offer_alternative", "tool": "search_knowledge", "params": {}}
            )
        except Exception:
            return AgentToolResult(
                success=False,
                message="I hit an unexpected issue. Let me try a different approach.",
                suggested_fix={"action": "retry_different"}
            )
```

**Why this makes it god-like:** The agent never gives up. It always has a next move. Users feel like the system has their back.

### C. Correction Learning Loop

When a user corrects the agent, it's the most valuable signal. The agent must learn from it:

```
User: "No, I meant the urgent ones, not all leads"
  → Correction ingested into memory
  → Short-term: adjust THIS response
  → Medium-term: update user profile (e.g., "user distinguishes urgent vs all")
  → Long-term: pattern recognized → proactive behavior adjusted
```

```python
class CorrectionEngine:
    @staticmethod
    def ingest(user_id: str, original_query: str, correction: str, agent_action: dict):
        # 1. Store correction in Honcho
        # 2. Update UserProfile.correction_count
        # 3. Extract the specific misunderstanding
        # 4. Store as a "don't do this again" rule
        # 5. If same correction happens 3x, auto-adjust the agent's behavior
```

**Why this makes it god-like:** The agent gets smarter with every correction. After a few weeks, the user thinks "it just gets me."

### D. Context Window Management (Scalability)

The agent session can't grow unbounded. Intelligent compression:

```python
class ContextManager:
    max_turns: int = 30       # soft limit
    compression_threshold: int = 20

    def build_context(self, session_history, user_profile, honcho_memories):
        # 1. Always include: user_profile (compact), honcho_top_memories (5), last 3 turns
        # 2. If history > 20 turns: summarize older turns into bullet points
        # 3. If history > 30 turns: drop the oldest summarized block
        # 4. Priority: corrections > successful actions > conversation
        pass
```

**Why this makes it scalable:** 10,000 users with 1,000 turns each don't break memory. The agent always works with the most relevant context.

### E. Intent Confidence & Clarification Protocol

When the agent is unsure, it must clarify — but gracefully:

```python
class ClarificationProtocol:
    confidence_threshold: float = 0.7

    def handle_uncertainty(self, intent, confidence):
        if confidence >= 0.9:
            return ExecuteAction(intent)  # Go ahead
        elif confidence >= 0.7:
            return ProposeWithConfirmation(intent)  # "I think you want to... confirm?"
        elif confidence >= 0.4:
            return AskClarifyingQuestion(intent)  # "Did you mean X or Y?"
        else:
            return OfferHelpFallback()  # "I'm not sure what you need. Here's what I can do..."
```

**Why this makes it god-like:** It never confidently does the wrong thing. When unsure, it's honest but helpful — like a wise friend who says "let me make sure I understand."

### F. Personality Engine (the "Friend" Layer)

The agent's persona is configurable per user and adapts:

```python
PERSONAS = {
    "coach": {
        "tone": "encouraging, asks questions back",
        "phrases": [
            "Great question! Here's what I'd recommend...",
            "You're on the right track. Let me suggest...",
        ],
    },
    "assistant": {
        "tone": "neutral, efficient, minimal",
        "phrases": ["Done.", "Here you go.", "What's next?"],
    },
    "friend": {
        "tone": "warm, remembers personal context, casual",
        "phrases": [
            "Hey! I noticed the Sharma deal is going well — want me to prep the proposal?",
            "You had a busy morning. Want me to catch you up on what changed?",
        ],
    },
    "guardian": {
        "tone": "protective, flags risks proactively",
        "phrases": [
            "Heads up — the Patel invoice is 7 days overdue.",
            "I'd recommend a second look before sending this.",
        ],
    },
}
```

Default persona starts at "assistant" and shifts toward "friend" as trust_score increases.

### G. Observability (for you — the god behind the god)

Every agent action is logged with full traceability:

```python
@dataclass
class AgentTrace:
    turn_id: str
    user_id: str
    tenant_id: str
    channel: str
    query: str
    intent: dict
    tool_calls: list[ToolCallTrace]  # which tools, params, results, duration
    confidence: float
    tokens_used: int
    latency_ms: int
    corrections: list[str]
    response: str
    created_at: str
```

Why this matters: at scale, you need to debug sessions, measure latency, track cost per user, and identify where the agent fails most often.

### H. Omniscient Search Engine (Scan the Entire Internet)

The agent must be able to scan the entire internet for the exact answer AND know when to answer from company data vs. the web. This is the "omniscience" layer.

#### H1. Source Decision Tree

Before searching, the agent classifies the query to decide WHERE to look:

```
User Query
    │
    ├── Entity-specific: "Show me the Patel invoice"
    │   → Internal data ONLY (company records)
    │
    ├── Company knowledge: "What's our refund policy?"  
    │   → Knowledge base FIRST, web fallback
    │
    ├── Live business data: "What's our revenue this month?"
    │   → Entity data + analytics ENGINE
    │
    ├── Research/Compare: "Compare Bali vs Maldives for honeymoon"
    │   → Web FIRST (trending), then internal (past bookings)
    │
    ├── Factual: "What's the visa fee for Thailand?"
    │   → Web search (multiple sources), cross-validate
    │
    ├── Real-time: "What's the flight status of UK-815?"
    │   → Web search (live), NOT cached knowledge
    │
    ├── User command: "Create a lead for Sharma family"
    │   → Action pipeline (not search at all)
    │
    └── Ambiguous: "Tell me about Bali"
        → BOTH: internal data (our Bali packages) + web (current info)
        → Present with dual-source labels
```

#### H2. Multi-Engine Web Search

Not one search engine — multiple, with cross-validation:

```python
class WebSearchEngine:
    """Searches across multiple engines, cross-validates, and returns the best answer."""

    engines: list[SearchProvider] = []
    # Providers: Firecrawl, Tavily, Google, Bing, Brave, DuckDuckGo
    # Each implements: search(query) -> SearchResult[]

    def search_with_fallback(self, query: str, depth: str = "normal") -> SearchResult:
        """
        depth = "quick"  → Try primary engine only, return fast
        depth = "normal" → Try primary, fallback to secondary on low confidence
        depth = "deep"   → Try ALL engines, cross-validate, return best
        depth = "exact"  → Full page content extraction from top results
        """
        pass

    def cross_validate(self, results: list[SearchResult]) -> CrossValidatedResult:
        """
        Compare results from multiple sources:
        - Agreement score (what % of sources agree)
        - Confidence per source (historical reliability)
        - Flag contradictions
        - Return the most corroborated answer
        """
        pass
```

#### H3. Deep Page Reading (the "Exact Answer" Protocol)

For queries where the user needs a specific, precise answer (not just a summary):

```python
class DeepReader:
    """Navigates to specific pages, extracts full content, and finds the exact answer."""

    def read_and_extract(self, urls: list[str], target_query: str) -> ExactAnswer:
        """
        1. Fetch full page content from each URL
        2. Extract relevant sections using target_query
        3. Cross-reference across pages
        4. Return the exact answer with source citation
        """
        pass

    def extract_structured_data(self, url: str, schema: dict) -> dict:
        """
        Extract structured data from a page (prices, dates, tables, lists).
        schema defines what to extract.
        """
        pass
```

#### H4. Confidence & Verification System

Every piece of information carries a verification badge visible to the user:

```python
@dataclass
class VerifiedAnswer:
    answer: str
    source_type: SourceType  # INTERNAL_DATA | KNOWLEDGE_BASE | WEB_SINGLE | WEB_MULTI | LIVE
    confidence: Confidence   # HIGH | MEDIUM | LOW
    verification_badge: str  # ✅ Verified | 📚 Company | 🌐 Web | ⚠️ Mixed | ❓ Low confidence
    sources: list[Source]
    contradictions: list[Contradiction]  # "Other sources say X, but our data says Y"
    last_verified: str        # ISO timestamp
    needs_refresh: bool       # True if the data is time-sensitive and old

    def to_display_html(self) -> str:
        """Render as HTML with badges for the Bird widget."""
        pass
```

**Verification badge rules:**

| Badge | Meaning | When |
|-------|---------|------|
| ✅ Verified | Cross-checked across 2+ sources that agree | Multiple web sources OR internal data + web |
| 📚 Company Data | From internal knowledge base or entity records | Internal-only queries |
| 🌐 Web (Single) | From one web source | Single search result, not cross-checked |
| ⚠️ Conflicting | Sources disagree | Different sources give different answers |
| ❓ Low Confidence | Agent is unsure | Partial data, ambiguous query, or no confident source |
| 🔴 Not Found | Agent searched everything and couldn't find | Information doesn't exist in any accessible source |

#### H5. Cache & Freshness

Not all data needs a fresh search. Smart caching with TTL:

```python
class SearchCache:
    """Cache search results with time-to-live per domain."""

    ttl_by_domain: dict = {
        "exchange_rate": 300,       # 5 minutes
        "flight_status": 120,       # 2 minutes
        "weather": 1800,            # 30 minutes
        "visa_info": 86400,         # 24 hours
        "company_knowledge": 604800, # 7 days
        "entity_data": -1,          # Never cache (live from DB)
    }

    def get(self, query: str, domain: str) -> Optional[CachedResult]:
        """Return cached result if fresh, None otherwise."""
        pass

    def set(self, query: str, domain: str, result: SearchResult):
        """Store with domain-appropriate TTL."""
        pass
```

#### H6. The "I Don't Know" Protocol (Honesty > Hallucination)

When the agent genuinely cannot find the answer, it must NOT hallucinate:

```
Agent searched:
  1. Internal data → No relevant records
  2. Knowledge base → No matching entries
  3. Web (engine 1) → No relevant results
  4. Web (engine 2) → No relevant results
  5. Deep page reading → No exact match

→ Response:
  "I searched your company data, the knowledge base, and the web but couldn't find
   a clear answer to '{query}'. Here's what I can do:
   - Upload a document with this information on the Ingest page
   - Ask me to search differently
   - I can research this deeper — just tell me where to look"
```

**Why this makes it god-like:** The agent never lies. It exhausts every source before admitting it doesn't know. And when it doesn't know, it gives you a path to fix it.

#### H7. End-to-End Search Flow

```
User: "What's the visa fee for Thailand for Indian citizens?"

Agent:
  1. Classify: factual query, needs web, fresh data needed
  2. Check cache: no cached result for this query
  3. Search web (engine 1): "Thailand visa fee Indian citizens 2026"
  4. Search web (engine 2): same query, different engine
  5. Cross-validate: both engines agree on ₹2,000 for tourist visa
  6. Deep read: open the top 2 pages, extract exact fee table
  7. Build VerifiedAnswer:
     answer: "Tourist visa: ₹2,000 (60 days, single entry)"
     source_type: WEB_MULTI
     confidence: HIGH
     badge: ✅ Verified
     sources: [indianvisa.gov.in, thaiembassy.in]
  8. Check internal: does our company have Thailand packages?
     → Yes, 3 packages found
     → Append: "We also have 3 Bali packages. Want me to show them?"

Response:
  ✅ Verified
  Tourist visa for Thailand: ₹2,000 (60 days, single entry)
  Sources: indianvisa.gov.in · thaiembassy.in

  📚 From your company data:
  We have 3 Thailand packages. Want to see them?
```

### Summary: Phase 1 Enhanced Components

| Component | Why God-Like | Why Scalable |
|-----------|-------------|-------------|
| User Personality Profile | Knows you personally, adapts tone | Compact, per-user, fast lookup |
| Graceful Fallback Chain | Never gives up | Prevents cascading failures |
| Correction Learning Loop | Gets smarter over time | Offline batch processing |
| Context Window Management | Remembers what matters | Fixed memory per session |
| Clarification Protocol | Never confidently wrong | Prevents compounding errors |
| Personality Engine | Feels like a friend | Configurable, A/B testable |
| Observability | You can debug anything | Structured logging, indexed |
| Source Decision Tree | Knows WHERE to look (internal vs web) | Prevents wasted searches |
| Multi-Engine Web Search | Searches everywhere, not one place | Fallback per engine, no single point of failure |
| Deep Page Reading | Not just snippets — full content extraction | Async, parallel page fetching |
| Confidence & Verification | Every answer has a badge (✅📚🌐⚠️❓) | Users learn to trust the badges |
| Cache & Freshness | Real-time when needed, cached when safe | TTL per domain, no stale data |
| I Don't Know Protocol | Never hallucinates | Explicit fallback, user can fill the gap |
| Dual-Source Merging | Internal + web combined in one answer | Both sources independently checked |

## 5. Build Order

**Phase 1 (4-5 hours): Tool Registry + Agent Loop + God-Like Foundation**
```
Day 1:
  - ToolRegistry class with discoverable tools
  - AgentLoop: think→pick→execute→observe→respond
  - 8 initial tools (create, search_knowledge, search_web, list, get, update, send_message, run_report)
  - SafeTool wrapper with fallback chains
  - UserProfile model + Honcho wiring
  - CorrectionEngine (learn from "no, I meant X")
  - ContextManager (intelligent history compression)
  - ClarificationProtocol (uncertainty → graceful question)
  - PersonalityEngine (tone adapts per user)
  - SourceDecisionTree (internal vs web classification)
  - WebSearchEngine (multi-engine with cross-validation)
  - DeepReader (page content extraction)
  - VerifiedAnswer + VerificationBadge system
  - SearchCache with TTL per domain
  - I Dont Know Protocol (exhaustive search → honest fallback)
  - DualSourceMerger (internal + web in one answer)
  - AgentTrace (full observability)
  - Wire Bird widget to AgentLoop
```

**Phase 2 (1-2 hours): Proactive Engine**
```
Day 2:
  - Proactive triggers (time + event based)
  - Agent Cron for periodic scans
  - "You haven't checked X" patterns
  - Learning from patterns (if user always checks leads at 10 AM, start having it ready)
```

**Phase 3 (1 hour): Channel Continuity**
```
Day 3:
  - Telegram adapter → AgentLoop instead of standalone webhook
  - WhatsApp adapter → AgentLoop
  - Cross-channel session continuity via thread_id
  - User personality profile shared across channels
```

**Phase 4 (ongoing): More Tools**
```
- Agent learns new tools as we add capabilities
- Module Builder creates entity types → auto-registers entity-type tool
- User can say "create a patient tracking module" → Module Builder → new entity type → new tool
```

## 6. Key Design Decisions

1. **LLM as the Brain, Not the Pipeline** — Today's pipeline has hand-coded intent detection. The agent uses the LLM to decide intent AND fill tool parameters. This generalizes without regex patterns.

2. **Tool Introspection** — The agent reads the tool manifest to know what it can do. Adding a new capability = registering a tool = agent can use it immediately.

3. **Session + Persistence** — Redis for hot session state (last 20 turns). Honcho for cold storage (user profile, long-term memory). Agent merges both on every turn.

4. **Governance First** — Every tool has a governance level. Agent checks before executing. Draft actions show confirmation card. Govern actions queue for approval.

5. **Channel Agnostic** — The AgentLoop doesn't know about channels. It outputs `AgentResponse` (text + cards + actions). Channel adapters render it.

6. **Internal Data First, Web for Depth** — The Source Decision Tree always prioritizes internal data for entity-specific queries, but proactively enriches with web data for research, comparison, and factual queries. The user never gets a partial answer when the web can complete it.

7. **Confidence Over Speed** — The agent can answer faster with lower confidence, but it always SHOWS the confidence badge. Users learn to trust ✅ and investigate ⚠️. Speed is secondary to correctness.

8. **Cache Aggressively, Verify Freshness** — Cache everything by default with domain-appropriate TTL. But time-sensitive data (flights, rates, news) always gets a fresh search. The agent tells the user when data is cached vs fresh.

9. **Cross-Validation is Mandatory** — For any factual claim from the web, at least 2 sources must agree before the agent marks it as ✅ Verified. Single-source answers are marked 🌐 Web (Single) — the user knows it's not cross-checked.

10. **Honesty > Hallucination** — The agent exhausts every source (internal → KB → web engine 1 → web engine 2 → deep page read) before saying "I don't know." But when it doesn't know, it says so clearly and offers a path to fill the gap. Never fabricate.
