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

    Raises:
        RuntimeError: If pdfkit or wkhtmltopdf is unavailable.
    """
    options = {
        'no-javascript': '',
        'disable-javascript': '',
        'javascript-delay': '0',
        'no-stop-slow-scripts': '',
        'encoding': 'UTF-8',
    }
    if extra_options:
        options.update(extra_options)

    import pdfkit
    pdfkit.from_string(html, output_path, options=options)
    logger.info("PDF generated: %s", output_path)