# src/writer.py
import csv
import re
from pathlib import Path
from src.converter import Section


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[^\w\s-]", " ", name).strip()
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
