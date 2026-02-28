# Coursera Reading Scraper — Design Document

**Date:** 2026-02-28
**Status:** Approved

## Overview

CLI tool that logs into Coursera, navigates all modules of a given course, and downloads every "Reading" lesson as a CSV file named after the lesson title.

## Input / Output

- **Input:** `python main.py <URL_COURSE>`
- **Credentials:** `COURSERA_EMAIL` and `COURSERA_PASSWORD` in `.env`
- **Output:** `output/<course-slug>/<lesson title>.csv` — one file per Reading lesson

## CSV Structure

| Column | Description |
|---|---|
| `module` | Module/week name |
| `lesson_title` | Reading lesson title |
| `section` | Heading (H2/H3) within the lesson |
| `content` | Markdown content of that section |

- One row per section (split by H2/H3 headings)
- If no headings found → single row with full content
- Content format: **Markdown** (converted from HTML via `markdownify`)

## Architecture

```
main.py  (CLI entrypoint)
   ├── src/auth.py        → Playwright login, returns authenticated browser context
   ├── src/navigator.py   → traverse all modules, collect Reading-type lessons only
   ├── src/extractor.py   → intercept internal API responses, extract HTML content
   ├── src/converter.py   → HTML → Markdown, split by headings into sections
   └── src/writer.py      → write structured CSV per lesson
```

## Technical Approach

**Playwright + API interception (Approach C)**

- Playwright launches a headless browser and authenticates with user credentials
- While navigating each Reading lesson page, a `page.on("response", ...)` handler intercepts XHR/Fetch calls to Coursera's internal API (e.g., `onDemandLectureAssets.v1`, `onDemandElements.v1`)
- The HTML content is extracted from the JSON response, avoiding the need to parse the rendered DOM
- Faster and more reliable than pure DOM scraping

## Project Structure

```
coursera-scrapping/
├── .env                  # COURSERA_EMAIL, COURSERA_PASSWORD (gitignored)
├── .env.example
├── requirements.txt
├── main.py
├── src/
│   ├── auth.py
│   ├── navigator.py
│   ├── extractor.py
│   ├── converter.py
│   └── writer.py
└── output/
    └── <course-slug>/
        ├── Introduction to Prompting.csv
        └── ...
```

## Stack

- **Python** (async)
- **Playwright** — browser automation and API interception
- **markdownify** — HTML to Markdown conversion
- **python-dotenv** — credentials management
- **csv** — built-in CSV writing

## Error Handling

| Scenario | Behavior |
|---|---|
| API response not intercepted (timeout 15s) | Log warning, skip lesson, continue |
| Navigation timeout | Retry 2x, then log and skip |
| Invalid filename characters | Sanitize to `-` (e.g., `How/Why?` → `How-Why.csv`) |
| No Readings in course | Warn and exit cleanly |
| Rate limiting | Configurable delay between requests (default: 2s) |
