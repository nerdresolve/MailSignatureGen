"""O desenho da assinatura.

Comparar pixel a pixel com uma imagem de referência quebraria a cada ajuste de
espaçamento, então o que se verifica aqui são as propriedades que precisam valer
sempre: o tamanho contratado, a tinta dentro da área útil, a marca presente e o
texto que não vaza para a coluna vizinha.
"""

from __future__ import annotations

import pytest
from PIL import Image

from app import brand, render

DADOS = render.Dados(
    nome="Ana Souza",
    cargo="Desenvolvedora",
    email="ana.souza@nerdresolve.com",
    telefone="+55 (21) 99999-9999",
)


@pytest.fixture(scope="module")
def marca():
    return brand.carregar("nerdresolve")


@pytest.fixture(scope="module")
def imagem(marca):
    return render.desenhar(marca, DADOS)


def _tem_tinta(imagem: Image.Image, fundo=(255, 255, 255), tolerancia=8) -> bool:
    """Se há algum pixel que não seja o fundo.

    `getbbox()` não serve: numa imagem RGB ele mede distância do preto, então
    uma área toda branca é "cheia" para ele.
    """
    pixels = imagem.load()
    return any(
        any(abs(c - f) > tolerancia for c, f in zip(pixels[x, y], fundo))
        for y in range(imagem.height)
        for x in range(imagem.width)
    )


def _pinta_ate(imagem: Image.Image, fundo=(255, 255, 255), tolerancia=8) -> int:
    """A última linha com algum pixel que não seja fundo."""
    pixels = imagem.load()
    ultima = 0
    for y in range(imagem.height):
        for x in range(imagem.width):
            if any(abs(c - f) > tolerancia for c, f in zip(pixels[x, y], fundo)):
                ultima = y
                break
    return ultima


class TestDimensoes:
    def test_a_largura_e_a_da_marca(self, marca, imagem):
        assert imagem.width == marca.largura

    def test_a_altura_da_marca_e_um_minimo(self, marca, imagem):
        # `altura` no brand.json é piso, não teto: conteúdo que cresce empurra
        # a imagem para baixo em vez de ser cortado.
        assert imagem.height >= marca.altura

    def test_nada_e_desenhado_fora_da_imagem(self, imagem):
        # Um bloco que transborda é cortado em silêncio pelo Pillow; este teste
        # é o que denuncia. A folga de 4px cobre o antialias da redução.
        assert _pinta_ate(imagem) <= imagem.height - 4

    def test_margem_esquerda_fica_limpa(self, marca, imagem):
        faixa = imagem.crop((0, 70, marca.margem - 6, imagem.height))
        assert not _tem_tinta(faixa), "algo invadiu a margem esquerda"


class TestConteudo:
    def test_a_cor_da_marca_aparece(self, marca, imagem):
        cores = {cor for _, cor in imagem.getcolors(maxcolors=1 << 16)}
        alvo = marca.cores["marca"]
        assert any(sum(abs(c - a) for c, a in zip(cor, alvo)) < 40 for cor in cores)

    def test_sem_telefone_a_imagem_muda(self, marca, imagem):
        sem = render.desenhar(marca, render.Dados(DADOS.nome, DADOS.cargo, DADOS.email))
        assert sem.tobytes() != imagem.tobytes()

        # A linha do telefone fica logo abaixo do e-mail, à esquerda. Sem
        # telefone, aquela faixa da coluna esquerda tem de estar vazia.
        faixa = (marca.margem, 214, marca.margem + 300, 244)
        assert _tem_tinta(imagem.crop(faixa)), "o telefone não foi desenhado"
        assert not _tem_tinta(sem.crop(faixa)), "sobrou tinta onde o telefone estaria"

    def test_nomes_diferentes_geram_imagens_diferentes(self, marca, imagem):
        outra = render.desenhar(marca, render.Dados("Bruno Lima", DADOS.cargo, DADOS.email))
        assert outra.tobytes() != imagem.tobytes()

    def test_o_mesmo_dado_gera_a_mesma_imagem(self, marca, imagem):
        assert render.desenhar(marca, DADOS).tobytes() == imagem.tobytes()


class TestTextoLongo:
    """Nome comprido encolhe a fonte; não vaza nem é truncado."""

    LONGO = render.Dados(
        nome="Maria Fernanda Albuquerque do Nascimento Silva",
        cargo="Coordenadora de Comunicação Institucional e Marketing",
        email="maria.fernanda.albuquerque@nerdresolve.com",
        telefone="+55 (21) 99999-9999",
    )

    def test_nao_invade_a_coluna_das_redes(self, marca):
        imagem = render.desenhar(marca, self.LONGO)
        # A coluna social começa em margem+336, e a faixa logo antes dela é a
        # zona de respiro. A medição começa abaixo da onda, que cruza a imagem
        # inteira de propósito e não é conteúdo.
        inicio_social = marca.margem + 336
        respiro = imagem.crop((inicio_social - 14, 60, inicio_social - 2, imagem.height))
        assert not _tem_tinta(respiro), "o texto da esquerda encostou nas redes"

    def test_o_nome_quebra_em_vez_de_sumir(self, marca):
        """Nome que não cabe numa linha ocupa duas, e nenhuma palavra se perde."""
        curto = render.desenhar(marca, render.Dados("Ana Souza", "Dev", "a@b.com"))
        longo = render.desenhar(marca, self.LONGO)
        assert _pinta_ate(longo) > _pinta_ate(curto)

    def test_continua_dentro_da_altura(self, marca):
        imagem = render.desenhar(marca, self.LONGO)
        assert _pinta_ate(imagem) <= imagem.height - 4

    def test_a_imagem_cresce_para_acomodar(self, marca):
        curta = render.desenhar(marca, DADOS)
        assert render.desenhar(marca, self.LONGO).height > curta.height


class TestFaixas:
    @pytest.mark.parametrize("faixa", ["onda", "barra", "nenhuma"])
    def test_toda_faixa_produz_imagem_valida(self, marca, faixa):
        variante = type(marca)(**{**marca.__dict__, "faixa": faixa})
        imagem = render.desenhar(variante, DADOS)
        assert imagem.width == marca.largura
        assert imagem.height >= marca.altura
        assert _pinta_ate(imagem) <= imagem.height - 4

    def test_sem_faixa_nao_ha_tinta_na_borda_esquerda(self, marca):
        """Sem faixa, o topo à esquerda fica vazio — o logo continua à direita."""
        variante = type(marca)(**{**marca.__dict__, "faixa": "nenhuma"})
        imagem = render.desenhar(variante, DADOS)
        assert not _tem_tinta(imagem.crop((0, 0, marca.largura // 2, 20)))

    def test_a_faixa_pinta_a_borda_esquerda(self, marca):
        """Com faixa, a onda cruza a imagem e alcança a borda esquerda."""
        imagem = render.desenhar(marca, DADOS)
        assert _tem_tinta(imagem.crop((0, 0, marca.largura // 2, 40)))


class TestSaida:
    def test_gera_png(self, imagem):
        dados = render.para_png(imagem)
        assert dados[:8] == b"\x89PNG\r\n\x1a\n"

    def test_o_arquivo_e_leve_o_bastante_para_e_mail(self, imagem):
        # Assinatura pesada é rejeitada ou recomprimida por cliente de e-mail.
        assert len(render.para_png(imagem)) < 150 * 1024
