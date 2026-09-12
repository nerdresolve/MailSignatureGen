"""Desenho da assinatura.

A imagem é composta do zero a cada requisição: fundo, faixa da marca, logo,
textos e ícones sociais. Não existe template achatado, e é de propósito — um PNG
pronto com os dados de alguém dentro exige editor de imagem para trocar de
cliente, e carrega para o repositório o nome e o telefone de quem posou de
exemplo.

O layout é uma coluna de blocos: cada bloco sabe a própria altura e o desenho
apenas empilha. Trocar a ordem, tirar o telefone ou aumentar a fonte não exige
recalcular coordenada nenhuma, que era o custo da versão anterior.
"""

from __future__ import annotations

import io
import math
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFont

from .brand import Estilo, Marca, Perfil

ESCALA = 2  # desenha em dobro e reduz: as bordas saem sem serrilhado

ESPACO_LINHA = 6
ESPACO_BLOCO = 14
ICONE = 15
ESPACO_ICONE = 9


@dataclass(frozen=True)
class Dados:
    """O que a pessoa preencheu."""

    nome: str
    cargo: str
    email: str
    telefone: str = ""


_cache_fontes: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def _fonte(estilo: Estilo, escala: int) -> ImageFont.FreeTypeFont:
    chave = (str(estilo.fonte), estilo.tamanho * escala)
    if chave not in _cache_fontes:
        _cache_fontes[chave] = ImageFont.truetype(str(estilo.fonte), estilo.tamanho * escala)
    return _cache_fontes[chave]


def _altura(estilo: Estilo, escala: int) -> int:
    ascent, descent = _fonte(estilo, escala).getmetrics()
    return ascent + descent


def _texto(draw: ImageDraw.ImageDraw, xy: tuple[int, int], texto: str, estilo: Estilo,
           escala: int, cor: tuple[int, int, int] | None = None) -> int:
    """Escreve e devolve a largura ocupada."""
    conteudo = texto.upper() if estilo.caixa_alta else texto
    fonte = _fonte(estilo, escala)
    draw.text(xy, conteudo, font=fonte, fill=cor or estilo.cor)
    return int(draw.textlength(conteudo, font=fonte))


def _texto_ajustado(draw: ImageDraw.ImageDraw, xy: tuple[int, int], texto: str, estilo: Estilo,
                    escala: int, limite: int, cor: tuple[int, int, int] | None = None,
                    max_linhas: int = 2) -> int:
    """Escreve dentro de `limite`, encolhendo e quebrando o quanto precisar.

    Devolve a altura ocupada, porque quem chama empilha o próximo bloco.

    A ordem importa. Primeiro encolhe até 85% — um ajuste que passa
    despercebido. Só então quebra em outra linha, e apenas até `max_linhas`.
    Encolher sozinho não resolve: um nome de quarenta e tantos caracteres
    precisaria de uns 11px para caber numa coluna de 320, e ninguém lê isso
    numa assinatura. Truncar está fora de questão — é o nome de uma pessoa.
    """
    conteudo = texto.upper() if estilo.caixa_alta else texto
    minimo = max(1, round(estilo.tamanho * 0.85))

    def com(tamanho: int) -> Estilo:
        return Estilo(estilo.peso, tamanho, estilo.cor, estilo.caixa_alta)

    def largura(txt: str, tamanho: int) -> float:
        return draw.textlength(txt, font=_fonte(com(tamanho), escala))

    tamanho = estilo.tamanho
    while tamanho > minimo and largura(conteudo, tamanho) > limite:
        tamanho -= 1

    # Ainda não coube: distribui as palavras em até `max_linhas`.
    linhas = [conteudo]
    if largura(conteudo, tamanho) > limite and max_linhas > 1:
        linhas, atual = [], ""
        for palavra in conteudo.split():
            tentativa = f"{atual} {palavra}".strip()
            if atual and largura(tentativa, tamanho) > limite and len(linhas) < max_linhas - 1:
                linhas.append(atual)
                atual = palavra
            else:
                atual = tentativa
        linhas.append(atual)

    # A última linha ainda pode estourar (uma palavra só, ou linhas demais);
    # aí sim encolhe o conjunto até caber de vez.
    while tamanho > 1 and max(largura(l, tamanho) for l in linhas) > limite:
        tamanho -= 1

    estilo_final = com(tamanho)
    passo = _altura(estilo_final, escala) + 2 * escala
    for i, linha in enumerate(linhas):
        # `_texto` reaplicaria o upper; as linhas já vieram em caixa alta.
        draw.text(
            (xy[0], xy[1] + i * passo), linha,
            font=_fonte(estilo_final, escala), fill=cor or estilo.cor,
        )

    return (len(linhas) - 1) * passo + _altura(estilo_final, escala)


