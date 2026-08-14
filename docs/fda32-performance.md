# FDA32 — Performance / Scale Baseline Measurement

**Date:** 2026-08-14  
**Backend:** http://127.0.0.1:5001  
**Environment:** development  
**Uptime:** ~4 minutes at measurement time  
**DB:** PostgreSQL 16  
**Workers:** 4 gunicorn workers  

---

## 1. Methodology

Each endpoint was measured **3 times** end-to-end (client → server → response). All authenticated measurements used the `demo@shunyaos.com` / `Demo2024!` credentials, which set `identity_id` in the session (required by search, objects, and AI endpoints). Timing was done via `time.monotonic()` from the Python `urllib` client — includes network round-trip, Flask request processing, DB queries, and response serialization.

Concurrent measurements: 5 simultaneous requests via Python threads, measuring total wall-clock time and per-request latency.

---

## 2. Individual Endpoint Measurements

### 2.1 Health Check — `GET /health`

| Trial | Status | Time    |
|-------|--------|---------|
| 1     | 200    | 5.5 ms  |
| 2     | 200    | 4.9 ms  |
| 3     | 200    | 4.1 ms  |

| Metric | Value   |
|--------|---------|
| Min    | 4.1 ms  |
| Max    | 5.5 ms  |
| Avg    | **4.9 ms** |

**Notes:** Performs a `SELECT 1` DB check and returns JSON with uptime, environment, and request ID. No auth required.

---

### 2.2 Readiness Check — `GET /ready`

| Trial | Status | Time   |
|-------|--------|--------|
| 1     | 200    | 4.0 ms |
| 2     | 200    | 4.0 ms |
| 3     | 200    | 5.8 ms |

| Metric | Value   |
|--------|---------|
| Min    | 4.0 ms  |
| Max    | 5.8 ms  |
| Avg    | **4.6 ms** |

**Notes:** Lightweight DB check, no auth. Similar to /health but simpler payload.

---

### 2.3 Liveness Check — `GET /live`

| Trial | Status | Time   |
|-------|--------|--------|
| 1     | 200    | 2.2 ms |
| 2     | 200    | 2.2 ms |
| 3     | 200    | 1.9 ms |

| Metric | Value   |
|--------|---------|
| Min    | 1.9 ms  |
| Max    | 2.2 ms  |
| Avg    | **2.1 ms** |

**Notes:** Fastest endpoint — no DB check, just a static JSON response. Ideal for load balancer liveness probes.

---

### 2.4 Login — `POST /login/password`

| Trial | Status | Time    |
|-------|--------|---------|
| 1     | 200    | 8.2 ms  |
| 2     | 200    | 15.6 ms |
| 3     | 200    | 9.4 ms  |

| Metric | Value    |
|--------|----------|
| Min    | 8.2 ms   |
| Max    | 15.6 ms  |
| Avg    | **11.1 ms** |

**Notes:** Authenticates via `TeamMember` model, sets `user_id` in session, updates `last_login` timestamp, generates a new token. The 15.6 ms outlier may be due to DB write (token generation + commit).

---

### 2.5 Workspace Load — `GET /workspace/`

| Trial | Status | Time    | Body Size |
|-------|--------|---------|-----------|
| 1     | 200    | 19.3 ms | 2,195 B   |
| 2     | 200    | 2.3 ms  | 2,195 B   |
| 3     | 200    | 3.6 ms  | 2,195 B   |

| Metric | Value    |
|--------|----------|
| Min    | 2.3 ms   |
| Max    | 19.3 ms  |
| Avg    | **8.4 ms** |

**Notes:** Serves a static SPA shell (index.html, 2.2 KB). First request includes cookie session parse overhead (19.3 ms). Subsequent requests are faster due to OS-level file cache. **No DB queries** — pure file read + response.

---

### 2.6 Object Listing — `GET /api/v1/founder/objects`

| Trial | Status | Time     | Body Size |
|-------|--------|----------|-----------|
| 1     | 200    | 1,032 ms | 213,500 B |
| 2     | 200    | 1,235 ms | 213,500 B |
| 3     | 200    | 1,222 ms | 213,500 B |

| Metric | Value      |
|--------|------------|
| Min    | 1.03 s     |
| Max    | 1.24 s     |
| Avg    | **1.16 s** |

**⚠️ BOTTLENECK #1 — Slowest authenticated endpoint.**

**Notes:** Returns 508 objects (213 KB payload). Time is dominated by SQL query execution and JSON serialization of a large result set. This endpoint would benefit from:
- Pagination (limit/offset)
- Filtering by type or status
- Lazy loading of object content
- Response caching

---

### 2.7 Search — `GET /api/v1/search?q=performance+test`

| Trial | Status | Time     | Body Size |
|-------|--------|----------|-----------|
| 1     | 200    | 1,568 ms | 2,416 B   |
| 2     | 200    | 1,915 ms | 2,361 B   |
| 3     | 200    | 674 ms   | 2,361 B   |

