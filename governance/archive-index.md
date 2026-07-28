# Constitutional Archive Index (DNA-AI-01)

**Status:** Governance — Active  
**Dependency:** SHUNYA Constitution (hierarchy); DNA-01 §18 (Constitutional Archival Policy)  
**Purpose:** Index of all superseded constitutional documents, preserving architectural history.

---

## 1. Archival Rule

Per DNA-01 §18:

- Superseded documents are moved to `docs/architecture/archive/`, preserving exact content, version, and ratification date
- Archived documents are read-only — no edits permitted
- Documents are never deleted
- Documents remain referencable by version number

---

## 2. Archive Contents

### SHUNYA Constitution Layer

| Document | Version | Superseded By | Ratification Date | Archive Path | Notes |
|----------|---------|---------------|-------------------|--------------|-------|
| — | — | — | — | — | No documents archived yet |

### Product Constitution Layer

| Document | Version | Superseded By | Ratification Date | Archive Path | Notes |
|----------|---------|---------------|-------------------|--------------|-------|
| — | — | — | — | — | No documents archived yet |

### Technical Constitution Layer

| Document | Version | Superseded By | Ratification Date | Archive Path | Notes |
|----------|---------|---------------|-------------------|--------------|-------|
| — | — | — | — | — | No documents archived yet |

### Design System Layer

| Document | Version | Superseded By | Ratification Date | Archive Path | Notes |
|----------|---------|---------------|-------------------|--------------|-------|
| — | — | — | — | — | No documents archived yet |

### Implementation Layer

| Document | Version | Superseded By | Ratification Date | Archive Path | Notes |
|----------|---------|---------------|-------------------|--------------|-------|
| — | — | — | — | — | No documents archived yet |

---

## 3. Archive Status

**As of the Constitutional Freeze (2026-07-27), the archive is empty.**

No constitutional documents have been superseded. DNA-01 v2.1 is the founding Technical Constitution. The Product Constitution documents have not yet been drafted. All prior responsive layout conventions were informal — not ratified constitutional documents — and are not eligible for the formal archive.

The first entries will appear when:
- CAP-01 is ratified (first constitutional amendment)
- A new version of any constitutional document supersedes an older one

---

## 4. Archive Directory Structure

When populated, the archive will follow this structure:

```
docs/architecture/archive/
├── shunya-constitution/
├── product-constitution/
│   ├── experience-canon/
│   ├── presence-canon/
│   ├── ai-collaboration-canon/
│   ├── navigation-canon/
│   └── workspace-model/
├── technical-constitution/
│   └── dna-01-*-device-native-architecture.md
├── design-system/
└── implementation/
```

The archive mirrors the source path under an `archive/` prefix.

---

## 5. Archival Procedure

When a document is superseded:

1. Copy the current document to `docs/architecture/archive/<layer>/<filename>-v<version>.md`
2. Verify the copy is byte-identical to the original before modification
3. Update this index with the new entry
4. Only then modify the canonical document

This order ensures the archive always captures the pre-amendment state.

---

## 6. Document History

| Version | Date | Change | Author |
|---------|------|--------|--------|
| 1.0 | 2026-07-27 | Initial creation per Constitutional Freeze directive. Archive is empty — no documents have been superseded yet. | Hermes Agent |
| 2.0 | 2026-07-28 | Revised per DIRECTIVE — DNA-01 RATIFICATION REVISION: updated archive layers to match multi-constitution hierarchy (SHUNYA Constitution, Product Constitution, Technical Constitution) | Hermes Agent |