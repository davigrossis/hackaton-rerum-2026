"""Testes das regras da base real (conhecimento/regras.yaml), uma a uma.

Os fatos entram direto na memória, sem calcular indicadores: aqui se testa só a base.
A ponta a ponta, com fazendas completas, fica no test_casos.py.
"""

from __future__ import annotations

import pytest

from motor.inferencia import Resultado, inferir
from motor.memoria import Memoria
from motor.regras import carregar_base

BASE = carregar_base()

# Marcas da régua de custos nos casos de situação (R$/mês): COE < COT < CT.
COE, COT, CT = 60000.0, 72000.0, 77000.0
CUSTOS = {"coe": COE, "cot": COT, "ct": CT}


def _inferir(**fatos: float) -> Resultado:
    memoria = Memoria()
    for nome, valor in fatos.items():
        memoria.adicionar(nome, valor, origem="calculado")
    return inferir(BASE, memoria)


def _disparadas(resultado: Resultado) -> list[str]:
    return [ciclo.escolhida for ciclo in resultado.traco]


# Um caso por regra: os fatos, a regra que deve disparar e a conclusão dela.
CASOS = [
    pytest.param(
        {"preco_leite_fazenda": 2.90, "preco_leite_uf": 3.04},
        "R-IND-01", "preco_leite", "abaixo_mercado",
        id="R-IND-01",
    ),
    pytest.param(
        {"pct_vacas_lactacao": 60.0},
        "R-IND-02", "lactacao_nivel", "baixa",
        id="R-IND-02",
    ),
    pytest.param(
        {"litros_vaca_dia": 8.0},
        "R-IND-03", "produtividade_nivel", "baixa",
        id="R-IND-03",
    ),
    pytest.param(
        {"pct_concentrado_receita": 45.0},
        "R-IND-04", "concentrado_receita_nivel", "alto",
        id="R-IND-04",
    ),
    pytest.param(
        {"pct_alimentacao_coe": 68.0, "litros_vaca_dia": 20.0},
        "R-IND-05", "custo_alimentar_nivel", "alto",
        id="R-IND-05",
    ),
    pytest.param(
        {"pct_alimentacao_coe": 68.0, "litros_vaca_dia": 28.0},
        "R-IND-06", "custo_alimentar_nivel", "adequado",
        id="R-IND-06",
    ),
    pytest.param(
        {"troca_leite_milho_uf": 2.0, "troca_leite_milho_uf_media_12m": 2.5},
        "R-IND-07", "troca_leite_milho_nivel", "desfavoravel",
        id="R-IND-07",
    ),
    pytest.param(
        {"ccs": 600.0},
        "R-IND-08", "qualidade_leite", "fora_in76",
        id="R-IND-08",
    ),
    pytest.param(
        {"cpp": 400.0},
        "R-IND-09", "qualidade_leite", "fora_in76",
        id="R-IND-09",
    ),
    pytest.param(
        {"receita_total": 80000.0, **CUSTOS},
        "R-SIT-01", "situacao_economica", "lucro",
        id="R-SIT-01",
    ),
    pytest.param(
        {"receita_total": 75000.0, **CUSTOS},
        "R-SIT-02", "situacao_economica", "medio_prazo",
        id="R-SIT-02",
    ),
    pytest.param(
        {"receita_total": 65000.0, **CUSTOS},
        "R-SIT-03", "situacao_economica", "curto_prazo",
        id="R-SIT-03",
    ),
    pytest.param(
        {"receita_total": 50000.0, **CUSTOS},
        "R-SIT-04", "situacao_economica", "prejuizo",
        id="R-SIT-04",
    ),
]  # fmt: skip


@pytest.mark.parametrize(("fatos", "regra", "fato", "valor"), CASOS)
def test_regra_dispara_e_conclui(fatos: dict, regra: str, fato: str, valor: str):
    resultado = _inferir(**fatos)
    assert regra in _disparadas(resultado)
    assert resultado.memoria.valor(fato).valor == valor


def test_toda_regra_da_base_tem_caso():
    """Regra do AGENTS.md: toda regra precisa de ao menos um caso que a exercite."""
    com_caso = {caso.values[1] for caso in CASOS}
    sem_caso = sorted({r.id for r in BASE.regras} - com_caso)
    assert not sem_caso, f"Regras sem caso em CASOS: {sem_caso}"


def test_regras_com_fonte_pendente():
    """Limiar sem fonte confiável fica PENDENTE; ao achar a fonte, atualize esta lista."""
    assert [r.id for r in BASE.regras_pendentes] == [
        "R-IND-02",
        "R-IND-03",
        "R-IND-04",
        "R-IND-05",
        "R-IND-06",
    ]


