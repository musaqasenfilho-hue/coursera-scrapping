# src/extractor.py
import asyncio
import logging
from typing import Optional
from playwright.async_api import BrowserContext, Response

logger = logging.getLogger(__name__)

READING_API_PATTERNS = [
    "onDemandLectureAssets.v1",
    "onDemandElements.v1",
    "onDemandSupplements.v1",
]


def extract_html_from_response(data: dict) -> Optional[str]:
    """Parse Coursera API JSON and extract HTML content field."""
    try:
        for elem in data.get("elements", []):
            defn = elem.get("definition", {}).get("value", {})
            html = defn.get("html")
            if html:
                return html
    except (AttributeError, TypeError):
        pass
    return None


async def extract_reading_content(
    context: BrowserContext,
    lesson_url: str,
    timeout: float = 15.0,
    retry: int = 2,
) -> Optional[str]:
    """
    Navigate to a reading lesson URL and intercept the API response
    that contains the reading HTML content.
    Returns the HTML string or None if not found after retries.
    """
    for attempt in range(retry + 1):
        captured: list[str] = []
        page = await context.new_page()

        async def handle_response(response: Response):
            if any(p in response.url for p in READING_API_PATTERNS):
                try:
                    body = await response.json()
                    html = extract_html_from_response(body)
                    if html:
                        captured.append(html)
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            await page.goto(lesson_url, wait_until="networkidle", timeout=30_000)
            await asyncio.sleep(2)
        except Exception as e:
            logger.warning(f"Navigation error on attempt {attempt + 1}: {e}")
        finally:
            await page.close()

        if captured:
            return captured[0]

        if attempt < retry:
            logger.info(f"Retrying {lesson_url} (attempt {attempt + 2})")
            await asyncio.sleep(3)

    logger.warning(f"Could not extract content from {lesson_url}")
    return None
