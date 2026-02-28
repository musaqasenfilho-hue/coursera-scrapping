# src/navigator.py
from dataclasses import dataclass
from bs4 import BeautifulSoup
from playwright.async_api import BrowserContext


@dataclass
class ReadingLesson:
    module: str
    lesson_title: str
    url: str


def parse_readings_from_html(html: str, base_url: str) -> list[ReadingLesson]:
    soup = BeautifulSoup(html, "html.parser")
    lessons: list[ReadingLesson] = []

    for module_div in soup.find_all(attrs={"data-testid": "module-item"}):
        heading = module_div.find("h3")
        module_name = heading.get_text(strip=True) if heading else "Unknown Module"

        for item in module_div.find_all(attrs={"data-testid": "lesson-item"}):
            if item.get("data-item-type") != "reading":
                continue
            link = item.find("a")
            if not link:
                continue
            title = link.get_text(strip=True)
            href = link.get("href", "")
            if not href:
                continue
            url = href if href.startswith("http") else base_url + href
            lessons.append(ReadingLesson(module=module_name, lesson_title=title, url=url))

    return lessons


async def get_course_readings(
    context: BrowserContext, course_url: str
) -> tuple[list[ReadingLesson], str]:
    """Navigate to course home and return (readings, course_slug)."""
    page = await context.new_page()
    try:
        await page.goto(course_url, wait_until="networkidle", timeout=30_000)
        html = await page.content()
    finally:
        await page.close()

    # Extract slug from /learn/<slug>/... pattern, fallback to last URL segment
    parts = course_url.rstrip("/").split("/learn/")
    if len(parts) > 1:
        slug = parts[-1].split("/")[0]
    else:
        slug = course_url.rstrip("/").split("/")[-1]

    readings = parse_readings_from_html(html, base_url="https://www.coursera.org")
    return readings, slug
