"""R6B-2.7 Window 6 — Block D: Document Intelligence.

Proves the document identification loop is REAL and deterministic:
  classification from content → entity extraction → persisted result → re-readable.

The classification must never fabricate a confident answer for content that
carries no business-document signal.
"""
import json

import pytest

from app.document.classification import classify_document
from app.document.intelligence import analyse_document, read_intelligence


# ── Classification ──────────────────────────────────────────────────────


def test_invoice_is_identified():
    text = (
        "INVOICE\nInvoice No: INV-7781\nBill To: Acme Ltd\n"
        "Subtotal 1000\nTax 180\nAmount Due 1180\nDue Date: 2026-10-01\n"
    )
    r = classify_document(text, filename="inv.pdf", file_type="pdf")
    assert r["classification"] == "invoice"
    assert r["confidence"] > 0.3
    assert r["signals"]


def test_contract_is_identified():
    text = (
        "EMPLOYMENT AGREEMENT\nThis contract is entered into between the parties "
        "of the first part and the second part. Governing law shall apply. "
        "Termination clause: 30 days notice. Witness signature below."
    )
    r = classify_document(text, filename="agreement.pdf")
    assert r["classification"] == "contract"


def test_emptiness_is_unknown_not_a_guess():
    r = classify_document("", filename="mystery.bin")
    assert r["classification"] == "unknown"
    assert r["confidence"] == 0.0


def test_weak_signals_do_not_produce_false_certainty():
    # A single incidental word must not yield a confident identification.
    r = classify_document("total", filename="x.txt")
    assert r["classification"] == "unknown"
    assert r["confidence"] < 0.6


def test_classification_is_deterministic():
    text = "QUOTATION\nValidity until Dec 2026. Unit price 500. Estimate only."
    a = classify_document(text, filename="q.pdf")
    b = classify_document(text, filename="q.pdf")
    assert a == b


# ── Persistence ─────────────────────────────────────────────────────────


class _FakeDoc:
    def __init__(self, text, filename="doc.txt", file_type="text"):
        self.id = 1
        self.extracted_text = text
        self.filename = filename
        self.file_type = file_type
        self.classification = "ingested"
        self.structured_data = ""


def test_analyse_persists_classification_and_entities():
    doc = _FakeDoc(
        "INVOICE\nInvoice No: INV7781\nBill To: Acme Ltd\nAmount Due $5,000\n"
        "Contact: billing@acme.example  Due Date: 2026-11-01\n"
    )
    intel = analyse_document(doc, persist=True)

    # persisted on the record
    assert doc.classification == "invoice"
    stored = json.loads(doc.structured_data)
    assert stored["intelligence"]["classification"] == "invoice"

    # entities extracted with provenance-bearing values
    assert intel["entity_count"] >= 1
    assert "amounts" in intel["entities"]
    assert any("acme.example" in e["value"] for e in intel["entities"].get("emails", []))
    assert "references" in intel["entities"]


def test_read_intelligence_round_trips():
    doc = _FakeDoc("REPORT\nExecutive Summary\nFindings: revenue grew.\nConclusion: fine.")
    analyse_document(doc, persist=True)
    got = read_intelligence(doc)
    assert got is not None
    assert got["classification"] == "report"
    assert got["engine"].startswith("document_intelligence")


def test_read_intelligence_none_when_unanalysed():
    doc = _FakeDoc("some text", filename="plain.txt")
    assert read_intelligence(doc) is None


def test_analyse_never_raises_on_weird_text():
    doc = _FakeDoc("\x00\x01 binary-ish \uffff content")
    intel = analyse_document(doc, persist=True)
    assert "classification" in intel
