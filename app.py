"""Entrada do Streamlit: assistente em etapas, parecer e simulação do Datalac."""

from __future__ import annotations

import streamlit as st

from dominio.diagnostico import diagnosticar, validar_respostas
from interface import formulario as fm
from interface.conhecimento import renderizar_base
from interface.estilo import (
    ICONE_APP,
    NOME_APP,
    aplicar_estilo,
    cabecalho,
    etapas,
)
from interface.resultado import renderizar_parecer, renderizar_revisao
from motor.explicacao import por_que
from motor.inferencia import Resultado, perguntas_pendentes
from motor.memoria import Memoria
from motor.regras import Base, carregar_base

CHAVE_ERRO = "erro_diagnostico"


@st.cache_resource
def obter_base() -> Base:
    """Carrega a base por meio do contrato do motor, uma vez por sessão."""
    return carregar_base()


def _ir_para(etapa: int) -> None:
    st.session_state[fm.CHAVE_ETAPA] = etapa
    st.session_state[fm.CHAVE_RESULTADO] = None
    st.session_state[CHAVE_ERRO] = None


def _ir_para_com_navegacao(etapa: int) -> None:
    st.session_state[fm.CHAVE_NAVEGACAO] = etapa
    _ir_para(etapa)


def _gerar(respostas: dict, estimados: frozenset[str] = frozenset()) -> None:
    """Revalida respostas e deixa erros explícitos na tela."""
    st.session_state[fm.CHAVE_RESULTADO] = None
    st.session_state[CHAVE_ERRO] = None
    base = obter_base()
    erros = validar_respostas(respostas, base.perguntas)
    if erros:
        st.session_state[CHAVE_ERRO] = " ".join(erros.values())
        return
    try:
        st.session_state[fm.CHAVE_RESULTADO] = diagnosticar(
            respostas, estimados=estimados, base=base
        )
    except (ValueError, KeyError, OSError) as erro:
        st.session_state[CHAVE_ERRO] = f"Não foi possível gerar o diagnóstico: {erro}"


def _barra_lateral(secoes: list[fm.SecaoComPerguntas], ids: set[str]) -> None:
    with st.sidebar:
        st.markdown("### Como funciona")
        st.write(
            "1. Preencha os dados do mês.\n"
            "2. Revise as respostas.\n"
            "3. Gere o diagnóstico."
        )
        respostas = fm.coletar_respostas()
        feitas, total = fm.progresso_obrigatorias(secoes, respostas)
        st.progress(feitas / total if total else 1.0)
        st.caption(f"{feitas} de {total} campos obrigatórios preenchidos")
        st.divider()
        st.button("Carregar fazenda-exemplo", on_click=fm.carregar_exemplo, args=(ids,))
        st.button("Limpar respostas", on_click=fm.limpar_respostas)


def _navegacao(atual: int, ultima: int) -> None:
    voltar, _, avancar = st.columns([1, 3, 1])
    if atual > 0:
        voltar.button("Voltar", on_click=_ir_para_com_navegacao, args=(atual - 1,))
    if atual < ultima:
        avancar.button(
            "Avançar",
            type="primary",
            on_click=_ir_para_com_navegacao,
            args=(atual + 1,),
        )


def _dialogo_pendencias(
    base: Base, resultado: Resultado, perguntas: list[fm.Pergunta]
) -> None:
    """Pergunta dados opcionais que destravam regras quase satisfeitas."""
    st.subheader("O motor precisa de mais um dado")
    st.write(
        "Essas informações são opcionais, mas podem completar uma regra que já "
        "está quase satisfeita."
    )
    for pergunta in perguntas:
        motivos = [
            motivo
            for motivo in por_que(base, pergunta.id, resultado)
            if motivo.esperando
        ]
        with st.container(border=True):
            st.markdown(f"**{pergunta.texto}**")
            for motivo in motivos:
                st.info(
                    f"Porque a regra **{motivo.regra.id}** pode concluir "
                    f"{motivo.regra.descricao.lower()}."
                )
            fm._renderizar_pergunta(pergunta, st.session_state[fm.CHAVE_DADOS])

    fm.sincronizar_respostas(perguntas)
    if st.button("Continuar diagnóstico", type="primary"):
        _gerar(fm.coletar_respostas(), fm.coletar_estimados())
        st.rerun()


def main() -> None:
    st.set_page_config(page_title=NOME_APP, page_icon=ICONE_APP, layout="wide")
    aplicar_estilo()
    fm.iniciar_estado()
    cabecalho()

    base = obter_base()
    pagina = st.sidebar.radio(
        "Página",
        ["Diagnóstico", "Base de conhecimento"],
        label_visibility="collapsed",
    )
    if pagina == "Base de conhecimento":
        renderizar_base(base)
        return

    perguntas = perguntas_pendentes(base, Memoria())
    secoes = [(s, [p for p in perguntas if p.secao == s.id]) for s in base.secoes]
    secoes = [(s, ps) for s, ps in secoes if ps]
    ids = {p.id for p in perguntas}
    fm.sincronizar_respostas(perguntas)
    _barra_lateral(secoes, ids)

    resultado = st.session_state[fm.CHAVE_RESULTADO]
    if resultado is not None:
        pendentes = perguntas_pendentes(base, resultado.memoria, resultado)
        if pendentes:
            _dialogo_pendencias(base, resultado, pendentes)
            return
        renderizar_parecer(resultado, base)
        st.button(
            "Editar respostas",
            on_click=_ir_para_com_navegacao,
            args=(len(secoes),),
        )
        return

    revisao = len(secoes)
    atual = min(st.session_state[fm.CHAVE_ETAPA], revisao)
    alcancada = max(st.session_state[fm.CHAVE_ALCANCADA], atual)
    st.session_state[fm.CHAVE_ALCANCADA] = alcancada

    respostas = fm.coletar_respostas()
    titulos = [s.titulo for s, _ in secoes] + ["Revisão"]
    estados = fm.estados_das_etapas(secoes, respostas, alcancada) + [""]

    escolhida = etapas(titulos, atual, estados)
    if escolhida is not None and escolhida != atual:
        _ir_para(escolhida)
        st.rerun()

    if atual < revisao:
        secao, perguntas_secao = secoes[atual]
        fm.renderizar_etapa(secao, perguntas_secao, base)
    else:
        achados = fm.problemas(secoes, respostas)
        estimados = fm.coletar_estimados()
        renderizar_revisao(secoes, respostas, achados, _ir_para, estimados)
        st.button(
            "Gerar diagnóstico",
            type="primary",
            disabled=bool(achados),
            on_click=_gerar,
            args=(respostas, estimados),
        )
        if st.session_state.get(CHAVE_ERRO):
            st.error(st.session_state[CHAVE_ERRO])

    _navegacao(atual, revisao)


if __name__ == "__main__":
    main()