def _onda(draw: ImageDraw.ImageDraw, largura: int, cor: tuple[int, int, int], escala: int) -> None:
    """A faixa superior: duas senoides deslocadas, a de trás mais clara.

    Duas ondas em vez de uma porque uma só lê como erro de renderização; duas,
    com opacidades diferentes, leem como marca.
    """
    altura_faixa = 54 * escala
    for opacidade, fase, amplitude in ((0.30, 0.0, 15), (1.0, 0.85, 11)):
        pontos = []
        for x in range(0, largura + 1, max(1, escala)):
            t = x / largura * math.tau * 1.35 + fase
            y = altura_faixa * 0.52 + math.sin(t) * amplitude * escala
            pontos.append((x, y))

        mistura = tuple(int(c + (255 - c) * (1 - opacidade)) for c in cor)
        draw.line(pontos, fill=mistura, width=max(2, 3 * escala), joint="curve")


def _barra(draw: ImageDraw.ImageDraw, largura: int, cor: tuple[int, int, int], escala: int) -> None:
    draw.rectangle((0, 0, largura, 6 * escala), fill=cor)


def _icone_social(draw: ImageDraw.ImageDraw, xy: tuple[int, int], rede: str,
                  cor: tuple[int, int, int], escala: int,
                  marca_fundo: tuple[int, int, int] = (255, 255, 255)) -> None:
    """Ícones desenhados a traço: um glifo por rede, sem depender de fonte de ícones.

    Font Awesome via CDN era a solução anterior, mas ela não alcança o Pillow —
    e uma assinatura de e-mail precisa da imagem, não do HTML.
    """
    x, y = xy
    d = ICONE * escala
    traco = max(1, round(1.6 * escala))
    caixa = (x, y, x + d, y + d)

    if rede == "instagram":
        draw.rounded_rectangle(caixa, radius=d * 0.28, outline=cor, width=traco)
        m = d * 0.28
        draw.ellipse((x + m, y + m, x + d - m, y + d - m), outline=cor, width=traco)
        p = d * 0.19
        draw.ellipse((x + d - p - traco, y + p, x + d - p + traco, y + p + 2 * traco), fill=cor)

    elif rede == "linkedin":
        # O "in" não cabe legível em 15px de traço fino: o glifo é maciço,
        # recortado em negativo, que é como o próprio LinkedIn o desenha.
        draw.rounded_rectangle(caixa, radius=d * 0.20, fill=cor)
        vazio = marca_fundo
        base = y + d * 0.76
        # haste do "i" e o ponto
        ix = x + d * 0.30
        draw.rectangle((ix - traco * 0.7, y + d * 0.42, ix + traco * 0.7, base), fill=vazio)
        draw.rectangle((ix - traco * 0.7, y + d * 0.24, ix + traco * 0.7, y + d * 0.34), fill=vazio)
        # o "n": haste, ombro e perna
        nx = x + d * 0.52
        largura_n = d * 0.20
        draw.rectangle((nx - traco * 0.7, y + d * 0.42, nx + traco * 0.7, base), fill=vazio)
        draw.rectangle((nx, y + d * 0.42, nx + largura_n + traco * 0.7, y + d * 0.42 + traco * 1.4), fill=vazio)
        draw.rectangle(
            (nx + largura_n - traco * 0.7, y + d * 0.42, nx + largura_n + traco * 0.7, base), fill=vazio
        )

    else:  # site: um globo
        draw.ellipse(caixa, outline=cor, width=traco)
        draw.line((x, y + d / 2, x + d, y + d / 2), fill=cor, width=traco)
        draw.ellipse((x + d * 0.28, y, x + d * 0.72, y + d), outline=cor, width=traco)


def _colar_logo(base: Image.Image, caminho, altura_alvo: int, xy: tuple[int, int]) -> int:
    """Cola o logo preservando proporção. Devolve a largura ocupada."""
    logo = Image.open(caminho).convert("RGBA")
    largura = max(1, round(logo.width * altura_alvo / logo.height))
    logo = logo.resize((largura, altura_alvo), Image.LANCZOS)
    base.paste(logo, xy, logo)
    return largura