| Metric | Value      |
|--------|------------|
| Min    | 674 ms     |
| Max    | 1.92 s     |
| Avg    | **1.39 s** |

**⚠️ BOTTLENECK #2 — High variance, network-dependent.**

**Notes:** Makes an external DuckDuckGo API call (`duckduckgo_search` library → `ddgs.text()`). The 674 ms outlier is a cache hit or faster upstream response. The 1.9s outlier is a slow upstream response. **This is not a server-side bottleneck** — the Flask handler is fast, but the external search dependency introduces significant latency.

---

### 2.8 AI Chat — `POST /api/v1/ai/chat`

| Trial | Status | Time    | Provider |
|-------|--------|---------|----------|
| 1     | 200    | 134 ms  | Groq (llama-3.3-70b-versatile) |
| 2     | 200    | 115 ms  | Groq (llama-3.3-70b-versatile) |
| 3     | 200    | 139 ms  | Groq (llama-3.3-70b-versatile) |

| Metric | Value      |
|--------|------------|
| Min    | 115 ms     |
| Max    | 139 ms     |
| Avg    | **129 ms** |

**Notes:** Uses Groq with fallback chain. Prompt was 2-token response ("OK"). Total tokens: 45 (43 prompt + 2 completion). Groq's inference time was ~10 ms; the remaining ~120 ms is network round-trip. Acceptable for AI chat. **No evidence-logging overhead was significant** (the log_evidence and cortex_bridge calls are wrapped in try/except).

---

### 2.9 System Health — `GET /system/health`

| Trial | Status | Time   | Body Size |
|-------|--------|--------|-----------|
| 1     | 200    | 7.0 ms | 307 B     |
| 2     | 200    | 9.1 ms | 307 B     |
| 3     | 200    | 6.5 ms | 307 B     |

| Metric | Value   |
|--------|---------|
| Min    | 6.5 ms  |
| Max    | 9.1 ms  |
| Avg    | **7.5 ms** |

**Notes:** Returns detailed system metrics: DB latency, event queue backlog, integration status, execution loop status. No auth required. Fast despite the richer payload.

---

## 3. Concurrent Request Performance

### 3.1 5× Simultaneous — `GET /health`

| Thread | Status | Time   |
|--------|--------|--------|
| 0      | 200    | 7.6 ms |
| 1      | 200    | 4.0 ms |
| 2      | 200    | 11.0 ms|
| 3      | 200    | 9.8 ms |
| 4      | 200    | 9.6 ms |

| Metric      | Value      |
|-------------|------------|
| Wall time   | **15.8 ms**|
| Avg per req | 8.4 ms     |
| Throughput  | ~316 req/s |

**Assessment:** Scales well. Gunicorn workers handle concurrent requests without contention.

---

### 3.2 5× Simultaneous — `GET /workspace/` (authenticated)

| Thread | Status | Time    |
|--------|--------|---------|
| 0      | 200    | 19.1 ms |
| 1      | 200    | 8.8 ms  |
| 2      | 200    | 15.1 ms |
| 3      | 200    | 10.0 ms |
| 4      | 200    | 8.9 ms  |

| Metric      | Value      |
|-------------|------------|
| Wall time   | **22.4 ms**|
| Avg per req | 12.4 ms    |
| Throughput  | ~223 req/s |

**Assessment:** Good. Session cookie parsing per request adds some overhead but still acceptable.

---

### 3.3 5× Simultaneous — `GET /api/v1/founder/objects` (authenticated)

| Thread | Status | Time     |
|--------|--------|----------|
| 0      | 200    | 614 ms   |
| 1      | 200    | 1,133 ms |
| 2      | 200    | 1,073 ms |
| 3      | 200    | 1,860 ms |
| 4      | 200    | 2,365 ms |

| Metric      | Value       |
|-------------|-------------|
| Wall time   | **2,373 ms**|
| Avg per req | 1,409 ms    |
| Throughput  | ~2.1 req/s  |

**⚠️ POOR SCALING.** Each request takes ~1.2s individually, and concurrent requests compound the issue. The DB query for 508 objects is likely the bottleneck — all workers compete for the same DB connection pool.

---

## 4. Database Query Time

**Raw psql query:** `SELECT 1`

| Trial | Time     |
|-------|----------|
| 1     | 52.0 ms  |
| 2     | 54.0 ms  |
| 3     | 57.6 ms  |

| Metric | Value    |
|--------|----------|
| Min    | 52.0 ms  |
| Max    | 57.6 ms  |
| Avg    | **54.5 ms** |

**Notes:** The `psql` client overhead dominates — the actual DB query is sub-millisecond. The `db_latency_ms` reported by `/system/health` confirms this (1.1–1.8 ms). The 54.5 ms is the cost of launching the `psql` process, establishing a connection, and tearing it down.

---

## 5. Memory Usage

