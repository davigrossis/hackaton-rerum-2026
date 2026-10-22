"""Estilo visual: CSS leve, só fontes do sistema (a demo roda sem internet)."""

from __future__ import annotations

import streamlit as st

VERDE = "#2e6b4a"
AZUL = "#2b5c8f"
FENO = "#8f7a2e"
VERMELHO = "#a63a2b"
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

/* Situação econômica e cards de destaque */
.el-situacao {{ font-size: 2.2rem; font-weight: 700; margin: .3rem 0; }}
.el-situacao-card {{
    padding: 1.2rem;
    border-radius: 8px;
    margin: .8rem 0 1.2rem;
    background: rgba(128, 128, 128, .06);
    border: 1px solid rgba(128, 128, 128, .2);
}}
.el-situacao-lucro {{ border-left: 8px solid {VERDE}; }}
.el-situacao-medio_prazo {{ border-left: 8px solid {AZUL}; }}
.el-situacao-curto_prazo {{ border-left: 8px solid {FENO}; }}
.el-situacao-prejuizo {{ border-left: 8px solid {VERMELHO}; }}

.el-badge {{
    display: inline-block;
    padding: 0.2rem 0.6rem;
    font-size: 0.8rem;
    font-weight: 600;
    border-radius: 4px;
    background: rgba(128, 128, 128, .15);
    margin-bottom: 0.4rem;
}}

.el-rodape {{
    border-top: 1px solid rgba(128, 128, 128, .2);
    padding-top: 1.5rem;
    margin-top: 2.5rem;
    margin-bottom: 1rem;
    text-align: center;
    font-size: 0.85rem;
    opacity: 0.75;
}}

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