@pytest.mark.parametrize(
    ("fatos", "fato"),
    [
        ({"preco_leite_fazenda": 3.04, "preco_leite_uf": 3.04}, "preco_leite"),
        ({"pct_vacas_lactacao": 70.0}, "lactacao_nivel"),
        ({"litros_vaca_dia": 10.0}, "produtividade_nivel"),
        ({"pct_concentrado_receita": 40.0}, "concentrado_receita_nivel"),
        (
            {"pct_alimentacao_coe": 65.0, "litros_vaca_dia": 28.0},
            "custo_alimentar_nivel",
        ),
        (
            {"troca_leite_milho_uf": 2.5, "troca_leite_milho_uf_media_12m": 2.5},
            "troca_leite_milho_nivel",
        ),
        ({"ccs": 500.0}, "qualidade_leite"),
        ({"cpp": 300.0}, "qualidade_leite"),
    ],
)
def test_indicador_no_limiar_nao_dispara(fatos: dict, fato: str):
    """As comparações são estritas: exatamente no limiar, nada é concluído."""
    assert _inferir(**fatos).memoria.valor(fato) is None


def test_ccs_ou_cpp_fora_da_in76():
    """Duas regras com a mesma conclusão fazem um OU; o CF combinado fica em 1,0."""
    resultado = _inferir(ccs=600.0, cpp=400.0)
    assert {"R-IND-08", "R-IND-09"} <= set(_disparadas(resultado))
    fato = resultado.memoria.valor("qualidade_leite")
    assert (fato.valor, fato.cf) == ("fora_in76", 1.0)
    assert [o.detalhe for o in fato.origens] == ["R-IND-08", "R-IND-09"]


def test_excecao_de_alta_producao_bloqueia_a_regra_geral():
    """Mesma prioridade: a R-IND-06 vence por ter mais condições e bloqueia a R-IND-05."""
    resultado = _inferir(pct_alimentacao_coe=68.0, litros_vaca_dia=28.0)
    fato = resultado.memoria.valor("custo_alimentar_nivel")
    assert (fato.valor, fato.cf) == ("adequado", 0.8)
    assert "R-IND-05" not in _disparadas(resultado)

    (ciclo,) = [c for c in resultado.traco if c.escolhida == "R-IND-06"]
    assert ciclo.conjunto_conflito == ("R-IND-06", "R-IND-05")
    (bloqueio,) = ciclo.bloqueadas
    assert (bloqueio.regra, bloqueio.valor_pretendido) == ("R-IND-05", "alto")


def test_excecao_nao_esconde_o_concentrado_na_receita():
    """O concentrado tem conclusão própria: a exceção da alimentação não o bloqueia."""
    resultado = _inferir(
        pct_alimentacao_coe=70.0, litros_vaca_dia=28.0, pct_concentrado_receita=45.0
    )
    assert resultado.memoria.valor("custo_alimentar_nivel").valor == "adequado"
    assert resultado.memoria.valor("concentrado_receita_nivel").valor == "alto"


@pytest.mark.parametrize(
    ("receita", "esperada"),
    [
        (50000.0, "prejuizo"),
        (59999.99, "prejuizo"),
        (COE, "curto_prazo"),  # na marca, cai na faixa de cima
        (71999.99, "curto_prazo"),
        (COT, "medio_prazo"),
        (76999.99, "medio_prazo"),
        (CT, "lucro"),
        (90000.0, "lucro"),
    ],
)
def test_situacao_cai_em_uma_faixa_so(receita: float, esperada: str):
    """As faixas não se sobrepõem: uma regra de situação dispara, sem conflito."""
    resultado = _inferir(receita_total=receita, **CUSTOS)
    situacoes = resultado.memoria.valores("situacao_economica")
    assert [f.valor for f in situacoes] == [esperada]
    assert situacoes[0].cf == 1.0
    ciclos = [c for c in resultado.traco if c.camada == "situacao"]
    assert len(ciclos) == 1
    assert ciclos[0].conjunto_conflito == (ciclos[0].escolhida,)


@pytest.mark.parametrize(
    ("receita", "esperada"),
    [
        (90000.0, None),  # cobre o COT: sem CT, não dá para dizer se há lucro
        (COT, None),
        (65000.0, "curto_prazo"),  # abaixo do COT, a situação não depende do CT
        (50000.0, "prejuizo"),
    ],
)
def test_sem_ct_lucro_e_medio_prazo_nao_disparam(receita: float, esperada: str | None):
    """Sem capital investido não há CT, e a R-SIT-01/02 esperam por ele (decisão da #8)."""
    resultado = _inferir(receita_total=receita, coe=COE, cot=COT)
    fato = resultado.memoria.valor("situacao_economica")
    assert (fato.valor if fato else None) == esperada
    assert not {"R-SIT-01", "R-SIT-02"} & set(_disparadas(resultado))
