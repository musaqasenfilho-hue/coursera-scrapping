# main.py
import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from src.auth import login
from src.navigator import get_course_readings
from src.extractor import extract_reading_content
from src.converter import html_to_sections
from src.writer import write_csv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DELAY_BETWEEN_LESSONS = float(os.getenv("SCRAPE_DELAY", "2"))


async def run(course_url: str):
    email = os.getenv("COURSERA_EMAIL")
    password = os.getenv("COURSERA_PASSWORD")
    if not email or not password:
        logger.error("Missing COURSERA_EMAIL or COURSERA_PASSWORD in environment / .env file")
        sys.exit(1)

    logger.info("Logging into Coursera...")
    playwright, browser, context = await login(email, password, headless=False)

    try:
        logger.info(f"Fetching course structure from {course_url}")
        readings, course_slug = await get_course_readings(context, course_url)

        if not readings:
            logger.warning("No Reading lessons found in this course.")
            return

        logger.info(f"Found {len(readings)} Reading lessons. Starting extraction...")

        for i, lesson in enumerate(readings, 1):
            logger.info(f"[{i}/{len(readings)}] {lesson.module} → {lesson.lesson_title}")
            html = await extract_reading_content(context, lesson.url)

            if html is None:
                logger.warning(f"  Skipping — could not extract content.")
                continue

            sections = html_to_sections(html, lesson_title=lesson.lesson_title)
            path = write_csv(
                course_slug=course_slug,
                module=lesson.module,
                lesson_title=lesson.lesson_title,
                sections=sections,
            )
            logger.info(f"  Saved → {path}")

            if i < len(readings):
                await asyncio.sleep(DELAY_BETWEEN_LESSONS)

    finally:
        await browser.close()
        await playwright.stop()

    logger.info("Done.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <COURSE_URL>")
        sys.exit(1)
    asyncio.run(run(sys.argv[1]))
