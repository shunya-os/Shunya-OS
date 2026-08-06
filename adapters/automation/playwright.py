"""Playwright browser automation adapter.

STUB — Playwright is not installed. To use:
    pip install playwright
    playwright install chromium

Calls: playwright.sync_api (navigate, screenshot, evaluate)
"""

from __future__ import annotations

from typing import Any

from adapters import BrowserAdapter


class PlaywrightAdapter(BrowserAdapter):
    """Browser automation via Microsoft Playwright.

    Each method launches an isolated headless Chromium context.
    This is a stub — the real implementation uses
    ``playwright.sync_api.sync_playwright``.
    """

    def navigate(self, url: str) -> str:
        """Navigate to *url* and return the page title."""
        # Real: with sync_playwright() as p:
        #          browser = p.chromium.launch()
        #          page = browser.new_page()
        #          page.goto(url)
        #          title = page.title()
        #          browser.close()
        #          return title
        msg = (
            f"[stub] PlaywrightAdapter.navigate('{url}') "
            f"would launch headless Chromium and return page title"
        )
        print(msg)
        return msg

    def screenshot(self, url: str) -> str:
        """Navigate to *url*, take a screenshot, return path to PNG."""
        # Real: with sync_playwright() as p:
        #          browser = p.chromium.launch()
        #          page = browser.new_page()
        #          page.goto(url)
        #          path = f"/tmp/playwright_{int(time.time())}.png"
        #          page.screenshot(path=path)
        #          browser.close()
        #          return path
        path = f"/tmp/playwright_stub_{hash(url) % 10**8}.png"
        msg = (
            f"[stub] PlaywrightAdapter.screenshot('{url}') "
            f"would save screenshot to {path}"
        )
        print(msg)
        return path

    def execute(self, url: str, script: str) -> Any:
        """Navigate to *url*, run *script* (JS), return result."""
        # Real: with sync_playwright() as p:
        #          browser = p.chromium.launch()
        #          page = browser.new_page()
        #          page.goto(url)
        #          result = page.evaluate(script)
        #          browser.close()
        #          return result
        msg = (
            f"[stub] PlaywrightAdapter.execute('{url}', '{script[:60]}...') "
            f"would evaluate JS in headless Chromium"
        )
        print(msg)
        return {"stub": True, "result": msg}