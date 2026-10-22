"""Controles da simulação de cenários econômicos."""

from __future__ import annotations

import streamlit as st

from dominio.diagnostico import simular
from motor.inferencia import Resultado
from motor.regras import Base

EXPLICACOES_SITUACAO: dict[str, str] = {
    "lucro": "A receita paga o Custo Total (CT), incluindo a remuneração do capital investido. Há lucro econômico e viabilidade no longo prazo.",
    "medio_prazo": "A receita paga o Custo Operacional Total (COT), mas não o CT. A atividade se mantém no médio prazo, porém ainda não remunera todo o capital.",
    "curto_prazo": "A receita paga apenas o Custo Operacional Efetivo (COE), os desembolsos do mês. A atividade sobrevive no curto prazo, mas não cobre todos os custos.",
    "prejuizo": "A receita não paga nem o COE. Falta dinheiro para cobrir os desembolsos operacionais do mês: há prejuízo operacional.",
}


def _rotulo_situacao(situacao: str) -> str:
    return {
        "lucro": "Lucro",
        "medio_prazo": "Médio prazo",
        "curto_prazo": "Curto prazo",
        "prejuizo": "Prejuízo",
    }.get(situacao, situacao.capitalize())


def _situacao(resultado: Resultado) -> str:
    fato = resultado.memoria.valor("situacao_economica")
    return str(fato.valor) if fato is not None else "sem_classificacao"


def _explicacao_situacao(situacao: str) -> str:
    return EXPLICACOES_SITUACAO.get(
        situacao,
        "Não foi possível detalhar esta situação com os dados disponíveis.",
    )


def renderizar_simulacao(resultado_original: Resultado, base: Base) -> None:
    """Renderiza sliders e compara o cenário recalculado ao parecer original."""
    st.subheader("Simulação “e se?”")
    st.caption(
        "Ajuste os valores para explorar cenários. O parecer original não é alterado."
    )

    colunas = st.columns(3)
    with colunas[0]:
        preco = st.slider(
            "Preço do leite",
            min_value=-30,
            max_value=30,
            value=0,
            format="%d%%",
            key="simulacao_preco_leite",
        )
    with colunas[1]:
        concentrado = st.slider(
            "Custo do concentrado",
            min_value=-30,
            max_value=30,
            value=0,
            format="%d%%",
            key="simulacao_custo_concentrado",
        )
    with colunas[2]:
        producao = st.slider(
            "Produção de leite",
            min_value=-20,
            max_value=20,
            value=0,
            format="%d%%",
            key="simulacao_producao",
        )

    variacoes = {
        "preco_leite_fazenda": preco / 100,
        "custo_concentrado": concentrado / 100,
        "producao_litros": producao / 100,
    }
    simulado = simular(resultado_original, variacoes, base=base)
    original = _situacao(resultado_original)
    novo = _situacao(simulado)

    resultado_colunas = st.columns(2)
    resultado_colunas[0].metric("Situação original", _rotulo_situacao(original))
    resultado_colunas[1].metric("Situação simulada", _rotulo_situacao(novo))
    explicacoes = st.columns(2)
    for coluna, titulo, situacao in (
        (explicacoes[0], "Original", original),
        (explicacoes[1], "Simulada", novo),
    ):
        with coluna:
            st.markdown(
                f"""
                <div class="el-explicacao-situacao">
                    <strong>{titulo}: {_rotulo_situacao(situacao)}</strong>
                    <div>{_explicacao_situacao(situacao)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.caption(
        "Como ler: prejuízo = receita abaixo do COE; curto prazo = receita entre "
        "COE e COT; médio prazo = receita entre COT e CT; lucro = receita a partir do CT."
    )
    if original == novo:
        st.info("Neste cenário, a situação econômica não mudou.")
    else:
        st.success("A variação cruzou um limiar e mudou a situação econômica.")
