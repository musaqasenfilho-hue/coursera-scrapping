# Coursera Reading Scraper Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** CLI tool that logs into Coursera, traverses all modules of a course, and saves every Reading lesson as a Markdown-structured CSV file.

**Architecture:** Playwright authenticates and navigates the course; a response interceptor captures the internal JSON API calls that deliver reading content; converter transforms HTML→Markdown split by headings; writer produces one CSV per lesson.

**Tech Stack:** Python 3.11+, Playwright (async), markdownify, BeautifulSoup4, python-dotenv, pytest, pytest-asyncio

---

### Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `src/__init__.py`
- Create: `tests/__init__.py`
- Create: `output/.gitkeep`

**Step 1: Create requirements.txt**

```
playwright==1.42.0
markdownify==0.11.6
beautifulsoup4==4.12.3
python-dotenv==1.0.1
pytest==8.1.1
pytest-asyncio==0.23.6
```

**Step 2: Create .env.example**

```
COURSERA_EMAIL=your@email.com
COURSERA_PASSWORD=yourpassword
```

**Step 3: Create .gitignore**

```
.env
output/
__pycache__/
.pytest_cache/
*.pyc
.venv/
```

**Step 4: Create empty init files**

```bash
mkdir -p src tests output
touch src/__init__.py tests/__init__.py output/.gitkeep
```

**Step 5: Install dependencies**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

**Step 6: Commit**

```bash
git add requirements.txt .env.example .gitignore src/ tests/ output/
git commit -m "chore: project setup with dependencies and structure"
```

---

### Task 2: converter.py — HTML → Markdown + Section Splitting

**Files:**
- Create: `src/converter.py`
- Create: `tests/test_converter.py`

**Step 1: Write failing tests**

```python
# tests/test_converter.py
from src.converter import html_to_sections, Section

def test_single_section_no_headings():
    html = "<p>Hello <strong>world</strong></p>"
    sections = html_to_sections(html, lesson_title="Intro")
    assert len(sections) == 1
    assert sections[0].heading == "Intro"
    assert "**world**" in sections[0].content

def test_splits_on_h2():
    html = "<p>Before</p><h2>Part A</h2><p>After A</p><h2>Part B</h2><p>After B</p>"
    sections = html_to_sections(html, lesson_title="Lesson")
    assert len(sections) == 3
    assert sections[0].heading == "Lesson"
    assert sections[1].heading == "Part A"
    assert sections[2].heading == "Part B"

def test_splits_on_h3():
    html = "<h3>Sub</h3><p>Content</p>"
    sections = html_to_sections(html, lesson_title="Lesson")
    assert sections[0].heading == "Sub"

def test_empty_html_returns_one_empty_section():
    sections = html_to_sections("", lesson_title="Empty")
    assert len(sections) == 1
    assert sections[0].heading == "Empty"
```

**Step 2: Run tests to verify they fail**

```bash
pytest tests/test_converter.py -v
```
Expected: `ImportError` or `ModuleNotFoundError` — converter doesn't exist yet.

**Step 3: Implement converter.py**

```python
# src/converter.py
from dataclasses import dataclass
from markdownify import markdownify as md
from bs4 import BeautifulSoup, NavigableString, Tag


@dataclass
class Section:
    heading: str
    content: str


def html_to_sections(html: str, lesson_title: str) -> list[Section]:
    if not html.strip():
        return [Section(heading=lesson_title, content="")]

    soup = BeautifulSoup(html, "html.parser")
    sections: list[Section] = []
    current_heading = lesson_title
    current_nodes: list = []

    def flush():
        raw = "".join(str(n) for n in current_nodes)
        content = md(raw, heading_style="ATX").strip()
        sections.append(Section(heading=current_heading, content=content))

    for elem in soup.children:
        if isinstance(elem, Tag) and elem.name in ("h2", "h3"):
            if current_nodes:
                flush()
            current_heading = elem.get_text(strip=True)
            current_nodes = []
        else:
            current_nodes.append(elem)

    if current_nodes:
        flush()

    if not sections:
        sections.append(Section(heading=lesson_title, content=md(html).strip()))

    return sections
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_converter.py -v
```
Expected: all 4 tests PASS.

