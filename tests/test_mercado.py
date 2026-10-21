"""Fatos de mercado da CONAB por UF, lidos do snapshot local (sem internet)."""

import socket

import pytest

from dominio.mercado import carregar_catalogo, fatos_mercado, ler_precos


@pytest.fixture(scope="module")
def precos():
    return ler_precos()


def test_fatos_mercado_mg_funciona_offline(monkeypatch):
    def sem_rede(*args, **kwargs):
        raise AssertionError("fatos_mercado tentou acessar a rede")

    monkeypatch.setattr(socket.socket, "connect", sem_rede)
    fatos = fatos_mercado("MG")
    assert set(fatos) == {
        "preco_leite_uf",
        "preco_leite_uf_media_12m",
        "preco_milho_uf",
        "preco_diesel_uf",
        "troca_leite_milho_uf",
        "troca_leite_milho_uf_media_12m",
    }


def test_valores_de_mg_batem_com_base_md(precos):
    # base.md, seção 10: MG em 09/2026.
    fatos = fatos_mercado("MG", precos=precos)
    assert fatos["preco_leite_uf"]["valor"] == pytest.approx(3.04)
    assert fatos["preco_leite_uf_media_12m"]["valor"] == pytest.approx(2.56, abs=0.005)
    assert fatos["preco_milho_uf"]["valor"] == pytest.approx(1.07)
    assert fatos["preco_diesel_uf"]["valor"] == pytest.approx(6.69)
    assert fatos["troca_leite_milho_uf"]["valor"] == pytest.approx(2.84, abs=0.005)
    assert fatos["troca_leite_milho_uf_media_12m"]["valor"] == pytest.approx(
        2.57, abs=0.005
    )


def test_cada_fato_traz_fonte_periodo_e_unidade(precos):
    fonte = carregar_catalogo()["fonte"]
    for fato in fatos_mercado("MG", precos=precos).values():
        assert fato["fonte"] == fonte
        assert fato["periodo"]
        assert fato["unidade"]
    fatos = fatos_mercado("MG", precos=precos)
    assert fatos["preco_leite_uf"]["periodo"] == "09/2026"
    assert (
        fatos["preco_leite_uf_media_12m"]["periodo"] == "10/2025 a 09/2026 (12 meses)"
    )


def test_media_de_12_meses_diz_quantos_meses_entraram(precos):
    # O AC não tem leite de 01 a 04/2026: a média usa 8 meses, e o período diz isso.
    fatos = fatos_mercado("AC", precos=precos)
    assert fatos["preco_leite_uf_media_12m"]["periodo"] == "10/2025 a 09/2026 (8 meses)"


def test_mes_pedido_usa_ultimo_preco_disponivel_do_insumo(precos):
    # Em MG não há diesel em 01/2026; vale o último antes disso, com a data dele.
    fatos = fatos_mercado("MG", (2026, 1), precos=precos)
    assert fatos["preco_leite_uf"]["valor"] == pytest.approx(2.11)
    assert fatos["preco_leite_uf"]["periodo"] == "01/2026"
    assert fatos["preco_diesel_uf"]["periodo"] == "11/2025"


def test_uf_sem_cotacao_nao_gera_fato(precos):
    # AM não tem milho na base: o fato não entra (e não vira zero), nem a troca.
    fatos = fatos_mercado("AM", precos=precos)
    assert "preco_leite_uf" in fatos
    assert "preco_milho_uf" not in fatos
    assert "troca_leite_milho_uf" not in fatos
    assert fatos_mercado("XX", precos=precos) == {}


def test_uf_aceita_minusculas_e_espacos(precos):
    assert fatos_mercado(" mg ", precos=precos) == fatos_mercado("MG", precos=precos)


def test_valor_fora_da_faixa_e_descartado():
    # Faixa do leite apertada para [3.0, 20.0]: em MG, 01/2026 (R$ 2,11) fica fora.
    catalogo = carregar_catalogo()
    leite = next(p for p in catalogo["produtos"] if p["nome"] == "leite")
    leite["faixa"] = [3.0, 20.0]
    precos = ler_precos(catalogo=catalogo)
    janeiro = fatos_mercado("MG", (2026, 1), precos=precos, catalogo=catalogo)
    assert "preco_leite_uf" not in janeiro  # descartado, e não vira zero
    setembro = fatos_mercado("MG", (2026, 9), precos=precos, catalogo=catalogo)
    assert setembro["preco_leite_uf"]["valor"] == pytest.approx(3.04)
