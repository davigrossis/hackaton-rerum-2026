"""Média da UF na PPM/IBGE (dominio/benchmark.py) e a regra R-IND-11, sem rede."""

from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest
import yaml

from dominio.benchmark import (
    ARQUIVO_PRODUCAO,
    ARQUIVO_VACAS,
    CODIGO_UF,
    fatos_benchmark,
    ler_tabela,
)
from dominio.diagnostico import diagnosticar
from motor.regras import carregar_base

RAIZ = Path(__file__).resolve().parent.parent
CASO = yaml.safe_load(
    (RAIZ / "dados" / "casos" / "05_benchmark_ibge.yaml").read_text(encoding="utf-8")
)


@pytest.mark.parametrize(
    ("arquivo", "esperado"),
    [
        (ARQUIVO_PRODUCAO, {"D2C": "106", "MC": "25", "D4C": "2682"}),  # leite, mil L
        (ARQUIVO_VACAS, {"D2C": "107", "MC": "24"}),  # vacas ordenhadas, cabeças
    ],
)
def test_snapshot_tem_variavel_unidade_e_as_27_ufs(arquivo: Path, esperado: dict):
    """Ao trocar o snapshot, aponta variável, unidade, produto ou UF errados."""
    linhas = json.loads(arquivo.read_text(encoding="utf-8"))[1:]
    for campo, valor in esperado.items():
        assert {linha[campo] for linha in linhas} == {valor}, campo
    assert {int(linha["D1C"]) for linha in linhas} == set(CODIGO_UF.values())


def test_codigo_uf_cobre_as_ufs_do_formulario():
    ufs = next(p.opcoes for p in carregar_base().perguntas if p.id == "uf")
    assert set(CODIGO_UF) == set(ufs)


def test_media_de_mg_calculada_a_mao():
    # PPM 2025, MG: 10.070.127 mil L de leite e 2.963.271 vacas ordenhadas.
    fato = fatos_benchmark("MG", 2026)["produtividade_regional_ibge"]
    assert fato["valor"] == pytest.approx(10070127 * 1000 / 2963271 / 365, abs=1e-4)
    assert fato["unidade"] == "L/vaca/dia"
    assert fato["periodo"] == "2025"
    assert "IBGE – PPM" in fato["fonte"]


def test_usa_o_ultimo_ano_antes_do_mes():
    fato = fatos_benchmark("MG", 2025)["produtividade_regional_ibge"]
    assert fato["periodo"] == "2024"
    assert fatos_benchmark("MG", 2024) == {}
    assert fatos_benchmark("XX", 2026) == {}


def test_simbolo_do_sidra_e_vacas_zeradas_nao_geram_fato(tmp_path):
    arquivo = tmp_path / "tabela.json"
    linhas = [
        {"V": "Valor"},
        {"D1C": "31", "D3C": "2025", "V": "..."},
        {"D1C": "35", "D3C": "2025", "V": "-"},
    ]
    arquivo.write_text(json.dumps(linhas), encoding="utf-8")
    assert ler_tabela(arquivo) == {}
    producao, vacas = {(31, 2025): 100.0}, {(31, 2025): 0.0}
    assert fatos_benchmark("MG", 2026, producao=producao, vacas=vacas) == {}


def test_caso_05_dispara_a_r_ind_11_sem_rede(monkeypatch):
    """Critérios de aceite da #18: roda offline e dispara em 1 caso."""

    def sem_rede(*args, **kwargs):
        pytest.fail("O diagnóstico não pode acessar a rede")

    monkeypatch.setattr(socket.socket, "connect", sem_rede)
    resultado = diagnosticar(CASO["entradas"])
    ciclo = next(c for c in resultado.traco if c.escolhida == "R-IND-11")
    premissa = ciclo.premissas[0]
    assert premissa.valor_fato == pytest.approx(7000 / (30 * 30))
    assert premissa.valor_alvo == pytest.approx(9.3105)
    conclusao = resultado.memoria.valor("produtividade_regional_nivel")
    assert (conclusao.valor, conclusao.cf) == ("abaixo_media", 1.0)