**Step 5: Commit**

```bash
git add src/converter.py tests/test_converter.py
git commit -m "feat: converter HTML to Markdown sections"
```

---

### Task 3: writer.py — CSV Writing

**Files:**
- Create: `src/writer.py`
- Create: `tests/test_writer.py`

**Step 1: Write failing tests**

```python
# tests/test_writer.py
import csv
from pathlib import Path
from src.converter import Section
from src.writer import write_csv, sanitize_filename


def test_sanitize_removes_special_chars():
    assert sanitize_filename("How/Why? It works!") == "How_Why_It_works"

def test_sanitize_keeps_spaces_as_underscores():
    assert sanitize_filename("Zero Shot Learning") == "Zero_Shot_Learning"

def test_write_csv_creates_file(tmp_path):
    sections = [
        Section(heading="Intro", content="Hello world"),
        Section(heading="Part A", content="More content"),
    ]
    path = write_csv(
        course_slug="test-course",
        module="Week 1",
        lesson_title="My Lesson",
        sections=sections,
        output_dir=tmp_path,
    )
    assert path.exists()
    assert path.name == "My_Lesson.csv"

def test_write_csv_correct_columns(tmp_path):
    sections = [Section(heading="S1", content="C1")]
    path = write_csv("slug", "Mod", "Lesson", sections, tmp_path)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert rows[0]["module"] == "Mod"
    assert rows[0]["lesson_title"] == "Lesson"
    assert rows[0]["section"] == "S1"
    assert rows[0]["content"] == "C1"

def test_write_csv_multiple_rows(tmp_path):
    sections = [Section(heading=f"S{i}", content=f"C{i}") for i in range(3)]
    path = write_csv("slug", "Mod", "Lesson", sections, tmp_path)
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert len(rows) == 3
```

**Step 2: Run to verify they fail**

```bash
pytest tests/test_writer.py -v
```

**Step 3: Implement writer.py**

```python
# src/writer.py
import csv
import re
from pathlib import Path
from src.converter import Section


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[^\w\s-]", "", name).strip()
    return re.sub(r"\s+", "_", name)


def write_csv(
    course_slug: str,
    module: str,
    lesson_title: str,
    sections: list[Section],
    output_dir: Path = Path("output"),
) -> Path:
    course_dir = output_dir / sanitize_filename(course_slug)
    course_dir.mkdir(parents=True, exist_ok=True)
    filepath = course_dir / (sanitize_filename(lesson_title) + ".csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["module", "lesson_title", "section", "content"]
        )
        writer.writeheader()
        for section in sections:
            writer.writerow(
                {
                    "module": module,
                    "lesson_title": lesson_title,
                    "section": section.heading,
                    "content": section.content,
                }
            )

    return filepath
```

**Step 4: Run to verify they pass**

```bash
pytest tests/test_writer.py -v
```

**Step 5: Commit**

```bash
git add src/writer.py tests/test_writer.py
git commit -m "feat: writer produces structured CSV per lesson"
```

---

### Task 4: auth.py — Playwright Login

**Files:**
- Create: `src/auth.py`
- Create: `tests/test_auth.py`

**Step 1: Write failing tests (mock-based)**

```python
# tests/test_auth.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_login_fills_credentials():
    mock_page = AsyncMock()
    mock_page.url = "https://www.coursera.org/browse"
    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page
    mock_browser = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch.return_value = mock_browser

    with patch("src.auth.async_playwright") as mock_ap:
        mock_ap.return_value.__aenter__ = AsyncMock(return_value=mock_playwright)
        mock_ap.return_value.__aexit__ = AsyncMock(return_value=False)
        from src.auth import login
        ctx = await login("user@test.com", "pass123", headless=True)

    mock_page.goto.assert_called_once()
    mock_page.fill.assert_any_await('[name="email"]', "user@test.com")
    mock_page.fill.assert_any_await('[name="password"]', "pass123")
```

