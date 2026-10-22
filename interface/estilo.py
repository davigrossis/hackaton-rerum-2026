"""Estilo visual: CSS leve, só fontes do sistema (a demo roda sem internet)."""

from __future__ import annotations

import streamlit as st

VERDE = "#2e6b4a"
FENO = "#8f7a2e"
NOME_APP = "Datalac"
ICONE_APP = "📊"

CSS = f"""
<style>
.block-container {{ max-width: 1040px; padding-top: 2.2rem; }}
.el-topo {{
    border-left: 6px solid {VERDE};
    padding: .2rem 0 .2rem 1rem;
    margin-bottom: 1.2rem;
}}
.el-titulo {{ font-size: 2rem; font-weight: 700; line-height: 1.15; }}
.el-sub {{ opacity: .75; margin-top: .25rem; max-width: 62ch; }}
.el-etapas {{ display: flex; flex-wrap: wrap; gap: .4rem; margin: .4rem 0 1rem; }}
.el-etapa {{
    padding: .28rem .8rem; border-radius: 999px; font-size: .82rem;
    border: 1px solid rgba(128,128,128,.35); opacity: .7;
}}
.el-etapa.atual {{
    background: {VERDE}; border-color: {VERDE}; color: #fff;
    font-weight: 600; opacity: 1;
}}
.el-etapa.ok {{ border-color: {VERDE}; color: {VERDE}; opacity: 1; }}
.el-etapa.alerta {{ border-color: {FENO}; color: {FENO}; opacity: 1; }}
.el-mock {{
    display: inline-block; background: #f3e7b0; color: #5c4a00;
    border: 1px solid {FENO};
    padding: .15rem .65rem; border-radius: 6px;
    font-weight: 700; font-size: .78rem;
}}
.el-situacao {{ font-size: 2.2rem; font-weight: 700; margin: .3rem 0; }}
[data-testid="stPills"] button[aria-label^="! "] {{
    border-color: {FENO};
    color: {FENO};
}}
</style>
"""


def aplicar_estilo() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def cabecalho() -> None:
    st.markdown(
        '<div class="el-topo">'
        f'<div class="el-titulo">{ICONE_APP} {NOME_APP}</div>'
        '<div class="el-sub">Descubra se a sua atividade leiteira está pagando '
        "os custos. Informe os dados de um mês e receba um parecer explicado."
        "</div></div>",
        unsafe_allow_html=True,
    )


def etapas(titulos: list[str], atual: int, estados: list[str]) -> int | None:
    """Trilha clicável. Devolve o índice escolhido (ou None se desmarcou)."""

    def rotulo(i: int) -> str:
        marca = {"ok": "✓ ", "alerta": "! "}.get(estados[i], "")
        return f"{marca}{titulos[i]}"

    opcoes: dict[str, object] = {
        "format_func": rotulo,
        "selection_mode": "single",
        "key": "navegacao_etapas",
        "label_visibility": "collapsed",
    }
    if "navegacao_etapas" not in st.session_state:
        opcoes["default"] = atual
    return st.pills("Etapas", list(range(len(titulos))), **opcoes)
