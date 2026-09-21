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
    # Travel documents. detect_hierarchy() has always special-cased an
    # "itinerary" class, but the classifier had NO signal group for it — so a
    # real travel itinerary was reported as "unknown" while its own hierarchy
    # still said "Itinerary". That contradiction is what these signals close.
    "itinerary": [
        (r"\bitinerary\b", 2.0),
        (r"\bcheck[- ]?in\b", 1.2),
        (r"\bcheck[- ]?out\b", 1.2),
        (r"\bpassenger\b|\bguest\b", 1.0),
        (r"\bflight\b|\bboarding\b|\bdeparture\b|\barrival\b", 1.2),
        (r"\bhotel\b|\breservation\b|\bbooking\b", 1.2),
        (r"\bdestination\b", 1.0),
        (r"\btrip\b|\bvacation\b|\bhoneymoon\b|\bretreat\b", 1.0),
        (r"\bday\s*\d+\b", 0.6),
        (r"\bpassport\b|\bvisa\b", 1.0),
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


def detect_hierarchy(text: str, filename: str = "", file_type: str = "",
                     base_classification: str = "") -> list[str]:
    """Detect a hierarchical document type path from meaning, not folders.

    Examples:
        classify_document -> "itinerary"
        detect_hierarchy -> ["Itinerary", "International", "Bali 4N5D"]

        classify_document -> "invoice"
        detect_hierarchy -> ["Invoice", "Vendor", "Acme Corp"]

    Returns a list of path segments from most general to most specific.
    """
    # Keep the ORIGINAL casing for the extractors: _extract_destination and
    # _extract_vendor match TitleCase patterns ([A-Z][a-z]+), so running them on
    # a lowercased string can never match — which silently disabled destination
    # and vendor naming in every hierarchy. Signals are matched on the
    # lowercased copy only.
    raw_text = (text or "").strip()
    text = raw_text.lower()
    hierarchy: list[str] = []
    cls_label = base_classification or ""

    # ── Itinerary hierarchy ──────────────────────────────────────────
    if cls_label in ("itinerary", "unknown") and _has_travel_signals(text):
        hierarchy.append("Itinerary")

        # Determine scope: International or Domestic
        if _is_international_travel(text, filename):
            hierarchy.append("International")
        elif _is_domestic_travel(text):
            hierarchy.append("Domestic")
        else:
            hierarchy.append("Travel")

        # Extract destination / trip name
        dest = _extract_destination(raw_text)
        if dest:
            hierarchy.append(dest)

    # ── Invoice hierarchy ────────────────────────────────────────────
    elif cls_label in ("invoice",) or _is_invoice_like(text):
        hierarchy.append("Invoice")

        # Detect vendor
        vendor = _extract_vendor(raw_text)
        if vendor:
            hierarchy.append(f"Vendor")
            hierarchy.append(vendor)

    # ── Contract hierarchy ───────────────────────────────────────────
    elif cls_label in ("contract",) or _is_contract_like(text):
        hierarchy.append("Contract")

        contract_type = _detect_contract_type(text)
        hierarchy.append(contract_type)

        # Extract counterparty
        counterparty = _extract_counterparty(text)
        if counterparty:
            hierarchy.append(counterparty)

    # ── Quotation / Proposal hierarchy ───────────────────────────────
    elif cls_label in ("quotation", "proposal"):
        hierarchy.append(cls_label.capitalize())

        client = _extract_client_name(text)
        if client:
            hierarchy.append(client)

    # ── Spreadsheet / CSV hierarchy ──────────────────────────────────
    elif cls_label in ("spreadsheet",):
        hierarchy.append("Spreadsheet")

        sheet_subject = _extract_spreadsheet_subject(text, filename)
        if sheet_subject:
            hierarchy.append(sheet_subject)

    # ── Report hierarchy ─────────────────────────────────────────────
    elif cls_label in ("report",):
        hierarchy.append("Report")

        report_type = _detect_report_type(text)
        hierarchy.append(report_type)

        report_subject = _extract_report_subject(text)
        if report_subject:
            hierarchy.append(report_subject)

    # ── Statement hierarchy ──────────────────────────────────────────
    elif cls_label in ("statement",):
        hierarchy.append("Statement")

        period = _extract_statement_period(text)
        if period:
            hierarchy.append(period)

    # ── Fallback: use extracted signals as hierarchy hints ────────
    if not hierarchy and cls_label:
        hierarchy.append(cls_label.capitalize())

    return hierarchy


# ── Hierarchy helper predicates ────────────────────────────────────


def _has_travel_signals(text: str) -> bool:
    """Check if text has travel/itinerary signals."""
    travel_signals = [
        r"\bcheck[- ]?in\b", r"\bcheck[- ]?out\b",
        r"\bitinerary\b", r"\bflight\b", r"\bbooking\b",
        r"\bhotel\b", r"\bdeparture\b", r"\barrival\b",
        r"\bdestination\b", r"\bpassenger\b", r"\bguest\b",
        r"\broom\b", r"\breservation\b", r"\btrip\b",
        r"\bvacation\b", r"\bhoneymoon\b", r"\bretreat\b",
    ]
    for pat in travel_signals:
        if re.search(pat, text, re.I):
            return True
    return False


def _is_international_travel(text: str, filename: str = "") -> bool:
    """Detect if travel involves international destinations."""
    intl_signals = [
        r"\bpassport\b", r"\bvisa\b", r"\binternational\b",
        r"\b(?:bali|thailand|singapore|dubai|paris|london|tokyo|"
        r"new\s*york|sydney|maldives|switzerland|dubai|phuket|"
        r"kuala\s*lumpur|bangkok|hong\s*kong)\b",
    ]
    for pat in intl_signals:
        if re.search(pat, text, re.I) or re.search(pat, filename, re.I):
            return True
    return False


def _is_domestic_travel(text: str) -> bool:
    """Detect if travel is domestic (within India focus)."""
    domestic_signals = [
        r"\b(?:mumbai|delhi|bangalore|goa|jaipur|chennai|kolkata|"
        r"kerala|manali|shimla|rishikesh|varanasi|agra|udaipur)\b",
    ]
    for pat in domestic_signals:
        if re.search(pat, text, re.I):
            return True
    return False


def _extract_destination(text: str) -> str | None:
    """Extract a destination or trip name from travel text."""
    # Look for "X N" patterns like "Bali 4N5D", "4 Nights 5 Days in Bali"
    m = re.search(
        r"(?:trip\s+(?:to|name)[:\s]+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        r"\s+(\d+\s*[nN]\s*\d*\s*[dD]|\d+\s*[nN]|\d+\s*[dD])",
        text,
    )
    if m:
        dest = m.group(1).strip()[:30]
        duration = m.group(2).strip()
        return f"{dest} {duration}" if dest else None

    # Look for just destination name
    m = re.search(
        r"(?:destination|location|place)[:\s]+([A-Z][a-zA-Z\s]{2,40})",
        text,
    )
    if m:
        return m.group(1).strip()[:40]

    # Known destinations in text
    known = re.search(
        r"\b(Bali|Thailand|Singapore|Dubai|Paris|London|Tokyo|"
        r"New\s+York|Sydney|Maldives|Switzerland|Phuket|"
        r"Mumbai|Goa|Jaipur|Kerala|Manali)\b",
        text,
    )
    if known:
        return known.group(1)

    return None


def _is_invoice_like(text: str) -> bool:
    return bool(re.search(r"\binvoice\b", text, re.I))


def _extract_vendor(text: str) -> str | None:
    m = re.search(r"(?:vendor|supplier|from|company|provider)[:\s]+([A-Z][A-Za-z0-9\s&.]{3,40})", text)
    if m:
        return m.group(1).strip()[:40]
    return None


def _is_contract_like(text: str) -> bool:
    return bool(re.search(r"\b(?:contract|agreement)\b", text, re.I))


def _detect_contract_type(text: str) -> str:
    types = [
        (r"\bservice\b", "Service"),
        (r"\b(?:nda|non.?disclosure|confidentiality)\b", "NDA"),
        (r"\bemploy(?:ee|ment)\b", "Employment"),
        (r"\blemse?\b", "Lease"),
        (r"\bconsult(?:ing|ancy)?\b", "Consulting"),
        (r"\blicens(?:e|ing)\b", "License"),
        (r"\bpartnership\b", "Partnership"),
        (r"\b(?:master\s+)?s(?:ervice\s+)?a(?:greement)?\b", "Service Agreement"),
    ]
    for pat, label in types:
        if re.search(pat, text, re.I):
            return label
    return "General"


def _extract_counterparty(text: str) -> str | None:
    m = re.search(
        r"(?:between|with|party)[:\s]+([A-Z][A-Za-z0-9\s&.]{3,50})",
        text,
    )
    if m:
        return m.group(1).strip()[:50]
    return None


def _extract_client_name(text: str) -> str | None:
    m = re.search(r"(?:client|customer|to)[:\s]+([A-Z][A-Za-z0-9\s&.]{3,50})", text)
    if m:
        return m.group(1).strip()[:50]
    return None


def _extract_spreadsheet_subject(text: str, filename: str = "") -> str | None:
    # First try to infer from filename
    name = filename.rsplit("/", 1)[-1] if "/" in filename else filename
    name = name.rsplit("\\", 1)[-1] if "\\" in name else name
    base = name.rsplit(".", 1)[0] if "." in name else name
    if base and base.lower() not in ("data", "sheet", "export", "report"):
        return base[:40]

    # Try to infer from header row
    lines = text.split("\n")
    if lines:
        header = lines[0].strip()
        if header and len(header) < 200:
            return header[:40]

    return None


def _detect_report_type(text: str) -> str:
    types = [
        (r"\bfinancial\b", "Financial"),
        (r"\bsales\b", "Sales"),
        (r"\bmarket(?:ing|)\b", "Marketing"),
        (r"\bquarter(?:ly)?\b", "Quarterly"),
        (r"\bannual\b", "Annual"),
        (r"\bexpense\b", "Expense"),
        (r"\banalytics?\b", "Analytics"),
    ]
    for pat, label in types:
        if re.search(pat, text, re.I):
            return label
    return "General"


def _extract_report_subject(text: str) -> str | None:
    m = re.search(r"(?:report\s+(?:on|for|of)[:\s]+)?([A-Z][A-Za-z0-9\s&.]{3,50})", text[:500])
    if m:
        subject = m.group(1).strip()[:50]
        if subject.lower() not in ("report", "this report"):
            return subject
    return None


def _extract_statement_period(text: str) -> str | None:
    m = re.search(r"(?:period|for\s+the\s+(?:month|period|quarter|year))[\s:]*(.+?)(?:\n|$)", text)
    if m:
        return m.group(1).strip()[:40]
    return None
