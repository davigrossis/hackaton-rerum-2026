"""Revisão antes do envio e parecer provisório (mock)."""

from __future__ import annotations

from typing import Any, Callable

import streamlit as st

from interface.formulario import SecaoComPerguntas


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


def renderizar_mock(respostas: dict[str, Any]) -> None:
    with st.container(border=True):
        st.markdown(
            '<span class="el-mock">RESULTADO PROVISÓRIO (MOCK)</span>',
            unsafe_allow_html=True,
        )
        st.caption("Situação econômica")
        st.markdown('<div class="el-situacao">médio prazo</div>', unsafe_allow_html=True)
        st.write(
            "Este parecer é só uma demonstração do fluxo da tela. "
            "A classificação real virá das regras de produção e do motor "
            "de inferência, com confiança (CF) e explicação de “como?” e "
            "“por quê?” para cada conclusão."
        )
    with st.expander("Dados enviados ao diagnóstico"):
        st.json(respostas)