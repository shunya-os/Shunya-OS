"""SHUNYA — Document Identification & Classification.

The first real document intelligence step: given a document's extracted text,
identify what kind of business document it is.

Design constraints (R6B-2.7 Window 6, Block D):
  • Business-agnostic — the SHUNYA model must not assume a vertical.
  • Deterministic and explainable — every classification carries the signals
    that produced it, so the user can see WHY. No fabrication.
  • Company data first — classification is computed from the document's own
    extracted text. No external/internet retrieval is performed here.
  • Truthful — an unclassifiable document returns UNKNOWN with confidence 0,
    never a confident guess.

This module only IDENTIFIES. It does not mutate anything; the caller persists
the returned result.
"""
from __future__ import annotations

import re
from typing import Any

from app.document.models import DocumentClassification

# ---------------------------------------------------------------------------
# Signal vocabulary — weighted keyword groups per document class.
# Patterns are matched case-insensitively against the extracted text.
# ---------------------------------------------------------------------------

_SIGNALS: dict[str, list[tuple[str, float]]] = {
    # NOTE: "invoice" is a canonical business-document class used by SHUNYA's
    # document intelligence even though it is not part of DocumentClassification
    # (the DB column is a free string, and invoices are a distinct real type).
    "invoice": [
        (r"\binvoice\b", 2.0),
        (r"\binvoice\s*(no|number|#)", 2.0),
        (r"\bbill\s*to\b", 1.5),
        (r"\bamount\s*due\b", 2.0),
        (r"\bsubtotal\b", 1.5),
        (r"\btax\b|\bgst\b|\bvat\b", 1.0),
        (r"\bpayment\s*terms\b", 1.0),
        (r"\bdue\s*date\b", 1.0),
    ],
    "quotation": [
        (r"\bquotation\b|\bquote\b", 2.0),
        (r"\bproposal\s*(no|number|#)?\b", 1.0),
        (r"\bvalid(ity)?\s*(until|for|till)\b", 1.5),
        (r"\bunit\s*price\b", 1.5),
        (r"\bestimate\b", 1.0),
        (r"\boffer\b", 0.8),
    ],
    DocumentClassification.CONTRACT: [
        (r"\bcontract\b", 2.0),
        (r"\bagreement\b", 1.8),
        (r"\bhereby\b", 1.5),
        (r"\bparty\s+of\s+the\s+first\s+part\b|\bparties\b", 1.5),
        (r"\bterm(ination)?\s+clause\b|\btermination\b", 1.2),
        (r"\bgoverning\s+law\b", 1.5),
        (r"\bsignatory\b|\bwitness\b", 1.0),
        (r"\bclause\b", 1.0),
    ],
    DocumentClassification.STATEMENT: [
        (r"\bstatement\b", 2.0),
        (r"\baccount\s*(no|number|#)\b", 1.5),
        (r"\bopening\s*balance\b", 2.0),
        (r"\bclosing\s*balance\b", 2.0),
        (r"\btransactions?\b", 1.2),
        (r"\bdebit\b|\bcredit\b", 1.2),
    ],
    DocumentClassification.PROPOSAL: [
        (r"\bproposal\b", 2.0),
        (r"\bscope\s+of\s+work\b", 1.5),
        (r"\bdeliverables?\b", 1.2),
        (r"\bwe\s+propose\b|\bour\s+approach\b", 1.2),
        (r"\btimeline\b|\bmilestones?\b", 1.0),
    ],
    DocumentClassification.REPORT: [
        (r"\breport\b", 1.5),
        (r"\bexecutive\s+summary\b", 2.0),
        (r"\bfindings?\b", 1.2),
        (r"\bconclusion\b", 1.0),
        (r"\bmethodology\b", 1.2),
        (r"\bquarter(ly)?\b|\bannual\b", 0.8),
    ],
    DocumentClassification.POLICY: [
        (r"\bpolicy\b", 2.0),
        (r"\bcompliance\b", 1.2),
        (r"\bguidelines?\b", 1.2),
        (r"\bprocedures?\b", 1.0),
        (r"\bshall\s+not\b|\bmust\s+not\b", 1.0),
    ],
    DocumentClassification.FORM: [
        (r"\bform\b", 1.5),
        (r"\bfill\s+(in|out)\b", 1.0),
        (r"_{4,}", 1.5),
        (r"\bapplicant\b|\bsignature\s*:?\s*_{0,}", 1.0),
        (r"\bdate\s*:\s*_{2,}", 1.2),
    ],
    DocumentClassification.SPREADSHEET: [
        (r"\brow\s*\d+\b", 1.0),
        (r"\bcolumn\b", 1.0),
        (r"\bsheet\b", 1.2),
        (r"\btotal\b", 0.6),
    ],
    DocumentClassification.PRESENTATION: [
        (r"\bslide\s*\d+\b", 2.0),
        (r"\bagenda\b", 1.0),
        (r"\btakeaways?\b", 1.0),
    ],
    DocumentClassification.CIRCULAR: [
        (r"\bcircular\b", 2.5),
        (r"\bnotice\s+to\s+all\b", 1.5),
        (r"\bthis\s+is\s+to\s+inform\b", 1.2),
    ],
    DocumentClassification.CORRESPONDENCE_ATTACHMENT: [
        (r"\bdear\s+(sir|madam|mr|ms|mrs)\b", 1.5),
        (r"\bregards\b|\bsincerely\b|\byours\s+faithfully\b", 1.2),
        (r"\bre:\s", 1.2),
        (r"\bplease\s+find\s+attached\b", 2.0),
    ],
}

