# tests/test_auth.py
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_login_fills_credentials():
    mock_page = AsyncMock()
    mock_context = AsyncMock()
    mock_context.new_page.return_value = mock_page
    mock_browser = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    mock_playwright = AsyncMock()
    mock_playwright.chromium.launch.return_value = mock_browser

    with patch("src.auth.async_playwright") as mock_ap:
        mock_ap.return_value.start = AsyncMock(return_value=mock_playwright)
        from src.auth import login
        result = await login("user@test.com", "pass123", headless=True)

    mock_page.goto.assert_called_once()
    mock_page.fill.assert_any_call('[name="email"]', "user@test.com")
    mock_page.fill.assert_any_call('[name="password"]', "pass123")
    assert result == (mock_playwright, mock_browser, mock_context)
