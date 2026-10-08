"""Upstream-refusal probe for the live DuckDuckGo dependency.

Shared by the live web-search tests (test_universal_research.py,
test_connector_certification.py) so they can distinguish an EXTERNAL upstream
refusal (datacenter-IP rate limit / bot wall — observed from GitHub Actions
runners: the raw upstream raises "No results found.") from a PRODUCT defect in
the canonical provider.

Contract:
  * None when the upstream serves items — a canonical provider that then
    returns nothing is a product defect, so the test must FAIL;
  * a reason string when the upstream itself is refusing — the test must SKIP
    with that reason (no SHUNYA code change can satisfy the assertion);
  * None when the ddgs dependency is missing — that is a product/config
    problem, so the test must FAIL, never excuse it.
"""


def ddg_upstream_refusal_reason() -> str | None:
    """Return a reason string when DuckDuckGo itself is refusing this network."""
    try:
        from ddgs import DDGS
    except ImportError:  # dependency missing is a product problem — do not excuse it
        return None
    try:
        with DDGS() as ddgs:
            items = list(ddgs.text("test", max_results=1))
        if not items:
            return "raw ddgs probe returned no items"
        return None  # upstream served — the provider must work
    except Exception as e:  # DDGSException('No results found.'), rate limits, timeouts
        return f"{type(e).__name__}: {e}"