def desenhar(marca: Marca, dados: Dados, perfil: Perfil | None = None) -> Image.Image:
    e = ESCALA
    perfil = perfil or marca.perfis[0]
    cor_marca = perfil.cor or marca.cores["marca"]

    largura = marca.largura * e
    margem = marca.margem * e

    # Desenha numa tela com folga e recorta no fim: a altura definitiva só é
    # conhecida depois que nome, cargo e redes ocuparam o que precisavam.
    folga = marca.altura * 2 * e
    imagem = Image.new("RGB", (largura, folga), marca.cores["fundo"])
    draw = ImageDraw.Draw(imagem)

    base_conteudo = 0  # a linha mais baixa que algum bloco alcançou

    if marca.faixa == "onda":
        _onda(draw, largura, cor_marca, e)
    elif marca.faixa == "barra":
        _barra(draw, largura, cor_marca, e)

    est = marca.estilos
    topo = (52 if marca.faixa != "nenhuma" else 26) * e

    # --- Alto, à direita: o logo ------------------------------------------
    x_direita = largura - margem
    base_logo = topo

    if caminho_logo := marca.logo_do(perfil):
        with Image.open(caminho_logo) as arquivo:
            proporcao = arquivo.width / arquivo.height
        altura_logo = marca.logo_altura * e
        largura_logo = max(1, round(altura_logo * proporcao))
        _colar_logo(imagem, caminho_logo, altura_logo, (x_direita - largura_logo, topo))
        base_logo = topo + altura_logo

    # --- Corpo: as três colunas, todas a partir da mesma linha ------------
    y_corpo = base_logo + 26 * e

    # A coluna da esquerda vai até onde as redes começam; sem redes, até o
    # filete do slogan. É esse número que limita nome, cargo e contato.
    # O texto começa em `margem`, então o limite é a distância daí até a
    # próxima coluna, menos a folga que as separa.
    x_social = margem + 336 * e
    respiro = 16 * e
    limite_esquerda = (x_social if marca.sociais else x_direita) - margem - respiro

    # Esquerda: quem é a pessoa e como falar com ela. Cada bloco devolve a
    # altura que ocupou — nome e cargo podem ter quebrado em duas linhas.
    y = y_corpo
    y += _texto_ajustado(draw, (margem, y), dados.nome, est["nome"], e,
                         limite_esquerda, cor_marca) + ESPACO_LINHA * e

    y += _texto_ajustado(draw, (margem, y), dados.cargo, est["cargo"], e,
                         limite_esquerda) + ESPACO_BLOCO * e

    y_contato = y  # as redes sociais se alinham ao primeiro contato
    # E-mail não quebra: um endereço partido em duas linhas não é copiável.
    y += _texto_ajustado(draw, (margem, y), dados.email, est["contato"], e,
                         limite_esquerda, max_linhas=1) + ESPACO_LINHA * e

    if dados.telefone:
        _texto(draw, (margem, y), dados.telefone, est["contato"], e)
        y += _altura(est["contato"], e)
    base_conteudo = max(base_conteudo, y)

    # Meio: as redes, à altura do bloco de contato.
    if marca.sociais:
        y_social = y_contato
        for social in marca.sociais:
            _icone_social(draw, (x_social, y_social), social.rede, cor_marca, e, marca.cores["fundo"])
            _texto(
                draw,
                (x_social + (ICONE + ESPACO_ICONE) * e, y_social - 1 * e),
                social.handle, est["contato"], e,
            )
            y_social += max(_altura(est["contato"], e), ICONE * e) + ESPACO_LINHA * e
        base_conteudo = max(base_conteudo, y_social - ESPACO_LINHA * e)

    # Direita: o slogan, encostado na borda e separado por um filete.
    if marca.slogan:
        linhas = marca.slogan.splitlines()
        fonte_slogan = _fonte(est["slogan"], e)
        passo = _altura(est["slogan"], e) + 3 * e
        x_texto = x_direita - max(draw.textlength(l, font=fonte_slogan) for l in linhas)

        draw.line(
            (x_texto - 16 * e, y_corpo, x_texto - 16 * e, y_corpo + len(linhas) * passo),
            fill=marca.cores["linha"], width=max(1, e),
        )

        for i, linha in enumerate(linhas):
            _texto(draw, (x_texto, y_corpo + i * passo), linha, est["slogan"], e)
        base_conteudo = max(base_conteudo, y_corpo + len(linhas) * passo)

    # A altura da marca é o mínimo, não o teto: um nome que quebrou em duas
    # linhas empurra o conteúdo para baixo, e cortar a última rede social seria
    # pior do que devolver uma imagem alguns pixels mais alta.
    altura_final = max(marca.altura, round(base_conteudo / e + marca.margem * 0.75))
    if altura_final > marca.altura:
        imagem = imagem.crop((0, 0, largura, altura_final * e))

    return imagem.resize((marca.largura, altura_final), Image.LANCZOS)


def para_png(imagem: Image.Image) -> bytes:
    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