**Step 2: Run to verify it fails**

```bash
pytest tests/test_auth.py -v
```

**Step 3: Implement auth.py**

```python
# src/auth.py
from playwright.async_api import async_playwright, BrowserContext


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
    # Click login button in header
    await page.click('[data-testid="header-login-button"]', timeout=10_000)
    await page.fill('[name="email"]', email)
    await page.click('[data-testid="email-next-button"]', timeout=5_000)
    await page.fill('[name="password"]', password)
    await page.click('[data-testid="signin-btn"]', timeout=5_000)
    # Wait for redirect away from login page
    await page.wait_for_url(
        lambda url: "accounts.coursera.org" not in url, timeout=30_000
    )

    return playwright, browser, context
```

**Step 4: Run tests**

```bash
pytest tests/test_auth.py -v
```

**Step 5: Commit**

```bash
git add src/auth.py tests/test_auth.py
git commit -m "feat: playwright login to Coursera"
```

---

### Task 5: navigator.py — Course Structure Traversal

**Files:**
- Create: `src/navigator.py`
- Create: `tests/test_navigator.py`
- Create: `tests/fixtures/course_sidebar.html`

**Step 1: Create sidebar HTML fixture**

Save this as `tests/fixtures/course_sidebar.html` — a minimal replica of Coursera's module sidebar:

```html
<div data-testid="course-home-sidebar">
  <div data-testid="module-item">
    <h3>Week 1: Foundations</h3>
    <ul>
      <li data-testid="lesson-item" data-item-type="reading">
        <a href="/learn/prompt-engineering/lecture/abc123/intro">Introduction to Prompting</a>
      </li>
      <li data-testid="lesson-item" data-item-type="lecture">
        <a href="/learn/prompt-engineering/lecture/def456/video">Video Lecture</a>
      </li>
      <li data-testid="lesson-item" data-item-type="reading">
        <a href="/learn/prompt-engineering/lecture/ghi789/zero-shot">Zero-Shot Prompting</a>
      </li>
    </ul>
  </div>
  <div data-testid="module-item">
    <h3>Week 2: Advanced</h3>
    <ul>
      <li data-testid="lesson-item" data-item-type="reading">
        <a href="/learn/prompt-engineering/lecture/jkl012/chain">Chain of Thought</a>
      </li>
    </ul>
  </div>
</div>
```

**Step 2: Write failing tests**

```python
# tests/test_navigator.py
from pathlib import Path
from src.navigator import parse_readings_from_html, ReadingLesson


FIXTURE = (Path(__file__).parent / "fixtures" / "course_sidebar.html").read_text()


def test_finds_only_readings():
    readings = parse_readings_from_html(FIXTURE, base_url="https://www.coursera.org")
    lesson_types = [r.lesson_title for r in readings]
    assert "Introduction to Prompting" in lesson_types
    assert "Zero-Shot Prompting" in lesson_types
    assert "Chain of Thought" in lesson_types

def test_excludes_non_readings():
    readings = parse_readings_from_html(FIXTURE, base_url="https://www.coursera.org")
    titles = [r.lesson_title for r in readings]
    assert "Video Lecture" not in titles

def test_captures_module_name():
    readings = parse_readings_from_html(FIXTURE, base_url="https://www.coursera.org")
    week1 = [r for r in readings if r.module == "Week 1: Foundations"]
    assert len(week1) == 2

def test_full_url():
    readings = parse_readings_from_html(FIXTURE, base_url="https://www.coursera.org")
    assert readings[0].url.startswith("https://www.coursera.org")
```

**Step 3: Run to verify they fail**

```bash
pytest tests/test_navigator.py -v
```

**Step 4: Implement navigator.py**

