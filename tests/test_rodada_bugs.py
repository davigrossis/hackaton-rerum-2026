"""Rodada de bugs cruzada (#22): casos conhecidos + 2 fazendas inventadas por outro dev.

Critérios de aceite da issue: nenhuma exceção e casos corretos. As fazendas inventadas
ficam em tests/fixtures/rodada_bugs/, com as contas feitas à mão nos comentários, e
disparam as regras que nenhum caso conhecido dispara ponta a ponta.
"""

from __future__ import annotations

import random
from pathlib import Path

import pytest
import yaml
from streamlit.testing.v1 import AppTest

from dominio.diagnostico import LIMITES_SIMULACAO, diagnosticar, simular
from interface.formulario import CHAVE_RESULTADO, PREFIXO_CAMPO, problemas
from motor.explicacao import como, por_que
from motor.inferencia import Resultado, perguntas_pendentes
from motor.regras import carregar_base

RAIZ = Path(__file__).resolve().parent.parent
PASTA_INVENTADAS = Path(__file__).resolve().parent / "fixtures" / "rodada_bugs"
BASE = carregar_base()


def _carregar(pasta: Path) -> list[dict]:
    return [
        yaml.safe_load(arq.read_text(encoding="utf-8"))
        for arq in sorted(pasta.glob("*.yaml"))
    ]


INVENTADAS = _carregar(PASTA_INVENTADAS)
CONHECIDOS = _carregar(RAIZ / "dados" / "casos")
TODAS = CONHECIDOS + INVENTADAS
IDS_INVENTADAS = [f["id"] for f in INVENTADAS]
IDS_TODAS = [f["id"] for f in TODAS]


def test_duas_fazendas_inventadas():
    assert IDS_INVENTADAS == ["alta_producao_mastite", "familiar_prejuizo"]


@pytest.mark.parametrize("fazenda", INVENTADAS, ids=IDS_INVENTADAS)
def test_fazenda_inventada_passa_no_formulario(fazenda):
    secoes = [(s, [p for p in BASE.perguntas if p.secao == s.id]) for s in BASE.secoes]
    assert problemas(secoes, fazenda["entradas"]) == []


@pytest.mark.parametrize("fazenda", INVENTADAS, ids=IDS_INVENTADAS)
def test_fazenda_inventada_bate_com_as_contas_a_mao(fazenda):
    memoria = diagnosticar(fazenda["entradas"], base=BASE).memoria
    esperado = fazenda["esperado"]

    for nome, valor in esperado["externos"].items():
        assert memoria.valor(nome).origens[-1].tipo == "externo", nome
        assert memoria.valor(nome).valor == pytest.approx(valor, abs=1e-4), nome

    for nome, valor in esperado["indicadores"].items():
        assert memoria.valor(nome).valor == pytest.approx(valor, abs=0.01), nome
    # Opcional vazio não vira zero: o indicador que depende dele não existe.
    for nome in esperado["indicadores_ausentes"]:
        assert not memoria.tem(nome), nome


@pytest.mark.parametrize("fazenda", INVENTADAS, ids=IDS_INVENTADAS)
def test_fazenda_inventada_conclui_o_esperado(fazenda):
    resultado = diagnosticar(fazenda["entradas"], base=BASE)
    memoria = resultado.memoria
    esperado = fazenda["esperado"]

    assert memoria.valor("situacao_economica").valor == esperado["situacao_economica"]

    concluidos = {
        c.fato: (c.valor, c.cf_fato) for c in resultado.traco if c.camada == "indicador"
    }
    assert concluidos.keys() == esperado["indicadores_concluidos"].keys()
    for fato, alvo in esperado["indicadores_concluidos"].items():
        assert concluidos[fato] == (alvo["valor"], pytest.approx(alvo["cf"])), fato

    bloqueios = {
        c.escolhida: sorted(b.regra for b in c.bloqueadas)
        for c in resultado.traco
        if c.bloqueadas
    }
    assert bloqueios == esperado["bloqueadas"]

    # Conjunto exato e CF combinado, como no test_casos.py (#12).
    for fato, chave in (("causa", "causas"), ("recomendacao", "recomendacoes")):
        obtidos = {f.valor: f.cf for f in memoria.valores(fato)}
        assert obtidos == pytest.approx(esperado[chave]), chave


def test_casos_e_fazendas_disparam_toda_regra_da_base():
    """Toda regra da base dispara ponta a ponta em algum caso conhecido ou inventado."""
    disparadas = {
        ciclo.escolhida
        for fazenda in TODAS
        for ciclo in diagnosticar(fazenda["entradas"], base=BASE).traco
    }
    assert {r.id for r in BASE.regras} - disparadas == set()


# --- Na tela: o formulário preenchido campo a campo, como o usuário faz ---