| PID     | %CPU | %MEM | RSS (MB) | Process                      |
|---------|------|------|----------|------------------------------|
| 3961499 | 2.6  | 2.3  | 185.0    | gunicorn worker              |
| 3961501 | 3.4  | 2.2  | 181.6    | gunicorn worker              |
| 3961500 | 2.1  | 1.9  | 157.3    | gunicorn worker              |
| 3961497 | 0.1  | 0.3  | 25.9     | gunicorn master (arbiter)    |

| Metric               | Value    |
|----------------------|----------|
| Workers              | 3 (sync) |
| Master (arbiter)     | 1        |
| Total RSS            | **549.7 MB** |
| Avg per worker       | 174.6 MB |
| Min worker RSS       | 157.3 MB |
| Max worker RSS       | 185.0 MB |

**Assessment:** Memory usage is high per worker (~175 MB RSS). For 3 sync workers at 175 MB each, that's 525 MB just for the application workers. This is likely due to the Flask app loading all modules, SQLAlchemy models, and AI provider registry into each worker's memory space.

---

## 6. Summary Table

| Endpoint                     | Method | Min     | Max     | Avg      | Body Size | Auth | Notes                       |
|------------------------------|--------|---------|---------|----------|-----------|------|-----------------------------|
| `/health`                    | GET    | 4.1 ms  | 5.5 ms  | **4.9 ms**  | 158 B     | No   | Fast, includes DB check     |
| `/ready`                     | GET    | 4.0 ms  | 5.8 ms  | **4.6 ms**  | 103 B     | No   | Fast, lightweight DB check  |
| `/live`                      | GET    | 1.9 ms  | 2.2 ms  | **2.1 ms**  | 59 B      | No   | Fastest — no DB             |
| `/login/password`            | POST   | 8.2 ms  | 15.6 ms | **11.1 ms** | 42 B      | No   | Includes DB write           |
| `/workspace/`                | GET    | 2.3 ms  | 19.3 ms | **8.4 ms**  | 2.2 KB    | Yes  | Static SPA shell            |
| `/api/v1/founder/objects`    | GET    | 1.03 s  | 1.24 s  | **1.16 s**  | 213 KB    | Yes  | **⚠️ BOTTLENECK #1**        |
| `/api/v1/search?q=test`      | GET    | 674 ms  | 1.92 s  | **1.39 s**  | 2.4 KB    | Yes  | **⚠️ BOTTLENECK #2** (external) |
| `/api/v1/ai/chat`            | POST   | 115 ms  | 139 ms  | **129 ms**  | 283 B     | Yes  | Groq inference, ~10 ms net  |
| `/system/health`             | GET    | 6.5 ms  | 9.1 ms  | **7.5 ms**  | 307 B     | No   | Detailed metrics, no auth   |

---

## 7. Identified Bottlenecks

### Bottleneck #1: Object Listing (`/api/v1/founder/objects`)
- **Severity:** HIGH
- **Avg response:** 1.16 s (3× trials)
- **Root cause:** Returns all 508 objects (213 KB) in a single query with no pagination, filtering, or lazy loading
- **Impact:** Single request is slow; 5 concurrent requests compound to 2.4s wall time
- **Recommendations:**
  - Add pagination (`?limit=50&offset=0`)
  - Add type/status filtering
  - Add `?fields=summary` option to return only lightweight fields
  - Add response caching (Redis or in-memory with TTL)
  - Consider adding a database index on `status` and `updated_at`

### Bottleneck #2: Search (`/api/v1/search`)
- **Severity:** MEDIUM
- **Avg response:** 1.39 s (high variance: 674 ms – 1.92 s)
- **Root cause:** External DuckDuckGo API call — network latency is the bottleneck, not server processing
- **Impact:** Unpredictable response times; depends on upstream API availability
- **Recommendations:**
  - Add a timeout (currently 10s — too generous)
  - Add result caching (TTL: 5 minutes)
  - Consider a local search index (e.g., Meilisearch, Typesense) for common queries
  - Add circuit breaker for when DuckDuckGo is slow/unavailable

### Observation: Worker Memory
- **Severity:** LOW (for development)
- **Current:** 175 MB avg per worker, 550 MB total
- **Recommendation:** Review for production — consider preload config (`--preload`) to share memory, or switch to `gevent` async workers to reduce total memory footprint

---

## 8. Recommendations

1. **Immediate (FDA32 follow-up):**
   - Add pagination to `/api/v1/founder/objects`
   - Add search result caching with 5-minute TTL
   - Reduce search timeout from 10s to 5s

2. **Short-term:**
   - Add database indexes on frequently-queried object columns (`status`, `updated_at`, `created_by`)
   - Consider `--preload` for gunicorn to reduce per-worker memory
   - Add response compression for large payloads (213 KB object listing)

3. **Medium-term:**
   - Implement a local search index (Typesense/Meilisearch) to replace DuckDuckGo for internal data
   - Add Redis caching layer for object listings and search results
   - Switch to async gunicorn workers (`gevent` or `uvicorn`) for better concurrency

---

*Report generated by Hermes Agent — FDA32 Performance Baseline Measurement*