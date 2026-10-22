"""Revisão antes do envio e parecer do diagnóstico."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import streamlit as st

from interface.formulario import SecaoComPerguntas
from motor.inferencia import Resultado
from motor.regras import Base, Regra


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


def renderizar_parecer(resultado: Resultado, base: Base) -> None:
    """Parecer v0 (#10): só lê o Resultado do motor; a tela completa é a #13."""
    regras = {r.id: r for r in base.regras}
    _situacao(resultado, regras)
    _outras_conclusoes(resultado, base)
    _indicadores(resultado, base)


def _rotulo(valor: Any) -> str:
    return str(valor).replace("_", " ")


def _situacao(resultado: Resultado, regras: dict[str, Regra]) -> None:
    fato = resultado.memoria.valor("situacao_economica")
    with st.container(border=True):
        st.caption("Situação econômica")
        if fato is None:
            st.info(
                "Com os dados informados, o motor não concluiu a situação econômica."
            )
            return
        st.markdown(
            f'<div class="el-situacao">{_rotulo(fato.valor)}</div>',
            unsafe_allow_html=True,
        )
        regra = regras[fato.origens[-1].detalhe]
        st.write(f"Confiança {fato.cf:.0%} · {regra.id}: {regra.descricao}")


def _outras_conclusoes(resultado: Resultado, base: Base) -> None:
    st.subheader("Outras conclusões")
    fatos = [
        fato
        for var in base.variaveis.values()
        if var.grupo == "conclusoes" and var.nome != "situacao_economica"
        for fato in resultado.memoria.valores(var.nome)
    ]
    if not fatos:
        st.caption("Nenhuma outra regra disparou com os dados informados.")
    for fato in fatos:
        regras = ", ".join(o.detalhe for o in fato.origens)
        descricao = base.variaveis[fato.nome].descricao
        st.write(f"{descricao}: **{_rotulo(fato.valor)}** · {fato.cf:.0%} · {regras}")


def _indicadores(resultado: Resultado, base: Base) -> None:
    st.subheader("Indicadores calculados")
    calculados = [
        f for f in resultado.memoria.fatos() if f.origens[-1].tipo == "calculado"
    ]
    st.table(
        {
            base.variaveis[f.nome].descricao: formatar(
                f.valor, base.variaveis[f.nome].unidade
            )
            for f in calculados
        }
    )
