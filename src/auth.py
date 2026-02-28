# src/auth.py
import json
import logging
from pathlib import Path
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

SESSION_FILE = Path("session.json")


async def login(email: str, password: str, headless: bool = True) -> tuple:
    """
    Login to Coursera and return (playwright, browser, context).
    If session.json exists, loads saved cookies (skips login form).
    Caller is responsible for closing playwright/browser.
    """
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        )
    )

    if SESSION_FILE.exists():
        logger.info("Loading saved session from session.json...")
        state = json.loads(SESSION_FILE.read_text())
        await context.add_cookies(state["cookies"])
        return playwright, browser, context

    # No session file — do browser login
    logger.info("No session.json found. Attempting browser login...")
    page = await context.new_page()
    await page.goto("https://www.coursera.org/?authMode=login", wait_until="networkidle", timeout=30_000)

    await page.wait_for_selector('input[name="email"]', timeout=15_000)
    await page.fill('input[name="email"]', email)
    await page.click('button:has-text("Continue")', timeout=10_000)

    await page.wait_for_selector('input[name="password"]', timeout=15_000)
    await page.fill('input[name="password"]', password)
    await page.press('input[name="password"]', "Enter")

    await page.wait_for_url(
        lambda url: "accounts.coursera.org" not in url and "authMode" not in url,
        timeout=30_000
    )
    logger.info(f"Logged in. Saving session to {SESSION_FILE}...")
    state = await context.storage_state()
    SESSION_FILE.write_text(json.dumps(state))
    await page.close()

    return playwright, browser, context
