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
