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
