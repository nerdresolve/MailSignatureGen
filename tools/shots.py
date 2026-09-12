"""Captura as telas do README.

Não são mockups: é a aplicação rodando. Sobe o servidor, abre a interface no
Chromium, preenche o formulário e fotografa — no desktop e no celular.

    python tools/shots.py     (precisa de: pip install playwright pillow && playwright install chromium)
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "docs" / "telas"

DESKTOP = {"width": 1280, "height": 900}
CELULAR = {"width": 390, "height": 844}

EXEMPLO = {
    "nome": "Ana Souza",
    "cargo": "Desenvolvedora",
    "email": "ana.souza@nerdresolve.com",
    "telefone": "+55 (21) 99999-9999",
}


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def esperar(porta: int, segundos: int = 30) -> None:
    limite = time.time() + segundos
    while time.time() < limite:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", porta)) == 0:
                return
        time.sleep(0.3)
    raise SystemExit("o servidor não subiu a tempo")


def salvar(pagina, nome: str, **kwargs) -> None:
    """Fotografa e guarda em WebP: as mesmas telas custam um quarto do peso."""
    temporario = DESTINO / f"{nome}.png"
    pagina.screenshot(path=temporario, **kwargs)

    with Image.open(temporario) as imagem:
        imagem.convert("RGB").save(DESTINO / f"{nome}.webp", "WEBP", quality=88, method=6)
    temporario.unlink()


def preencher(pagina) -> None:
    for campo, valor in EXEMPLO.items():
        pagina.fill(f"#{campo}", valor)


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)

    porta = porta_livre()
    servidor = subprocess.Popen(
        ["node", "app/server.js"],
        cwd=RAIZ,
        env={**os.environ, "PORT": str(porta)},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        esperar(porta)
        base = f"http://127.0.0.1:{porta}"

        with sync_playwright() as p:
            navegador = p.chromium.launch()

            # Desktop: o formulário vazio e, depois, com a prévia gerada.
            pagina = navegador.new_page(viewport=DESKTOP, device_scale_factor=2)
            pagina.goto(base, wait_until="networkidle")
            pagina.wait_for_timeout(400)
            salvar(pagina, "01-formulario")

            preencher(pagina)
            pagina.click("#btn-gerar")
            pagina.wait_for_selector("#previa:not([hidden])", timeout=20_000)
            pagina.wait_for_timeout(600)
            salvar(pagina, "02-previa", full_page=True)

            # Celular: a mesma tela, com a prévia.
            movel = navegador.new_page(viewport=CELULAR, device_scale_factor=2)
            movel.goto(base, wait_until="networkidle")
            preencher(movel)
            movel.click("#btn-gerar")
            movel.wait_for_selector("#previa:not([hidden])", timeout=20_000)
            movel.wait_for_timeout(600)
            salvar(movel, "03-celular", full_page=True)

            navegador.close()

        for arquivo in sorted(DESTINO.glob("*.webp")):
            print(f"{arquivo.relative_to(RAIZ)}  ({arquivo.stat().st_size / 1024:.0f} kB)")

    finally:
        servidor.terminate()
        servidor.wait(timeout=10)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
