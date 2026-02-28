# src/converter.py
from dataclasses import dataclass
from markdownify import markdownify as md
from bs4 import BeautifulSoup, Tag


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
        # Fallback: HTML had only headings with no interspersed content
        sections.append(Section(heading=lesson_title, content=md(html, heading_style="ATX").strip()))

    return sections
