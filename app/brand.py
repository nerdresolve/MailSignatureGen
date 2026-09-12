"""Leitura e validação do arquivo de marca.

Uma marca é um diretório em `brands/<id>/` com um `brand.json` e as imagens que
ele cita. Este módulo transforma esse JSON em objetos com valores já resolvidos:
cor nomeada vira hexadecimal, caminho relativo vira caminho absoluto, campo
ausente vira o padrão. O renderizador não lê JSON — recebe daqui.

Erro de configuração é reportado com o caminho do campo (`cores.marca`), não com
um KeyError, porque quem edita o arquivo normalmente não escreve Python.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DIR_MARCAS = RAIZ / "brands"
DIR_FONTES = RAIZ / "assets" / "fonts"

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

PESOS = {
    "regular": "Manrope-Regular.ttf",
    "semibold": "Manrope-SemiBold.ttf",
    "bold": "Manrope-Bold.ttf",
}

CORES_PADRAO = {
    "marca": "#7C3AED",
    "texto": "#1E1B2E",
    "textoSuave": "#6B7280",
    "fundo": "#FFFFFF",
    "linha": "#E5E7EB",
}

FAIXAS = ("onda", "barra", "nenhuma")


class ErroDeMarca(Exception):
    """Configuração inválida. A mensagem é para quem edita o `brand.json`."""


def _hex_para_rgb(valor: str) -> tuple[int, int, int]:
    valor = valor.lstrip("#")
    return tuple(int(valor[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


@dataclass(frozen=True)
class Estilo:
    """Como um campo de texto é desenhado."""

    peso: str = "regular"
    tamanho: int = 14
    cor: tuple[int, int, int] = (0, 0, 0)
    caixa_alta: bool = False

    @property
    def fonte(self) -> Path:
        return DIR_FONTES / PESOS[self.peso]


@dataclass(frozen=True)
class Social:
    rede: str
    handle: str
    url: str = ""


@dataclass(frozen=True)
class Perfil:
    """Uma variante da assinatura: unidade, submarca ou linha de negócio."""

    id: str
    nome: str
    descricao: str = ""
    cor: tuple[int, int, int] | None = None
    logo: Path | None = None


@dataclass(frozen=True)
class Marca:
    id: str
    nome: str
    diretorio: Path
    cores: dict[str, tuple[int, int, int]]
    logo: Path | None
    logo_altura: int
    largura: int
    altura: int
    margem: int
    faixa: str
    estilos: dict[str, Estilo]
    slogan: str
    sociais: tuple[Social, ...]
    perfis: tuple[Perfil, ...]
    cargos: tuple[str, ...]
    site: str = ""
    dominio_email: str = ""
    telefone_obrigatorio: bool = False
    icones: dict[str, Path] = field(default_factory=dict)

    def perfil(self, id_perfil: str) -> Perfil:
        for p in self.perfis:
            if p.id == id_perfil:
                return p
        validos = ", ".join(p.id for p in self.perfis)
        raise ErroDeMarca(f"perfil '{id_perfil}' não existe em '{self.id}' (há: {validos})")

    def cor_do(self, estilo: Estilo, perfil: Perfil | None = None) -> tuple[int, int, int]:
        """A cor da marca é a do perfil quando ele traz uma própria."""
        if perfil and perfil.cor and estilo.cor == self.cores["marca"]:
            return perfil.cor
        return estilo.cor

    def logo_do(self, perfil: Perfil | None) -> Path | None:
        return perfil.logo if perfil and perfil.logo else self.logo


def _cores(bruto: dict, onde: str) -> dict[str, tuple[int, int, int]]:
    resolvidas = {}
    for nome, padrao in CORES_PADRAO.items():
        valor = bruto.get(nome, padrao)
        if not isinstance(valor, str) or not HEX.match(valor):
            raise ErroDeMarca(
                f"{onde}.cores.{nome}: '{valor}' não é hexadecimal de seis dígitos (ex.: #7C3AED)"
            )
        resolvidas[nome] = _hex_para_rgb(valor)
    return resolvidas


def _estilos(bruto: dict, cores: dict, onde: str) -> dict[str, Estilo]:
    padroes = {
        "nome": Estilo("bold", 24, cores["marca"], True),
        "cargo": Estilo("semibold", 15, cores["texto"]),
        "contato": Estilo("regular", 14, cores["textoSuave"]),
        "slogan": Estilo("semibold", 13, cores["marca"]),
    }

    for campo, padrao in padroes.items():
        cfg = bruto.get(campo)
        if not cfg:
            continue

        peso = cfg.get("peso", padrao.peso)
        if peso not in PESOS:
            raise ErroDeMarca(
                f"{onde}.tipografia.{campo}.peso: '{peso}' não existe (use: {', '.join(PESOS)})"
            )

        nome_cor = cfg.get("cor")
        if nome_cor and nome_cor not in cores:
            raise ErroDeMarca(
                f"{onde}.tipografia.{campo}.cor: '{nome_cor}' não é uma cor declarada "
                f"(use: {', '.join(cores)})"
            )

        padroes[campo] = Estilo(
            peso=peso,
            tamanho=int(cfg.get("tamanho", padrao.tamanho)),
            cor=cores[nome_cor] if nome_cor else padrao.cor,
            caixa_alta=bool(cfg.get("caixaAlta", padrao.caixa_alta)),
        )

    return padroes


def _perfis(bruto: list, diretorio: Path, onde: str) -> tuple[Perfil, ...]:
    if not bruto:
        return (Perfil(id="padrao", nome="Padrão"),)

    perfis = []
    for i, cfg in enumerate(bruto):
        if not cfg.get("id"):
            raise ErroDeMarca(f"{onde}.perfis[{i}]: falta o campo 'id'")

        cor = None
        if valor := cfg.get("cor"):
            if not HEX.match(valor):
                raise ErroDeMarca(f"{onde}.perfis[{i}].cor: '{valor}' não é hexadecimal de seis dígitos")
            cor = _hex_para_rgb(valor)

        logo = None
        if arquivo := cfg.get("logo"):
            logo = diretorio / arquivo
            if not logo.exists():
                raise ErroDeMarca(f"{onde}.perfis[{i}].logo: arquivo não encontrado em {logo}")

        perfis.append(
            Perfil(
                id=cfg["id"],
                nome=cfg.get("nome", cfg["id"]),
                descricao=cfg.get("descricao", ""),
                cor=cor,
                logo=logo,
            )
        )

    ids = [p.id for p in perfis]
    if len(ids) != len(set(ids)):
        raise ErroDeMarca(f"{onde}.perfis: há ids repetidos ({', '.join(ids)})")

    return tuple(perfis)


def carregar(id_marca: str) -> Marca:
    """Lê `brands/<id_marca>/brand.json` e devolve a marca com tudo resolvido."""
    diretorio = DIR_MARCAS / id_marca
    arquivo = diretorio / "brand.json"

    if not arquivo.exists():
        disponiveis = ", ".join(sorted(m.name for m in listar())) or "nenhuma"
        raise ErroDeMarca(f"marca '{id_marca}' não encontrada em {arquivo} (há: {disponiveis})")

    try:
        bruto = json.loads(arquivo.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise ErroDeMarca(f"{arquivo.name} não é JSON válido: linha {erro.lineno}, {erro.msg}") from erro

    onde = f"brands/{id_marca}/brand.json"
    cores = _cores(bruto.get("cores", {}), onde)

    logo = None
    cfg_logo = bruto.get("logo", {})
    if arquivo_logo := cfg_logo.get("arquivo"):
        logo = diretorio / arquivo_logo
        if not logo.exists():
            raise ErroDeMarca(f"{onde}.logo.arquivo: não encontrado em {logo}")

    ass = bruto.get("assinatura", {})
    faixa = ass.get("faixa", "onda")
    if faixa not in FAIXAS:
        raise ErroDeMarca(f"{onde}.assinatura.faixa: '{faixa}' não existe (use: {', '.join(FAIXAS)})")

    for fonte in PESOS.values():
        if not (DIR_FONTES / fonte).exists():
            raise ErroDeMarca(f"fonte ausente: {DIR_FONTES / fonte}")

    return Marca(
        id=id_marca,
        nome=bruto.get("nome", id_marca),
        diretorio=diretorio,
        cores=cores,
        logo=logo,
        logo_altura=int(cfg_logo.get("altura", 46)),
        largura=int(ass.get("largura", 800)),
        altura=int(ass.get("altura", 260)),
        margem=int(ass.get("margem", 32)),
        faixa=faixa,
        estilos=_estilos(bruto.get("tipografia", {}), cores, onde),
        slogan=bruto.get("slogan", ""),
        sociais=tuple(
            Social(rede=s.get("rede", ""), handle=s.get("handle", ""), url=s.get("url", ""))
            for s in bruto.get("sociais", [])
        ),
        perfis=_perfis(bruto.get("perfis", []), diretorio, onde),
        cargos=tuple(bruto.get("cargos", [])),
        site=bruto.get("site", ""),
        dominio_email=bruto.get("dominioEmail", ""),
        telefone_obrigatorio=bool(bruto.get("telefone", {}).get("obrigatorio", False)),
    )


def listar() -> list[Path]:
    """Os diretórios de `brands/` que têm um `brand.json`."""
    if not DIR_MARCAS.exists():
        return []
    return sorted(d for d in DIR_MARCAS.iterdir() if d.is_dir() and (d / "brand.json").exists())
