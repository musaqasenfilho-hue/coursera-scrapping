# src/auth.py
from playwright.async_api import async_playwright


async def login(email: str, password: str, headless: bool = False) -> tuple:
    """
    Login to Coursera and return (playwright, browser, context).
    Caller is responsible for closing all three.
    headless=False so user can handle 2FA or captcha if needed.
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
    page = await context.new_page()

    await page.goto("https://www.coursera.org/")
    await page.click('[data-testid="header-login-button"]', timeout=10_000)
    await page.fill('[name="email"]', email)
    await page.click('[data-testid="email-next-button"]', timeout=5_000)
    await page.fill('[name="password"]', password)
    await page.click('[data-testid="signin-btn"]', timeout=5_000)
    await page.wait_for_url(
        lambda url: "accounts.coursera.org" not in url, timeout=30_000
    )
    await page.close()

    return playwright, browser, context
