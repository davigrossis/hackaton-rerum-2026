"""Renderização da base de conhecimento para consulta na interface."""

from __future__ import annotations

from typing import Any

import streamlit as st

from motor.regras import Base, Premissa, Regra


def _valor(valor: Any) -> str:
    if isinstance(valor, str):
        return valor.replace("_", " ")
    if isinstance(valor, list | tuple):
        return "[" + ", ".join(_valor(item) for item in valor) + "]"
    return str(valor)


def _premissa(premissa: Premissa) -> str:
    alvo = (
        f"${premissa.alvo[1:].replace('_', ' ')}"
        if isinstance(premissa.alvo, str) and premissa.alvo.startswith("$")
        else _valor(premissa.alvo)
    )
    return f"{premissa.fato.replace('_', ' ')} {premissa.operador} {alvo}"


def _regra_em_texto(regra: Regra) -> str:
    condicoes = " E ".join(_premissa(premissa) for premissa in regra.se)
    conclusao = f"{regra.fato.replace('_', ' ')} = {_valor(regra.valor)}"
    return f"SE {condicoes} ENTÃO {conclusao}"


def renderizar_base(base: Base) -> None:
    """Lista todas as regras da base carregada e a versão publicada."""
    st.subheader("Base de conhecimento")
    st.write(
        "Regras determinísticas usadas pelo motor de inferência. "
        "A base é carregada dos arquivos YAML versionados."
    )
    st.caption(f"Versão {base.versao} · {len(base.regras)} regras")

    for regra in base.regras:
        with st.container(border=True):
            st.markdown(f"**{regra.id} — {regra.descricao}**")
            st.write(f"**Camada:** {regra.camada}")
            st.write(f"**Regra:** {_regra_em_texto(regra)}")
            st.write(f"**Confiança da regra:** {regra.cf:.0%}")
            st.write(f"**Fonte:** {regra.fonte}")
