# tests/test_navigator.py
from pathlib import Path
from src.navigator import parse_readings_from_html, ReadingLesson


FIXTURE = (Path(__file__).parent / "fixtures" / "course_sidebar.html").read_text()


def test_finds_only_readings():
    readings = parse_readings_from_html(FIXTURE, base_url="https://www.coursera.org")
    titles = [r.lesson_title for r in readings]
    assert "Introduction to Prompting" in titles
    assert "Zero-Shot Prompting" in titles
    assert "Chain of Thought" in titles

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
