"""
Abre um browser para você logar no Coursera manualmente.
Quando o login for detectado, salva a sessão em session.json automaticamente.

Usage:
    python save_session.py
"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

SESSION_FILE = Path("session.json")


async def save():
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=False,
        args=["--start-maximized"]
    )
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        no_viewport=True,
    )
    page = await context.new_page()
    await page.goto("https://www.coursera.org/?authMode=login")

    print("Browser aberto. Faça o login no Coursera.")
    print("A sessão será salva automaticamente após o login...")

    # Aguarda até que a URL não contenha mais authMode (login concluído)
    await page.wait_for_url(
        lambda url: "authMode" not in url and "accounts.coursera.org" not in url,
        timeout=300_000  # 5 minutos para o usuário logar
    )

    print("Login detectado! Salvando sessão...")
    state = await context.storage_state()
    SESSION_FILE.write_text(json.dumps(state))
    print(f"Sessão salva em {SESSION_FILE}. Pode fechar o browser.")

    await browser.close()
    await pw.stop()


asyncio.run(save())
