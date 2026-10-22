"""Formulário em etapas: perguntas vêm da base, respostas ficam em um dict."""

from __future__ import annotations

import re
from typing import Any

import streamlit as st

from interface.exemplo import FAZENDA_EXEMPLO
from motor.regras import Pergunta, Secao

CHAVE_DADOS = "dados"
CHAVE_ETAPA = "etapa"
CHAVE_RESULTADO = "resultado"
PREFIXO_CAMPO = "resposta_"
CHAVE_ALCANCADA = "etapa_alcancada"
CHAVE_NAVEGACAO = "navegacao_etapas"
PADRAO_MES = re.compile(r"^(0[1-9]|1[0-2])/\d{4}$")

SecaoComPerguntas = tuple[Secao, list[Pergunta]]


def iniciar_estado() -> None:
    st.session_state.setdefault(CHAVE_DADOS, {})
    st.session_state.setdefault(CHAVE_ETAPA, 0)
    st.session_state.setdefault(CHAVE_ALCANCADA, 0)
    st.session_state.setdefault(CHAVE_NAVEGACAO, 0)
    st.session_state.setdefault(CHAVE_RESULTADO, None)


def _chave(pergunta: Pergunta) -> str:
    return f"{PREFIXO_CAMPO}{pergunta.id}"


def _limpar_widgets() -> None:
    for chave in [k for k in st.session_state if k.startswith(PREFIXO_CAMPO)]:
        del st.session_state[chave]


def carregar_exemplo(ids_validos: set[str]) -> None:
    """Preenche só campos que existem na base e volta à primeira etapa."""
    _limpar_widgets()
    st.session_state[CHAVE_DADOS] = {
        k: v for k, v in FAZENDA_EXEMPLO.items() if k in ids_validos
    }
    st.session_state[CHAVE_ETAPA] = 0
    st.session_state[CHAVE_ALCANCADA] = 0
    st.session_state[CHAVE_NAVEGACAO] = 0
    st.session_state[CHAVE_RESULTADO] = None


def limpar_respostas() -> None:
    _limpar_widgets()
    st.session_state[CHAVE_DADOS] = {}
    st.session_state[CHAVE_ETAPA] = 0
    st.session_state[CHAVE_ALCANCADA] = 0
    st.session_state[CHAVE_NAVEGACAO] = 0
    st.session_state[CHAVE_RESULTADO] = None


def _semear(pergunta: Pergunta, dados: dict[str, Any]) -> None:
    """Devolve ao widget o valor guardado (widgets fora da tela são descartados)."""
    chave = _chave(pergunta)
    if chave in st.session_state or pergunta.id not in dados:
        return
    valor = dados[pergunta.id]
    if pergunta.tipo == "inteiro":
        valor = int(valor)
    elif pergunta.tipo == "numero":
        valor = float(valor)
    if pergunta.tipo == "escolha" and valor not in (pergunta.opcoes or ()):
        return
    st.session_state[chave] = valor


def _renderizar_pergunta(pergunta: Pergunta, dados: dict[str, Any]) -> None:
    _semear(pergunta, dados)
    chave = _chave(pergunta)
    rotulo = pergunta.texto + (" :red[\\*]" if pergunta.obrigatoria else "")
    comum: dict[str, Any] = {"help": pergunta.ajuda, "key": chave}

    if pergunta.tipo == "escolha":
        st.selectbox(
            rotulo, list(pergunta.opcoes or ()), index=None,
            placeholder="Selecione", **comum,
        )  # fmt: skip
    elif pergunta.tipo == "mes":
        st.text_input(rotulo, placeholder="MM/AAAA, ex.: 09/2026", **comum)
    elif pergunta.tipo == "inteiro":
        st.number_input(
            rotulo,
            min_value=int(pergunta.faixa[0]) if pergunta.faixa else None,
            max_value=int(pergunta.faixa[1]) if pergunta.faixa else None,
            step=1, format="%d", value=None, **comum,
        )  # fmt: skip
    else:
        st.number_input(
            rotulo,
            min_value=float(pergunta.faixa[0]) if pergunta.faixa else None,
            max_value=float(pergunta.faixa[1]) if pergunta.faixa else None,
            step=0.01, format="%.2f", value=None, **comum,
        )  # fmt: skip

    valor = st.session_state.get(chave)
    if isinstance(valor, str):
        valor = valor.strip()
    if valor is None or valor == "":
        dados.pop(pergunta.id, None)
    else:
        dados[pergunta.id] = valor

    situacao = "obrigatório" if pergunta.obrigatoria else "opcional"
    unidade = f"{pergunta.unidade} · " if pergunta.unidade else ""
    st.caption(f"{unidade}{situacao}")


def renderizar_etapa(secao: Secao, perguntas: list[Pergunta]) -> None:
    dados = st.session_state[CHAVE_DADOS]
    with st.container(border=True):
        st.subheader(secao.titulo)
        colunas = st.columns(2, gap="large")
        for i, pergunta in enumerate(perguntas):
            with colunas[i % 2]:
                _renderizar_pergunta(pergunta, dados)


def coletar_respostas() -> dict[str, Any]:
    """Cópia das respostas; campos vazios nunca entram (nada vira zero)."""
    return dict(st.session_state[CHAVE_DADOS])


def problemas(
    secoes: list[SecaoComPerguntas], respostas: dict[str, Any]
) -> list[tuple[int, str]]:
    """Lista (índice da etapa, mensagem) para obrigatórias ausentes e mês inválido."""
    achados: list[tuple[int, str]] = []
    for indice, (_, perguntas) in enumerate(secoes):
        for p in perguntas:
            if p.obrigatoria and p.id not in respostas:
                achados.append((indice, f"{p.texto}: falta preencher."))
            elif (
                p.tipo == "mes"
                and p.id in respostas
                and not PADRAO_MES.match(str(respostas[p.id]))
            ):
                achados.append((indice, f"{p.texto}: use o formato MM/AAAA."))
    return achados


def estados_das_etapas(
    secoes: list[SecaoComPerguntas], respostas: dict[str, Any], alcancada: int
) -> list[str]:
    """'' (ainda não visitada), 'ok' ou 'alerta' (visitada com pendência)."""
    ruins = {i for i, _ in problemas(secoes, respostas)}
    estados = []
    for i in range(len(secoes)):
        if i > alcancada:
            estados.append("")
        elif i in ruins:
            estados.append("alerta")
        else:
            estados.append("ok")
    return estados


def progresso_obrigatorias(
    secoes: list[SecaoComPerguntas], respostas: dict[str, Any]
) -> tuple[int, int]:
    obrigatorias = [p for _, ps in secoes for p in ps if p.obrigatoria]
    feitas = sum(1 for p in obrigatorias if p.id in respostas)
    return feitas, len(obrigatorias)


def sincronizar_respostas(perguntas: list[Pergunta]) -> None:
    """Copia para o dict os valores dos widgets ainda presentes no estado.

    Roda no início de cada execução, antes de trocar de etapa, para que o
    que foi digitado em uma seção não se perca ao navegar.
    """
    dados = st.session_state[CHAVE_DADOS]
    for pergunta in perguntas:
        chave = _chave(pergunta)
        if chave not in st.session_state:
            continue
        valor = st.session_state[chave]
        if isinstance(valor, str):
            valor = valor.strip()
        if valor is None or valor == "":
            dados.pop(pergunta.id, None)
        else:
            dados[pergunta.id] = valor
