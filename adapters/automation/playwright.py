"""Playwright browser automation adapter.

Uses ``playwright.sync_api`` when the ``playwright`` package is installed.
Falls back to a comprehensive stub that logs what it would do.

To install Playwright::

    pip install playwright
    playwright install chromium
"""

from __future__ import annotations

import logging
import time
from typing import Any

from adapters import BrowserAdapter

logger = logging.getLogger(__name__)


class PlaywrightAdapter(BrowserAdapter):
    """Browser automation via Microsoft Playwright.

    Each method launches an isolated headless Chromium context.
    Falls back to a detailed stub when Playwright is not installed.
    """

    _playwright_available: bool | None = None  # class-level cache

    @classmethod
    def check_playwright(cls) -> bool:
        """Check if the ``playwright`` module is importable.

        Results are cached on the class after first check.
        """
        if cls._playwright_available is not None:
            return cls._playwright_available

        try:
            import playwright  # noqa: F401
            cls._playwright_available = True
            logger.info("Playwright is available — using real browser automation")
        except ImportError:
            cls._playwright_available = False
            logger.warning(
                "Playwright not installed — using stub. "
                "Install with: pip install playwright && playwright install chromium"
            )
        return cls._playwright_available

    # ------------------------------------------------------------------
    # BrowserAdapter interface
    # ------------------------------------------------------------------

    def navigate(self, url: str) -> str:
        """Navigate to *url* and return the page title."""
        if self.check_playwright():
            return self._real_navigate(url)
        return self._stub_navigate(url)

    def screenshot(self, url: str) -> str:
        """Navigate to *url*, take a screenshot, return path to PNG."""
        if self.check_playwright():
            return self._real_screenshot(url)
        return self._stub_screenshot(url)

    def execute(self, url: str, script: str) -> Any:
        """Navigate to *url*, run *script* (JS), return result."""
        if self.check_playwright():
            return self._real_execute(url, script)
        return self._stub_execute(url, script)

    # ------------------------------------------------------------------
    # Real Playwright implementations
    # ------------------------------------------------------------------

    @staticmethod
    def _real_navigate(url: str) -> str:
        """Actual Playwright navigation."""
        from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")
            title = page.title()
            browser.close()
        logger.info("Playwright navigated to %s — title: %s", url, title)
        return title

    @staticmethod
    def _real_screenshot(url: str) -> str:
        """Actual Playwright screenshot."""
        from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]

        path = f"/tmp/playwright_{int(time.time())}_{hash(url) % 10**6}.png"
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.goto(url, wait_until="networkidle")
            page.screenshot(path=path, full_page=False)
            browser.close()
        logger.info("Playwright screenshot saved to %s", path)
        return path

    @staticmethod
    def _real_execute(url: str, script: str) -> Any:
        """Actual Playwright JavaScript execution."""
        from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")
            result = page.evaluate(script)
            browser.close()
        logger.info("Playwright executed script on %s", url)
        return result

    # ------------------------------------------------------------------
    # Stub implementations
    # ------------------------------------------------------------------

    @staticmethod
    def _stub_navigate(url: str) -> str:
        """Stub: log what would happen."""
        msg = (
            f"[stub] PlaywrightAdapter.navigate('{url}') "
            f"would launch headless Chromium and return page title"
        )
        logger.warning(msg)
        print(msg)
        return msg

    @staticmethod
    def _stub_screenshot(url: str) -> str:
        """Stub: log what would happen."""
        path = f"/tmp/playwright_stub_{hash(url) % 10**8}.png"
        msg = (
            f"[stub] PlaywrightAdapter.screenshot('{url}') "
            f"would save screenshot to {path}"
        )
        logger.warning(msg)
        print(msg)
        return path

    @staticmethod
    def _stub_execute(url: str, script: str) -> Any:
        """Stub: log what would happen."""
        msg = (
            f"[stub] PlaywrightAdapter.execute('{url}', '{script[:80]}...') "
            f"would evaluate JS in headless Chromium"
        )
        logger.warning(msg)
        print(msg)
        return {"stub": True, "result": msg}

    def __repr__(self) -> str:
        available = self.check_playwright()
        return f"PlaywrightAdapter(real_playwright={available})"