"""
Panchi Club Travel OS — AI Document Reading (Unit 10)

Extracts text from PDFs, DOCX, images, and plain text files.
Classifies documents and extracts structured lead info.
All methods have try/except fallbacks — missing dependencies return empty/graceful results.
"""

import os
import re
import json
from typing import Optional


class DocumentReader:
    """AI-powered document reader for Panchi Club.

    Supports PDF, DOCX, image (OCR), and plain text extraction.
    Classifies documents and extracts structured lead information.
    """

    # ── Text Extraction ────────────────────────────────────────────────

    def extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text from a document file.

        Args:
            file_path: Absolute path to the file.
            file_type: One of 'pdf', 'docx', 'image', 'text'.

        Returns:
            Extracted text string, or empty string on failure.
        """
        if not os.path.exists(file_path):
            return ""

        extractors = {
            "pdf": self._extract_pdf,
            "docx": self._extract_docx,
            "image": self._extract_image,
            "text": self._extract_text,
        }

        handler = extractors.get(file_type, self._extract_text)
        try:
            return handler(file_path) or ""
        except Exception:
            return ""

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF. Try PyMuPDF first, fallback to pdfplumber, then raw."""
        text = ""
        # Try PyMuPDF (fitz)
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
            if text.strip():
                return text.strip()
        except ImportError:
            pass
        except Exception:
            pass

        # Try pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    text += page_text + "\n"
            if text.strip():
                return text.strip()
        except ImportError:
            pass
        except Exception:
            pass

        # Fallback: read raw bytes, extract any printable text
        try:
            with open(file_path, "rb") as f:
                raw = f.read()
            # Extract ASCII printable strings
            strings = re.findall(rb"[\x20-\x7E]{4,}", raw)
            text = "\n".join(s.decode("ascii", errors="ignore") for s in strings)
            return text.strip()
        except Exception:
            return ""

    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX using python-docx."""
        try:
            import docx
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs]
            return "\n".join(paragraphs).strip()
        except ImportError:
            return ""
        except Exception:
            return ""

    def _extract_image(self, file_path: str) -> str:
        """Extract text from image using pytesseract OCR."""
        try:
            from PIL import Image
            import pytesseract
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)
            return text.strip()
        except ImportError:
            return ""
        except Exception:
            return ""

    def _extract_text(self, file_path: str) -> str:
        """Read plain text file."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read().strip()
        except Exception:
            return ""

    # ── Lead Info Extraction ───────────────────────────────────────────

    def extract_lead_info(self, text: str) -> dict:
        """Extract structured lead info from document text using parse_inquiry_text.

        Returns:
            dict with keys: destination, nights, adults, kids, dates, name, budget, occasion
            plus any additional fields parsed from the text.
        """
        if not text or not text.strip():
            return {}

        result = {}
        try:
            from app.services import parse_inquiry_text
            parsed = parse_inquiry_text(text)
            result.update(parsed)
        except ImportError:
            pass
        except Exception:
            pass

        # Additional extraction beyond travel inquiry parser
        # Try to find email addresses
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if emails:
            result["emails"] = emails

        # Try to find phone numbers (Indian + international)
        phones = re.findall(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
        if phones:
            result["phones"] = phones

        # Try to find monetary amounts
        amounts = re.findall(r"(?:₹|Rs\.?|INR|USD|EUR|£)\s*\.?\s*(\d[\d,]*\.?\d*)", text, re.I)
        if amounts:
            result["amounts"] = [a.replace(",", "") for a in amounts]

        # Try to find dates
        date_patterns = re.findall(
            r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{2,4}",
            text, re.I
        )
        if date_patterns:
            result["dates_found"] = date_patterns

        # Try to find reference/ID numbers
        refs = re.findall(r"(?:Ref|ID|No|Ticket|Booking|PNR)[.\s:#]*([A-Z0-9]{4,20})", text, re.I)
        if refs:
            result["reference_numbers"] = refs

        return result

    # ── Summarization ──────────────────────────────────────────────────

    def summarize_document(self, text: str, max_length: int = 500) -> str:
        """Truncate/summarize document text to max_length characters.

        Tries to break at sentence boundaries for clean truncation.
        """
        if not text:
            return ""
        if len(text) <= max_length:
            return text.strip()

        # Try to truncate at sentence boundary
        truncated = text[:max_length]
        # Find last sentence-ending punctuation
        for sep in (". ", "! ", "? ", ".\n", "!\n", "?\n"):
            last = truncated.rfind(sep)
            if last > max_length // 2:
                return truncated[: last + 1].strip()

        # Fallback: truncate at last space
        last_space = truncated.rfind(" ")
        if last_space > 0:
            return truncated[:last_space].strip() + "…"
        return truncated.strip() + "…"

    # ── Classification ─────────────────────────────────────────────────

    def classify_document(self, text: str) -> str:
        """Classify a document based on its text content.

        Returns one of: invoice, itinerary, passport_copy, id_proof, booking_confirmation, other
        """
        if not text or not text.strip():
            return "other"

        lower = text.lower()

        # Invoice detection
        invoice_score = 0
        if re.search(r"(?:invoice|tax\s*(?:invoice|receipt)|bill\s*(?:to|no)|gst\s*(?:in|number)|tax\s*amount)", lower):
            invoice_score += 3
        if re.search(r"(?:total|subtotal|grand\s*total|amount\s*due|due\s*date|payment\s*terms)", lower):
            invoice_score += 2
        if re.search(r"(?:₹\s*\d+|rs\.?\s*\d+|inr\s*\d+)", lower):
            invoice_score += 1
        if re.search(r"(?:invoice\s*#|inv\s*no|invoice\s*number)", lower):
            invoice_score += 2
        if invoice_score >= 4:
            return "invoice"

        # Itinerary / travel plan detection
        itinerary_score = 0
        if re.search(r"(?:itinerary|travel\s*plan|trip\s*summary|day\s*\d+|day\s*plan)", lower):
            itinerary_score += 3
        if re.search(r"(?:flight|hotel|check[-\s]in|check[-\s]out|departure|arrival|boarding)", lower):
            itinerary_score += 2
        if re.search(r"(?:destination|tour|sightseeing| excursion|transfer)", lower):
            itinerary_score += 1
        if itinerary_score >= 4:
            return "itinerary"

        # Passport detection
        passport_score = 0
        if re.search(r"(?:passport|passport\s*no|passport\s*number|type\s*[pP])", lower):
            passport_score += 3
        if re.search(r"(?:given\s*names|surname|date\s*of\s*birth|place\s*of\s*birth|nationality|sex\s*[MF])", lower):
            passport_score += 2
        if re.search(r"(?:passport\s*expiry|date\s*of\s*issue|authority)", lower):
            passport_score += 1
        if passport_score >= 4:
            return "passport_copy"

        # ID proof detection
        id_score = 0
        if re.search(r"(?:aadhaar|aadhar|voter|driving\s*license|pan\s*card|identity\s*card|id\s*proof)", lower):
            id_score += 3
        if re.search(r"(?:date\s*of\s*birth|father|mother|spouse|address|gender|photo)", lower):
            id_score += 1
        if id_score >= 3:
            return "id_proof"

        # Booking confirmation detection
        booking_score = 0
        if re.search(r"(?:booking\s*(?:confirmation|reference|no|id|number)|confirmation\s*number|pnr|ticket\s*(?:no|number|#))", lower):
            booking_score += 3
        if re.search(r"(?:booked|confirmed|reservation|ticket\s*no|e[-\s]?ticket)", lower):
            booking_score += 2
        if re.search(r"(?:flight|hotel|room|train|bus)", lower) and re.search(r"(?:date|time|check[-\s]in)", lower):
            booking_score += 1
        if booking_score >= 4:
            return "booking_confirmation"

        return "other"

    # ── Convenience ────────────────────────────────────────────────────

    def process_document(self, file_path: str, file_type: str) -> dict:
        """Full pipeline: extract, classify, summarize, extract lead info.

        Returns:
            dict with keys: extracted_text, classification, summary, structured_data
        """
        text = self.extract_text(file_path, file_type)
        classification = self.classify_document(text)
        summary = self.summarize_document(text)
        lead_info = self.extract_lead_info(text)

        return {
            "extracted_text": text,
            "classification": classification,
            "summary": summary,
            "structured_data": lead_info,
        }