```python
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
            url = href if href.startswith("http") else base_url + href
            lessons.append(ReadingLesson(module=module_name, lesson_title=title, url=url))

    return lessons


async def get_course_readings(context: BrowserContext, course_url: str) -> list[ReadingLesson]:
    """Navigate to course home and return all Reading lessons."""
    page = await context.new_page()
    await page.goto(course_url, wait_until="networkidle", timeout=30_000)
    html = await page.content()
    await page.close()

    # Extract course slug for output directory naming
    slug = course_url.rstrip("/").split("/learn/")[-1].split("/")[0]

    readings = parse_readings_from_html(html, base_url="https://www.coursera.org")
    return readings, slug
```

**Step 5: Run tests**

```bash
pytest tests/test_navigator.py -v
```

**Step 6: Commit**

```bash
git add src/navigator.py tests/test_navigator.py tests/fixtures/
git commit -m "feat: navigator parses course modules and filters Reading lessons"
```

---

### Task 6: extractor.py — API Response Interception

**Files:**
- Create: `src/extractor.py`
- Create: `tests/test_extractor.py`

**Step 1: Write failing tests**

```python
# tests/test_extractor.py
import pytest
from src.extractor import extract_html_from_response


def test_extracts_html_from_ondemand_response():
    fake_json = {
        "elements": [
            {
                "typeName": "reading",
                "definition": {
                    "value": {
                        "html": "<p>Hello world</p>"
                    }
                }
            }
        ]
    }
    result = extract_html_from_response(fake_json)
    assert result == "<p>Hello world</p>"


def test_returns_none_when_no_html():
    result = extract_html_from_response({"elements": []})
    assert result is None


def test_returns_none_on_wrong_structure():
    result = extract_html_from_response({"data": "something_else"})
    assert result is None
```

**Step 2: Run to verify they fail**

```bash
pytest tests/test_extractor.py -v
```

**Step 3: Implement extractor.py**

```python
# src/extractor.py
import asyncio
import json
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
    Returns the HTML string or None if not found.
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
            # Give interceptor time to catch any late responses
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
```

**Step 4: Run tests**

```bash
pytest tests/test_extractor.py -v
```

**Step 5: Commit**

```bash
git add src/extractor.py tests/test_extractor.py
git commit -m "feat: extractor intercepts Coursera API for reading HTML"
```

---

### Task 7: main.py — CLI Wiring

**Files:**
- Create: `main.py`

**Step 1: Implement main.py**

No unit test here — this is the integration glue. Manual smoke test in Step 3.

```python
# main.py
import asyncio
import logging
import os
import sys
import time
from pathlib import Path

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
    email = os.environ["COURSERA_EMAIL"]
    password = os.environ["COURSERA_PASSWORD"]

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
                time.sleep(DELAY_BETWEEN_LESSONS)

    finally:
        await browser.close()
        await playwright.stop()

    logger.info("Done.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <COURSE_URL>")
        sys.exit(1)
    asyncio.run(run(sys.argv[1]))
```

**Step 2: Create .env from example**

```bash
cp .env.example .env
# Edit .env with your actual credentials
```

**Step 3: Manual smoke test**

```bash
python main.py "https://www.coursera.org/learn/prompt-engineering/home/module/1"
```

Expected:
- Browser opens, logs in
- Terminal shows lesson-by-lesson progress
- `output/prompt-engineering/` folder appears with `.csv` files

**Step 4: Run full test suite**

```bash
pytest -v
```
Expected: all tests PASS.

**Step 5: Commit**

```bash
git add main.py .env.example
git commit -m "feat: main CLI wires auth, navigator, extractor, converter, writer"
```

---

### Task 8: Final Cleanup

**Step 1: Add pytest config**

Add `pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
```

**Step 2: Run all tests one last time**

```bash
pytest -v
```

**Step 3: Final commit**

```bash
git add pytest.ini
git commit -m "chore: add pytest asyncio config"
```
