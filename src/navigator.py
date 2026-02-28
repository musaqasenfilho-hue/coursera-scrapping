# src/navigator.py
import logging
from dataclasses import dataclass
from bs4 import BeautifulSoup
from playwright.async_api import BrowserContext

logger = logging.getLogger(__name__)

BASE_URL = "https://www.coursera.org"


@dataclass
class ReadingLesson:
    module: str
    lesson_title: str
    url: str


def parse_module_page(html: str, base_url: str = BASE_URL) -> tuple[str, list[ReadingLesson]]:
    """Parse a single module page. Returns (module_name, reading_lessons)."""
    soup = BeautifulSoup(html, "html.parser")

    # Module name: h2 inside rc-periodPage (strip nested badge elements)
    module_name = "Unknown Module"
    period_page = soup.find(attrs={"data-test": "rc-periodPage"})
    if period_page:
        h2 = period_page.find("h2")
        if h2:
            for badge in h2.find_all(["h4", "span"]):
                if badge.find_parent("h2") == h2 and badge.name in ("h4",):
                    badge.decompose()
            module_name = h2.get_text(strip=True)

    # Reading items: supplement display items
    lessons: list[ReadingLesson] = []
    for item in soup.find_all(attrs={"data-test": "WeekSingleItemDisplay-supplement"}):
        name_el = item.find(attrs={"data-test": "rc-ItemName"})
        if not name_el:
            continue
        title = name_el.get_text(strip=True)
        a = item.find("a")
        if not a:
            continue
        href = a.get("href", "")
        if not href:
            continue
        url = href if href.startswith("http") else base_url + href
        lessons.append(ReadingLesson(module=module_name, lesson_title=title, url=url))

    return module_name, lessons


async def get_course_readings(
    context: BrowserContext, course_url: str
) -> tuple[list[ReadingLesson], str]:
    """Navigate to course home, visit each module, and return (readings, course_slug)."""
    # Extract slug from /learn/<slug>/... pattern
    parts = course_url.rstrip("/").split("/learn/")
    slug = parts[-1].split("/")[0] if len(parts) > 1 else course_url.rstrip("/").split("/")[-1]

    # Visit the course home page to discover module links
    page = await context.new_page()
    try:
        await page.goto(course_url, wait_until="networkidle", timeout=30_000)
        home_html = await page.content()
    finally:
        await page.close()

    soup = BeautifulSoup(home_html, "html.parser")
    module_hrefs = [
        item.get("href", "")
        for item in soup.find_all(attrs={"data-testid": "rc-WeekNavigationItem"})
        if item.get("href", "")
    ]

    if not module_hrefs:
        logger.warning("No module links found on course home page; parsing home page directly.")
        _, readings = parse_module_page(home_html)
        return readings, slug

    # Visit each module page and collect reading lessons
    all_readings: list[ReadingLesson] = []
    for href in module_hrefs:
        module_url = href if href.startswith("http") else BASE_URL + href
        page = await context.new_page()
        try:
            await page.goto(module_url, wait_until="networkidle", timeout=30_000)
            module_html = await page.content()
        finally:
            await page.close()
        _, readings = parse_module_page(module_html)
        logger.info("Module %s: found %d reading(s)", module_url, len(readings))
        all_readings.extend(readings)

    return all_readings, slug
