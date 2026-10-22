"""Testes de conformidade para operação 100% offline e máquina limpa (#21).

Garante que o diagnóstico, mercado CONAB, benchmark IBGE e a interface Streamlit
funcionam sem conexão com a internet (sem Wi-Fi), sem requisições HTTP externas e
sem chamadas de rede para fora do loopback local.
"""

from __future__ import annotations

import socket
from pathlib import Path

import pytest
import yaml
from streamlit.testing.v1 import AppTest

from dominio.benchmark import fatos_benchmark
from dominio.diagnostico import diagnosticar
from dominio.mercado import fatos_mercado

RAIZ = Path(__file__).resolve().parent.parent
PASTA_CASOS = RAIZ / "dados" / "casos"
ARQUIVOS_CASOS = sorted(
    [arq.name for arq in PASTA_CASOS.glob("*.yaml") if arq.is_file()]
)


@pytest.fixture(autouse=True)
def bloquear_rede_externa(monkeypatch: pytest.MonkeyPatch):
    """Bloqueia qualquer conexão externa de rede durante os testes.

    Permite apenas loopback local (127.0.0.1, localhost, ::1) exigido pelo
    asyncio / IPC interno do Python e do Streamlit no Windows.
    """
    orig_connect = socket.socket.connect

    def connect_seguro(self, address):
        host = address[0] if isinstance(address, tuple) else address
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise AssertionError(
                f"Acesso à rede externa bloqueado no modo offline: {address}"
            )
        return orig_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", connect_seguro)


@pytest.mark.parametrize("nome_caso", ARQUIVOS_CASOS)
def test_todos_os_casos_rodam_offline(nome_caso: str):
    """Garante que todos os casos de referência executam sem tocar na rede."""
    dados = yaml.safe_load((PASTA_CASOS / nome_caso).read_text(encoding="utf-8"))
    entradas = dados.get("entradas", {})
    resultado = diagnosticar(entradas)
    assert len(resultado.memoria.fatos()) > 0
    assert resultado.memoria.tem("situacao_economica")


@pytest.mark.parametrize("uf", ["MG", "SP", "PR", "GO", "RS", "BA", "SC"])
def test_mercado_conab_funciona_offline(uf: str):
    """Garante que a base CONAB responde para diversas UFs sem tocar na internet."""
    fatos = fatos_mercado(uf, (2026, 9))
    assert "preco_leite_uf" in fatos
    assert fatos["preco_leite_uf"]["valor"] > 0


@pytest.mark.parametrize("uf", ["MG", "SP", "PR", "SC", "RS", "GO"])
def test_benchmark_ibge_funciona_offline(uf: str):
    """Garante que as tabelas 74 e 94 da PPM/IBGE respondem offline."""
    fatos = fatos_benchmark(uf, 2026)
    assert "produtividade_regional_ibge" in fatos
    assert fatos["produtividade_regional_ibge"]["valor"] > 0


def test_app_streamlit_inicia_e_navega_offline():
    """Garante que o app Streamlit inicia e permite navegação sem conexão externa."""
    app = AppTest.from_file(str(RAIZ / "app.py")).run()
    assert not app.exception

    # Verifica rádio de navegação lateral
    assert len(app.sidebar.radio) > 0

    # Navega para Base de conhecimento
    app.sidebar.radio[0].set_value("Base de conhecimento").run()
    assert not app.exception
    tela = " ".join(m.value for m in app.markdown)
    assert "R-IND-01" in tela

    # Volta para Diagnóstico
    app.sidebar.radio[0].set_value("Diagnóstico").run()
    assert not app.exception
