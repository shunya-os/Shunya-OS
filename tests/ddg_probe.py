"""Live-DuckDuckGo helpers shared by the web-search test files.

The upstream intermittently refuses INDIVIDUAL requests from datacenter IPs
(GitHub runners): run 37807894159 refused the canonical call ("No results
found.") while a raw probe of the same upstream served seconds later. These
helpers distinguish that external flakiness from a PRODUCT defect in the
canonical provider:

  * ``live_search_with_retries`` — the canonical provider called with bounded
    retries (an intermittent refusal is retried, not excused);
  * ``raw_search_attempts``     — the raw ddgs upstream probed with the SAME
    query. Only when it demonstrably serves that exact query (>= 2 successful
    attempts) while the provider returned nothing after its retries is the
    empty result a product defect and the test must FAIL. When the upstream
    itself refuses too, the test must SKIP with the reason.

A missing ddgs dependency is a product/config problem (counted as 0 successes
with an explicit error, so the live test FAILS rather than skips).
"""
import time


def live_search_with_retries(provider, query: str, max_results: int = 3,
                             attempts: int = 3) -> list:
    """Canonical provider search with bounded retries for a flaky upstream."""
    results: list = []
    for index in range(attempts):
        results = provider.search(query, max_results=max_results)
        if results:
            return results
        if index < attempts - 1:
            time.sleep(1.0 + index)
    return results


def raw_search_attempts(query: str, max_results: int = 3, attempts: int = 3):
    """Raw ddgs attempts for the SAME query.

    Returns ``(successes, items, last_error)`` where ``successes`` counts
    attempts that returned items.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        return 0, [], "ddgs not installed (product defect — do not excuse)"
    successes: int = 0
    items: list = []
    last_error = None
    for index in range(attempts):
        try:
            with DDGS() as ddgs:
                items = list(ddgs.text(query, max_results=max_results))
            if items:
                successes += 1
            else:
                last_error = "raw ddgs returned no items"
        except Exception as e:  # DDGSException('No results found.'), rate limits
            last_error = f"{type(e).__name__}: {e}"
        if index < attempts - 1:
            time.sleep(1.0 + index)
    return successes, items, last_error
