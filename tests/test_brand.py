"""A configuração de marca: o que ela aceita e o que ela recusa.

O alvo destes testes é quem forka o projeto e edita o `brand.json` sem ler o
código. Um erro de digitação precisa virar mensagem com o caminho do campo, não
um KeyError trinta linhas adiante.
"""

from __future__ import annotations

import json

import pytest

from app import brand


@pytest.fixture
def marca_minima(tmp_path, monkeypatch):
    """Uma marca válida em disco, para os testes mexerem sem tocar em brands/."""

    def escrever(**alteracoes):
        config = {
            "nome": "Teste",
            "cores": {"marca": "#7C3AED"},
            "perfis": [{"id": "padrao", "nome": "Padrão"}],
        }
        config.update(alteracoes)

        diretorio = tmp_path / "brands" / "teste"
        diretorio.mkdir(parents=True, exist_ok=True)
        (diretorio / "brand.json").write_text(json.dumps(config), encoding="utf-8")

        monkeypatch.setattr(brand, "DIR_MARCAS", tmp_path / "brands")
        return brand.carregar("teste")

    return escrever


class TestCores:
    def test_hexadecimal_vira_rgb(self, marca_minima):
        assert marca_minima().cores["marca"] == (124, 58, 237)

    def test_cor_ausente_usa_o_padrao(self, marca_minima):
        marca = marca_minima(cores={})
        assert marca.cores["marca"] == (124, 58, 237)
        assert marca.cores["fundo"] == (255, 255, 255)

    @pytest.mark.parametrize("ruim", ["#7C3AE", "roxo", "rgb(124,58,237)", "7C3AED", "#7C3AEDD"])
    def test_cor_invalida_diz_qual_campo(self, marca_minima, ruim):
        with pytest.raises(brand.ErroDeMarca, match=r"cores\.marca"):
            marca_minima(cores={"marca": ruim})

    def test_hexadecimal_minusculo_tambem_vale(self, marca_minima):
        assert marca_minima(cores={"marca": "#7c3aed"}).cores["marca"] == (124, 58, 237)


class TestPerfis:
    def test_sem_perfis_ganha_um_padrao(self, marca_minima):
        marca = marca_minima(perfis=[])
        assert len(marca.perfis) == 1
        assert marca.perfis[0].id == "padrao"

    def test_perfil_sem_id_e_recusado(self, marca_minima):
        with pytest.raises(brand.ErroDeMarca, match=r"perfis\[0\].*'id'"):
            marca_minima(perfis=[{"nome": "Sem id"}])

    def test_ids_repetidos_sao_recusados(self, marca_minima):
        with pytest.raises(brand.ErroDeMarca, match="repetidos"):
            marca_minima(perfis=[{"id": "a"}, {"id": "a"}])

    def test_buscar_perfil_inexistente_lista_os_validos(self, marca_minima):
        marca = marca_minima(perfis=[{"id": "vendas"}, {"id": "suporte"}])
        with pytest.raises(brand.ErroDeMarca, match="vendas, suporte"):
            marca.perfil("juridico")

    def test_perfil_pode_ter_cor_propria(self, marca_minima):
        marca = marca_minima(perfis=[{"id": "verde", "cor": "#00FF00"}])
        assert marca.perfil("verde").cor == (0, 255, 0)


class TestTipografia:
    def test_peso_inexistente_lista_os_validos(self, marca_minima):
        with pytest.raises(brand.ErroDeMarca, match="regular, semibold, bold"):
            marca_minima(tipografia={"nome": {"peso": "black"}})

    def test_cor_nao_declarada_e_recusada(self, marca_minima):
        with pytest.raises(brand.ErroDeMarca, match=r"tipografia\.nome\.cor"):
            marca_minima(tipografia={"nome": {"cor": "roxinho"}})

    def test_tipografia_parcial_preserva_o_resto_do_padrao(self, marca_minima):
        marca = marca_minima(tipografia={"nome": {"tamanho": 30}})
        assert marca.estilos["nome"].tamanho == 30
        assert marca.estilos["nome"].peso == "bold"       # não foi informado
        assert marca.estilos["cargo"].tamanho == 15       # nem tocado


class TestArquivos:
    def test_logo_ausente_diz_o_caminho(self, marca_minima):
        with pytest.raises(brand.ErroDeMarca, match="não encontrado"):
            marca_minima(logo={"arquivo": "nao-existe.png"})

    def test_json_quebrado_aponta_a_linha(self, tmp_path, monkeypatch):
        diretorio = tmp_path / "brands" / "quebrada"
        diretorio.mkdir(parents=True)
        (diretorio / "brand.json").write_text('{"nome": "x",}', encoding="utf-8")
        monkeypatch.setattr(brand, "DIR_MARCAS", tmp_path / "brands")

        with pytest.raises(brand.ErroDeMarca, match="linha"):
            brand.carregar("quebrada")

    def test_marca_inexistente_lista_as_que_existem(self, marca_minima):
        marca_minima()  # cria "teste" e reaponta DIR_MARCAS
        with pytest.raises(brand.ErroDeMarca, match="teste"):
            brand.carregar("fantasma")


class TestFaixa:
    @pytest.mark.parametrize("faixa", ["onda", "barra", "nenhuma"])
    def test_faixas_validas(self, marca_minima, faixa):
        assert marca_minima(assinatura={"faixa": faixa}).faixa == faixa

    def test_faixa_invalida_lista_as_validas(self, marca_minima):
        with pytest.raises(brand.ErroDeMarca, match="onda, barra, nenhuma"):
            marca_minima(assinatura={"faixa": "diagonal"})


def test_a_marca_do_repositorio_carrega():
    """A marca que acompanha o projeto precisa estar sempre válida."""
    marca = brand.carregar("nerdresolve")
    assert marca.nome == "NerdResolve"
    assert marca.cores["marca"] == (124, 58, 237)
    assert marca.logo and marca.logo.exists()
