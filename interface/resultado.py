"""Revisão antes do envio e parecer econômico com simulação "e se?"."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

from interface.formulario import SecaoComPerguntas
from interface.simulacao import renderizar_simulacao
from motor.inferencia import Resultado
from motor.regras import Base


def formatar(valor: Any, unidade: str | None) -> str:
    """Formata no padrão brasileiro (1.234,56) sem alterar o dado original."""
    if isinstance(valor, float):
        texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    elif isinstance(valor, int):
        texto = f"{valor:,}".replace(",", ".")
    else:
        texto = str(valor)
    return f"{texto} {unidade}" if unidade else texto


def renderizar_revisao(
    secoes: list[SecaoComPerguntas],
    respostas: dict[str, Any],
    achados: list[tuple[int, str]],
    ir_para: Callable[[int], None],
) -> None:
    st.subheader("Revise antes de gerar")
    if achados:
        st.warning(
            "Corrija os pontos abaixo para liberar o diagnóstico. "
            "Os campos opcionais podem ficar em branco."
        )
        for indice, mensagem in achados:
            colunas = st.columns([4, 1])
            colunas[0].write(f"• {mensagem}")
            colunas[1].button(
                "Corrigir", key=f"corrigir_{indice}_{mensagem}",
                on_click=ir_para, args=(indice,),
            )  # fmt: skip
    else:
        st.success("Tudo certo. Confira os valores e gere o diagnóstico.")

    for indice, (secao, perguntas) in enumerate(secoes):
        with st.expander(secao.titulo, expanded=False):
            linhas = {
                p.texto: formatar(respostas[p.id], p.unidade)
                if p.id in respostas
                else "— não informado"
                for p in perguntas
            }
            st.table(linhas)
            st.button(
                "Editar esta seção", key=f"editar_{indice}",
                on_click=ir_para, args=(indice,),
            )  # fmt: skip


def renderizar_resultado(resultado: Resultado, base: Base) -> None:
    """Parecer econômico do motor, seguido da simulação "e se?"."""
    with st.container(border=True):
        st.subheader("Parecer econômico")
        fato = resultado.memoria.valor("situacao_economica")
        if fato is None:
            st.warning(
                "Nenhuma regra classificou a situação econômica com os dados "
                "informados."
            )
        else:
            rotulo = str(fato.valor).replace("_", " ")
            st.caption("Situação econômica")
            st.markdown(
                f'<div class="el-situacao">{rotulo}</div>', unsafe_allow_html=True
            )
            st.caption(f"Confiança: {fato.cf:.0%}")
    renderizar_simulacao(resultado, base)