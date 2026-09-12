"""Interface de linha de comando.

Gera uma assinatura sem subir o servidor. É o que o `server.js` chama, e também
o caminho para gerar em lote a partir de uma planilha exportada em CSV.

    python -m app.cli --marca nerdresolve --nome "Ana Souza" \
        --cargo "Desenvolvedora" --email ana@nerdresolve.com --saida ana.png

Sem `--saida`, o PNG vai para a saída padrão, que é como o servidor consome.
"""

from __future__ import annotations

import argparse
import sys
import unicodedata

from . import brand, render


def _limpar(valor: str) -> str:
    return unicodedata.normalize("NFC", valor).strip()


def montar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="Gera uma assinatura de e-mail em PNG a partir de uma marca configurada.",
    )
    p.add_argument("--marca", default="nerdresolve", help="id da pasta em brands/ (padrão: nerdresolve)")
    p.add_argument("--perfil", default=None, help="id do perfil dentro da marca (padrão: o primeiro)")
    p.add_argument("--nome", required=True, help="nome completo")
    p.add_argument("--cargo", required=True, help="cargo ou setor")
    p.add_argument("--email", required=True, help="e-mail")
    p.add_argument("--telefone", default="", help="telefone (opcional)")
    p.add_argument("--saida", default=None, help="arquivo de destino (padrão: stdout)")
    p.add_argument("--listar", action="store_true", help="lista as marcas disponíveis e sai")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    if "--listar" in argv:
        for diretorio in brand.listar():
            marca = brand.carregar(diretorio.name)
            perfis = ", ".join(p.id for p in marca.perfis)
            print(f"{marca.id:<16} {marca.nome:<24} perfis: {perfis}")
        return 0

    args = montar_parser().parse_args(argv)

    try:
        marca = brand.carregar(args.marca)
        perfil = marca.perfil(args.perfil) if args.perfil else marca.perfis[0]

        dados = render.Dados(
            nome=_limpar(args.nome),
            cargo=_limpar(args.cargo),
            email=_limpar(args.email),
            telefone=_limpar(args.telefone),
        )

        png = render.para_png(render.desenhar(marca, dados, perfil))

    except brand.ErroDeMarca as erro:
        print(f"erro de configuração: {erro}", file=sys.stderr)
        return 2
    except Exception as erro:  # noqa: BLE001 — a CLI reporta, não propaga tracebacks
        print(f"erro ao gerar: {erro}", file=sys.stderr)
        return 1

    if args.saida:
        with open(args.saida, "wb") as arquivo:
            arquivo.write(png)
        print(f"{args.saida} ({len(png) / 1024:.0f} kB)", file=sys.stderr)
    else:
        sys.stdout.buffer.write(png)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