def _clicar(botoes, rotulo: str) -> None:
    next(b for b in botoes if b.label == rotulo).click().run()


def _preencher_etapa(app: AppTest, entradas: dict) -> None:
    widgets = [*app.selectbox, *app.text_input, *app.number_input]
    for widget in widgets:
        if not widget.key or not widget.key.startswith(PREFIXO_CAMPO):
            continue
        nome = widget.key.removeprefix(PREFIXO_CAMPO)
        if nome in entradas:
            widget.set_value(entradas[nome])
    app.run()


@pytest.mark.parametrize("fazenda", TODAS, ids=IDS_TODAS)
def test_formulario_digitado_chega_ao_parecer(fazenda):
    entradas = fazenda["entradas"]
    situacao = fazenda["esperado"]["situacao_economica"]
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()

    for _ in BASE.secoes:
        _preencher_etapa(app, entradas)
        _clicar(app.button, "Avançar")
    _clicar(app.button, "Gerar diagnóstico")

    assert not app.exception
    resultado = app.session_state[CHAVE_RESULTADO]
    assert isinstance(resultado, Resultado)
    # O formulário entregou ao motor exatamente as respostas da fazenda.
    respostas = {
        f.nome: f.valor
        for f in resultado.memoria.fatos()
        if f.origens[-1].tipo == "usuario"
    }
    assert respostas == entradas
    assert perguntas_pendentes(BASE, resultado.memoria, resultado) == []
    tela = " ".join(m.value for m in app.markdown)
    assert f'<div class="el-situacao">{situacao}</div>' in tela
    assert "Diagnóstico Econômico" in [s.value for s in app.subheader]


# --- Fazendas aleatórias: nenhuma exceção e situação coerente com Matsunaga ---

MESES = ["09/2026", "01/2026", "10/2025", "10/2026", "01/2000", "12/2099"]


def _resposta_aleatoria(rng: random.Random, pergunta) -> object:
    if pergunta.tipo == "escolha":
        return rng.choice(pergunta.opcoes)
    if pergunta.tipo == "mes":
        return rng.choice(MESES)
    minimo, maximo = pergunta.faixa
    sorteio = rng.random()
    if sorteio < 0.15:
        valor = minimo
    elif sorteio < 0.30:
        valor = maximo
    else:
        # Escala sorteada: sem ela, quase toda fazenda teria valores perto do máximo.
        escala = rng.choice([1e-4, 1e-2, 1.0])
        valor = rng.uniform(minimo, minimo + (maximo - minimo) * escala)
    return round(valor) if pergunta.tipo == "inteiro" else float(valor)


def _fazenda_aleatoria(rng: random.Random) -> dict:
    return {
        p.id: _resposta_aleatoria(rng, p)
        for p in BASE.perguntas
        if p.obrigatoria or rng.random() < 0.7
    }


def _situacao_coerente(resultado: Resultado) -> None:
    memoria = resultado.memoria
    situacao = memoria.valor("situacao_economica")
    receita, coe, cot, ct = (
        memoria.valor(n).valor if memoria.tem(n) else None
        for n in ("receita_total", "coe", "cot", "ct")
    )
    if situacao is None:
        # Sem CT, a fazenda que cobre o COT fica sem situação (decisão da #8).
        assert ct is None and receita >= cot
        return
    faixas = {
        "lucro": lambda: receita >= ct,
        "medio_prazo": lambda: cot <= receita < ct,
        "curto_prazo": lambda: coe <= receita < cot,
        "prejuizo": lambda: receita < coe,
    }
    assert faixas[situacao.valor]()
    causas = {f.valor for f in memoria.valores("causa")}
    if situacao.valor == "lucro":
        assert causas <= {"qualidade_leite"}


@pytest.mark.parametrize("semente", range(4))
def test_fazendas_aleatorias_nao_quebram(semente):
    rng = random.Random(semente)
    for _ in range(25):
        respostas = _fazenda_aleatoria(rng)
        numericas = [k for k in respostas if k not in ("uf", "mes_referencia")]
        estimados = frozenset(k for k in numericas if rng.random() < 0.1)

        resultado = diagnosticar(respostas, estimados=estimados, base=BASE)

        _situacao_coerente(resultado)
        assert all(0 < f.cf <= 1 for f in resultado.memoria.fatos())
        for ciclo in resultado.traco:
            assert como(resultado, ciclo.fato, ciclo.valor)
        for pergunta in BASE.perguntas:
            por_que(BASE, pergunta.id, resultado)
        # Simulação nos limites dos sliders, para cima ou para baixo.
        variacoes = {
            nome: rng.choice([-1, 1]) * limite
            for nome, limite in LIMITES_SIMULACAO.items()
        }
        simulado = simular(resultado, variacoes, base=BASE)
        _situacao_coerente(simulado)
