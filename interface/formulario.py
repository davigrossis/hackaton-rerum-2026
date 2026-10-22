"""Formulário em etapas: perguntas vêm da base, respostas ficam em um dict."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dominio.diagnostico import validar_respostas
from interface.exemplo import FAZENDA_EXEMPLO
from motor.regras import Base, Pergunta, Regra, Secao

CHAVE_DADOS = "dados"
CHAVE_ESTIMADOS = "estimados"
CHAVE_ETAPA = "etapa"
CHAVE_RESULTADO = "resultado"
PREFIXO_CAMPO = "resposta_"
PREFIXO_ESTIMADO = "estimado_"
CHAVE_ALCANCADA = "etapa_alcancada"
CHAVE_NAVEGACAO = "navegacao_etapas"

SecaoComPerguntas = tuple[Secao, list[Pergunta]]


def pode_estimar(pergunta: Pergunta) -> bool:
    """Apenas grandezas numéricas (numero/inteiro) podem ser marcadas como estimadas."""
    return pergunta.tipo in ("numero", "inteiro")


def regras_dependentes(base: Base, pergunta_id: str) -> list[Regra]:
    """Retorna regras que usam a pergunta diretamente ou via variáveis calculadas derivadas."""
    calculadas = [v for v in base.variaveis.values() if v.grupo == "calculadas"]
    vars_dependentes = {pergunta_id}
    mudou = True
    while mudou:
        mudou = False
        for c in calculadas:
            if c.nome not in vars_dependentes and any(
                dep in vars_dependentes for dep in c.entradas + c.opcionais
            ):
                vars_dependentes.add(c.nome)
                mudou = True

    regras_vistas: dict[str, Regra] = {}
    for var in vars_dependentes:
        for r in base.regras_que_usam(var):
            if r.id not in regras_vistas:
                regras_vistas[r.id] = r
    return sorted(regras_vistas.values(), key=lambda r: (r.camada, r.id))


def iniciar_estado() -> None:
    st.session_state.setdefault(CHAVE_DADOS, {})
    st.session_state.setdefault(CHAVE_ESTIMADOS, set())
    st.session_state.setdefault(CHAVE_ETAPA, 0)
    st.session_state.setdefault(CHAVE_ALCANCADA, 0)
    st.session_state.setdefault(CHAVE_NAVEGACAO, 0)
    st.session_state.setdefault(CHAVE_RESULTADO, None)


def _chave(pergunta: Pergunta) -> str:
    return f"{PREFIXO_CAMPO}{pergunta.id}"


def _chave_estimado(pergunta: Pergunta) -> str:
    return f"{PREFIXO_ESTIMADO}{pergunta.id}"


def _limpar_widgets() -> None:
    for chave in [
        k for k in st.session_state if k.startswith((PREFIXO_CAMPO, PREFIXO_ESTIMADO))
    ]:
        del st.session_state[chave]


def carregar_exemplo(ids_validos: set[str]) -> None:
    """Preenche só campos que existem na base e volta à primeira etapa."""
    _limpar_widgets()
    st.session_state[CHAVE_DADOS] = {
        k: v for k, v in FAZENDA_EXEMPLO.items() if k in ids_validos
    }
    st.session_state[CHAVE_ESTIMADOS] = set()
    st.session_state[CHAVE_ETAPA] = 0
    st.session_state[CHAVE_ALCANCADA] = 0
    st.session_state[CHAVE_NAVEGACAO] = 0
    st.session_state[CHAVE_RESULTADO] = None


def limpar_respostas() -> None:
    _limpar_widgets()
    st.session_state[CHAVE_DADOS] = {}
    st.session_state[CHAVE_ESTIMADOS] = set()
    st.session_state[CHAVE_ETAPA] = 0
    st.session_state[CHAVE_ALCANCADA] = 0
    st.session_state[CHAVE_NAVEGACAO] = 0
    st.session_state[CHAVE_RESULTADO] = None


def _semear(pergunta: Pergunta, dados: dict[str, Any]) -> None:
    """Devolve ao widget o valor guardado (widgets fora da tela são descartados)."""
    chave = _chave(pergunta)
    if chave not in st.session_state and pergunta.id in dados:
        valor = dados[pergunta.id]
        if pergunta.tipo == "inteiro":
            valor = int(valor)
        elif pergunta.tipo == "numero":
            valor = float(valor)
        if pergunta.tipo != "escolha" or valor in (pergunta.opcoes or ()):
            st.session_state[chave] = valor

    if pode_estimar(pergunta):
        chave_est = _chave_estimado(pergunta)
        if chave_est not in st.session_state:
            estimados = st.session_state.get(CHAVE_ESTIMADOS, set())
            st.session_state[chave_est] = (
                pergunta.id in estimados and pergunta.id in dados
            )


def _renderizar_pergunta(
    pergunta: Pergunta, dados: dict[str, Any], base: Base | None = None
) -> None:
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

    if pode_estimar(pergunta):
        estimado = st.checkbox(
            "Valor estimado",
            key=_chave_estimado(pergunta),
            help="Marque se este número for uma estimativa aproximada (entra com confiança de 70%).",
        )
        estimados = st.session_state.get(CHAVE_ESTIMADOS, set())
        if estimado and pergunta.id in dados:
            estimados.add(pergunta.id)
        else:
            estimados.discard(pergunta.id)
        st.session_state[CHAVE_ESTIMADOS] = estimados

    if base is not None:
        regras = regras_dependentes(base, pergunta.id)
        if regras:
            with st.expander("Por que pergunto?"):
                for r in regras:
                    st.markdown(f"• **{r.id}** ({r.camada}): {r.descricao}")


def renderizar_etapa(
    secao: Secao, perguntas: list[Pergunta], base: Base | None = None
) -> None:
    dados = st.session_state[CHAVE_DADOS]
    with st.container(border=True):
        st.subheader(secao.titulo)
        colunas = st.columns(2, gap="large")
        for i, pergunta in enumerate(perguntas):
            with colunas[i % 2]:
                _renderizar_pergunta(pergunta, dados, base)


def coletar_respostas() -> dict[str, Any]:
    """Cópia das respostas; campos vazios nunca entram (nada vira zero)."""
    return dict(st.session_state[CHAVE_DADOS])


def coletar_estimados() -> frozenset[str]:
    """Retorna o conjunto imutável de IDs de perguntas preenchidas e marcadas como estimadas."""
    dados = st.session_state.get(CHAVE_DADOS, {})
    estimados = st.session_state.get(CHAVE_ESTIMADOS, set())
    return frozenset(cid for cid in estimados if cid in dados)


def problemas(
    secoes: list[SecaoComPerguntas], respostas: dict[str, Any]
) -> list[tuple[int, str]]:
    """Lista (índice da etapa, mensagem) usando a validação do diagnóstico."""
    return [
        (indice, mensagem)
        for indice, (_, perguntas) in enumerate(secoes)
        for mensagem in validar_respostas(respostas, perguntas).values()
    ]


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
    erros = validar_respostas(respostas, obrigatorias)
    feitas = sum(1 for p in obrigatorias if p.id not in erros)
    return feitas, len(obrigatorias)


def sincronizar_respostas(perguntas: list[Pergunta]) -> None:
    """Copia para o dict os valores dos widgets ainda presentes no estado.

    Roda no início de cada execução, antes de trocar de etapa, para que o
    que foi digitado em uma seção não se perca ao navegar.
    """
    dados = st.session_state[CHAVE_DADOS]
    estimados = st.session_state.setdefault(CHAVE_ESTIMADOS, set())
    for pergunta in perguntas:
        chave = _chave(pergunta)
        if chave in st.session_state:
            valor = st.session_state[chave]
            if isinstance(valor, str):
                valor = valor.strip()
            if valor is None or valor == "":
                dados.pop(pergunta.id, None)
            else:
                dados[pergunta.id] = valor

        if pode_estimar(pergunta):
            chave_est = _chave_estimado(pergunta)
            if chave_est in st.session_state:
                if bool(st.session_state[chave_est]) and pergunta.id in dados:
                    estimados.add(pergunta.id)
                else:
                    estimados.discard(pergunta.id)
