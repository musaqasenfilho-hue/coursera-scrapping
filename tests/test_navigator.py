# tests/test_navigator.py
from pathlib import Path
from src.navigator import parse_module_page, ReadingLesson


FIXTURE = (Path(__file__).parent / "fixtures" / "course_sidebar.html").read_text()


def test_finds_only_readings():
    _, readings = parse_module_page(FIXTURE)
    titles = [r.lesson_title for r in readings]
    assert "Introduction to Prompting" in titles
    assert "Zero-Shot Prompting" in titles
    assert "Chain of Thought" in titles


def test_excludes_non_readings():
    _, readings = parse_module_page(FIXTURE)
    titles = [r.lesson_title for r in readings]
    assert "Video Lecture" not in titles


def test_captures_module_name():
    module_name, readings = parse_module_page(FIXTURE)
    assert module_name == "Week 1: Foundations"
    assert len(readings) == 3


def test_full_url():
    _, readings = parse_module_page(FIXTURE, base_url="https://www.coursera.org")
    assert readings[0].url.startswith("https://www.coursera.org")
