"""Controles da simulação de cenários econômicos."""

from __future__ import annotations

import streamlit as st

from dominio.diagnostico import simular
from motor.inferencia import Resultado
from motor.regras import Base


def _situacao(resultado: Resultado) -> str:
    fato = resultado.memoria.valor("situacao_economica")
    return str(fato.valor).replace("_", " ") if fato is not None else "sem classificação"


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
    resultado_colunas[0].metric("Situação original", original)
    resultado_colunas[1].metric("Situação simulada", novo)
    if original == novo:
        st.info("Neste cenário, a situação econômica não mudou.")
    else:
        st.success("A variação cruzou um limiar e mudou a situação econômica.")