# Document type inferred from the file extension (a supporting signal).
_EXT_TYPE = {
    "xlsx": DocumentClassification.SPREADSHEET,
    "csv": DocumentClassification.SPREADSHEET,
    "pptx": DocumentClassification.PRESENTATION,
}


def classify_document(text: str, filename: str = "", file_type: str = "") -> dict[str, Any]:
    """Identify the document class from its extracted text.

    Returns a dict:
        classification : one of DocumentClassification values
        confidence     : 0.0–1.0
        reason         : human-readable explanation
        signals        : the matched signals that drove the decision
    """
    text = (text or "").strip()
    scores: dict[str, float] = {}
    matched: dict[str, list[str]] = {}

    for cls, patterns in _SIGNALS.items():
        for pattern, weight in patterns:
            m = re.search(pattern, text, re.I)
            if m:
                scores[cls] = scores.get(cls, 0.0) + weight
                matched.setdefault(cls, []).append(m.group(0).strip()[:40])

    # File-extension support — a weak prior, never decisive on its own.
    ext = (file_type or "").lower().lstrip(".") or filename.rsplit(".", 1)[-1].lower() if "." in filename else (file_type or "").lower()
    ext_cls = _EXT_TYPE.get(ext)
    if ext_cls:
        scores[ext_cls] = scores.get(ext_cls, 0.0) + 0.5
        matched.setdefault(ext_cls, []).append(f"file:{ext}")

    if not scores or max(scores.values()) <= 0:
        return {
            "classification": DocumentClassification.UNKNOWN,
            "confidence": 0.0,
            "reason": "No recognised business-document signals were found in the content.",
            "signals": [],
        }

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_cls, top_score = ranked[0]
    total = sum(scores.values())
    # Confidence: share of the winning class, scaled so a single strong signal
    # does not masquerade as certainty.
    share = top_score / total if total else 0.0
    confidence = round(min(0.95, 0.35 + 0.6 * share) * min(1.0, top_score / 3.0), 2)

    if confidence < 0.3:
        return {
            "classification": DocumentClassification.UNKNOWN,
            "confidence": confidence,
            "reason": "Signals were too weak to identify this document confidently.",
            "signals": matched.get(top_cls, [])[:6],
        }

    return {
        "classification": top_cls,
        "confidence": confidence,
        "reason": f"Identified as '{top_cls}' from {len(matched.get(top_cls, []))} content signal(s).",
        "signals": matched.get(top_cls, [])[:6],
    }
