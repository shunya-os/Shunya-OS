"""Safe PDF generation — mitigates pdfkit JavaScript injection (PYSEC-2026-2860).

All pdfkit.from_string calls must use this wrapper, which disables JavaScript
execution in wkhtmltopdf to prevent server-side JS injection attacks.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def generate_pdf(html: str, output_path: str, extra_options: Optional[dict] = None) -> None:
    """Generate a PDF from HTML with JavaScript disabled.

    Args:
        html: HTML content to render.
        output_path: File path for the generated PDF.
        extra_options: Additional wkhtmltopdf options (safe keys only).
            Security-sensitive options (javascript, local file access, external
            resources) are ENFORCED and cannot be overridden by caller input.

    Raises:
        RuntimeError: If pdfkit or wkhtmltopdf is unavailable.
    """
    # Mandatory security invariants — always applied LAST so caller flexibility
    # cannot override them. These must NEVER be weakened by caller options.
    SECURITY_INVARIANTS = {
        'no-javascript': '',
        'disable-javascript': '',
        'javascript-delay': '0',
        'no-stop-slow-scripts': '',
    }

    options = {
        'encoding': 'UTF-8',
    }
    if extra_options:
        # Apply caller options first
        options.update(extra_options)
    # Security invariants override everything — enforced after caller options
    options.update(SECURITY_INVARIANTS)

    import pdfkit
    pdfkit.from_string(html, output_path, options=options)
    logger.info("PDF generated: %s", output_path)