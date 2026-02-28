# tests/test_extractor.py
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


def test_returns_none_when_no_elements():
    result = extract_html_from_response({"elements": []})
    assert result is None


def test_returns_none_on_wrong_structure():
    result = extract_html_from_response({"data": "something_else"})
    assert result is None


def test_returns_none_when_html_field_missing():
    fake_json = {
        "elements": [
            {
                "typeName": "video",
                "definition": {"value": {"videoId": "abc123"}}
            }
        ]
    }
    result = extract_html_from_response(fake_json)
    assert result is None


def test_extracts_html_from_linked_assets():
    """Matches the real onDemandSupplements.v1 response structure."""
    fake_json = {
        "elements": [{"itemId": "CIPwz", "id": "course~CIPwz"}],
        "linked": {
            "openCourseAssets.v1": [
                {
                    "itemId": "CIPwz",
                    "typeName": "cml",
                    "definition": {
                        "renderableHtmlWithMetadata": {
                            "renderableHtml": "<p>Reading content here</p>"
                        }
                    },
                }
            ]
        },
    }
    result = extract_html_from_response(fake_json)
    assert result == "<p>Reading content here</p>"
