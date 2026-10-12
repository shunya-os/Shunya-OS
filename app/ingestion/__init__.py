"""SHUNYA ingestion package — RESERVED (currently empty by design).

The original source for this package was removed; only stale bytecode
remained, which crashed any import attempt (no ``__init__.py``). As of the
docs/knowledge/comms/execution dead-end remediation:

- No code imports this package (verified: no ``app.ingestion`` references
  in app/, core/, or tests/).
- Real ingestion lives in ``app.documents_knowledge`` (governed pipeline)
  and ``app/documents_api.py`` (file ingestion).

If a future ingestion capability is added, it SHOULD live here — but nothing
may import this package until then.
"""