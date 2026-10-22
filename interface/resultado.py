"""Revisão antes do envio e parecer completo do diagnóstico com simulação."""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st

from interface.estilo import VERDE
from interface.formulario import SecaoComPerguntas
from interface.simulacao import renderizar_simulacao
from motor.explicacao import NoComo, como, por_que
from motor.inferencia import Resultado
from motor.regras import Base

ROTULOS_VALORES: dict[str, str] = {
    # Situação econômica
    "lucro": "Lucro econômico",
    "medio_prazo": "Equilíbrio apenas no médio prazo",
    "curto_prazo": "Sobrevivência apenas no curto prazo",
    "prejuizo": "Prejuízo operacional (não cobre o COE)",
    # Níveis de indicadores
    "abaixo_mercado": "Abaixo da média estadual",
    "no_mercado": "Em linha com a média estadual",
    "acima_mercado": "Acima da média estadual",
    "abaixo_media": "Abaixo da média estadual",
    "alto": "Alto",
    "adequado": "Adequado",
    "adequada": "Adequada",
    "baixa": "Baixa",
    "alta": "Alta",
    "favoravel": "Favorável",
    "desfavoravel": "Desfavorável",
    "dentro_in76": "Em conformidade legal (IN 76/2018)",
    "fora_in76": "Fora dos limites legais (IN 76/2018)",
    # Causas
    "preco_recebido_baixo": "Preço do leite recebido abaixo do mercado",
    "custo_alimentar_alto": "Custo alimentar elevado em relação ao desembolso",
    "rebanho_reproducao": "Baixa eficiência reprodutiva (% lactação baixa)",
    "qualidade_leite": "Problemas de qualidade do leite (CCS/CPP elevados)",
    "escala_baixa": "Baixa escala de produção",
    # Recomendações
    "negociar_com_laticinio": "Negociar bonificações ou buscar novos compradores",
    "revisar_dieta_com_nutricionista": "Revisar formulação da dieta e custos com nutricionista",
    "manejo_reprodutivo": "Intensificar manejo reprodutivo e IATF",
    "melhorar_higiene_ordenha": "Melhorar protocolos de higiene de ordenha e refrigeração",
    "avaliar_escala": "Avaliar alternativas para aumento de volume/escala",
    "manter_controle_e_avaliar_expansao": "Manter controle gerencial e avaliar expansão planejada",
}

ITENS_COE: list[tuple[str, str]] = [
    ("custo_concentrado", "Concentrado"),
    ("custo_volumoso", "Volumoso"),
    ("custo_mineral", "Sal mineral"),
    ("custo_mao_obra_contratada", "Mão de obra contratada"),
    ("custo_sanidade_reproducao", "Sanidade e reprodução"),
    ("custo_energia_combustivel", "Energia e combustível"),
    ("custo_outros", "Outros desembolsos"),
]


def rotulo_amigavel(valor: Any) -> str:
    """Retorna um texto legível para valores categóricos ou termos técnicos."""
    if isinstance(valor, str) and valor in ROTULOS_VALORES:
        return ROTULOS_VALORES[valor]
    return str(valor).replace("_", " ").capitalize()


def formatar(valor: Any, unidade: str | None = None) -> str:
    """Formata no padrão brasileiro (1.234,56) sem alterar o dado original."""
    if valor is None:
        return "—"
    if isinstance(valor, float):
        texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    elif isinstance(valor, int):
        texto = f"{valor:,}".replace(",", ".")
    else:
        texto = str(valor)
    return f"{texto} {unidade}" if unidade else texto


def _percentual(valor: float) -> str:
    """Percentual com uma casa e vírgula decimal: 35.04 → '35,0%'."""
    return f"{valor:.1f}%".replace(".", ",")


def renderizar_revisao(
    secoes: list[SecaoComPerguntas],
    respostas: dict[str, Any],
    achados: list[tuple[int, str]],
    ir_para: Callable[[int], None],
    estimados: frozenset[str] = frozenset(),
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
                "Corrigir",
                key=f"corrigir_{indice}_{mensagem}",
                use_container_width=True,
                on_click=ir_para,
                args=(indice,),
            )  # fmt: skip
    else:
        st.success("Tudo certo. Confira os valores e gere o diagnóstico.")

    for indice, (secao, perguntas) in enumerate(secoes):
        with st.expander(secao.titulo, expanded=False):
            linhas = {}
            for p in perguntas:
                if p.id in respostas:
                    valor_str = formatar(respostas[p.id], p.unidade)
                    if p.id in estimados:
                        valor_str = f"{valor_str} (estimado · CF 70%)"
                else:
                    valor_str = "— não informado"
                linhas[p.texto] = valor_str
            st.table(linhas)
            st.button(
                "Editar esta seção",
                key=f"editar_{indice}",
                use_container_width=True,
                on_click=ir_para,
                args=(indice,),
            )  # fmt: skip


def renderizar_parecer(resultado: Resultado, base: Base) -> None:
    """Parecer executivo explicável completo (#13) e simulação (#15)."""
    _situacao(resultado, base)
    st.divider()
    _cards_mercado(resultado, base)
    st.divider()
    _grafico_coe(resultado, base)
    st.divider()
    _causas_e_recomendacoes(resultado, base)
    st.divider()
    _diagnostico_indicadores(resultado, base)
    st.divider()
    _dados_opcionais_pendentes(resultado, base)
    st.divider()
    _indicadores(resultado, base)
    _memoria_trabalho(resultado, base)
    st.divider()
    renderizar_simulacao(resultado, base)
    _rodape(base)


def _situacao(resultado: Resultado, base: Base) -> None:
    fato = resultado.memoria.valor("situacao_economica")
    st.subheader("Diagnóstico Econômico")

    if fato is None:
        st.warning(
            "Com os dados informados, o motor não pôde determinar a situação econômica."
        )
        receita = resultado.memoria.valor("receita_total")
        cot = resultado.memoria.valor("cot")
        capital = resultado.memoria.valor("capital_investido")
        if (
            receita
            and cot
            and receita.valor >= cot.valor
            and (capital is None or capital.valor is None)
        ):
            st.info(
                "A receita cobre o COT, mas o capital investido não foi informado. "
                "Sem o capital, não é possível calcular a remuneração do capital e o Custo Total (CT) "
                "para distinguir entre Lucro e Médio Prazo."
            )
        return

    regra = next(
        (r for r in base.regras if r.id == fato.origens[-1].detalhe),
        None,
    )
    descricao_regra = (
        f"{regra.id}: {regra.descricao}" if regra else str(fato.origens[-1].detalhe)
    )

    card_html = f"""
    <div class="el-situacao-card el-situacao-{fato.valor}">
        <span class="el-badge">Confiança {fato.cf:.0%} · {regra.id if regra else ""}</span>
        <div class="el-situacao">{fato.valor}</div>
        <div style="font-size: 1.25rem; font-weight: 600; margin-bottom: 0.3rem;">{rotulo_amigavel(fato.valor)}</div>
        <div style="opacity: 0.9;"><b>{descricao_regra}</b></div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
    st.write(f"Confiança {fato.cf:.0%} · {descricao_regra}")

    # Métricas financeiras e margens
    col1, col2, col3, col4 = st.columns(4)
    rec = resultado.memoria.valor("receita_total")
    coe = resultado.memoria.valor("coe")
    cot = resultado.memoria.valor("cot")
    ct = resultado.memoria.valor("ct")
    mb = resultado.memoria.valor("margem_bruta")
    ml = resultado.memoria.valor("margem_liquida")
    luc = resultado.memoria.valor("lucro")

    col1.metric("Receita Total", formatar(rec.valor, "R$") if rec else "—")
    col2.metric(
        "COE (Desembolso)",
        formatar(coe.valor, "R$") if coe else "—",
        help=f"Margem Bruta: {formatar(mb.valor, 'R$') if mb else '—'}",
    )
    col3.metric(
        "COT (Operacional)",
        formatar(cot.valor, "R$") if cot else "—",
        help=f"Margem Líquida: {formatar(ml.valor, 'R$') if ml else '—'}",
    )
    col4.metric(
        "CT (Custo Total)",
        formatar(ct.valor, "R$") if ct else "— (sem capital)",
        help=f"Lucro Econômico: {formatar(luc.valor, 'R$') if luc else '—'}",
    )

    _renderizar_como(resultado, base, "situacao_economica", fato.valor)


def _cards_mercado(resultado: Resultado, base: Base) -> None:
    externos = [
        f
        for f in resultado.memoria.fatos()
        if any(o.tipo == "externo" for o in f.origens)
        and f.nome != "produtividade_regional_ibge"
    ]
    if not externos:
        st.info("Informe UF e mês de referência para comparar com a CONAB.")
        return

    st.subheader("Fazenda × Mercado da UF (CONAB)")
    c1, c2, c3 = st.columns(3)

    preco_fazenda = resultado.memoria.valor("preco_leite_fazenda")
    preco_uf = resultado.memoria.valor("preco_leite_uf")
    preco_12m = resultado.memoria.valor("preco_leite_uf_media_12m")

    if preco_fazenda and preco_uf:
        delta_pct = ((preco_fazenda.valor - preco_uf.valor) / preco_uf.valor) * 100
        preco_fmt = (
            f"R$ {preco_fazenda.valor:,.2f}".replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )
        c1.metric(
            "Preço do Leite (R$/L)",
            preco_fmt,
            delta=f"{delta_pct:+.1f}% vs UF ({formatar(preco_uf.valor, 'R$/L')})",
        )
        if preco_12m:
            c1.caption(f"Média 12m UF: {formatar(preco_12m.valor, 'R$/L')}")

    troca_uf = resultado.memoria.valor("troca_leite_milho_uf")
    troca_12m = resultado.memoria.valor("troca_leite_milho_uf_media_12m")
    if troca_uf:
        delta_troca = (troca_uf.valor - troca_12m.valor) if troca_12m else None
        delta_str = (
            f"{delta_troca:+.2f} vs 12m ({troca_12m.valor:,.2f})".replace(".", ",")
            if delta_troca is not None
            else None
        )
        c2.metric(
            "Troca Leite:Milho na UF",
            f"{troca_uf.valor:,.2f} kg/L".replace(".", ","),
            delta=delta_str,
        )
        if troca_12m:
            c2.caption(
                f"Poder de compra: 1 L de leite compra {troca_uf.valor:,.2f} kg de milho."
            )

    milho = resultado.memoria.valor("preco_milho_uf")
    diesel = resultado.memoria.valor("preco_diesel_uf")
    if milho or diesel:
        c3.metric(
            "Milho Grão na UF",
            formatar(milho.valor, "R$/kg") if milho else "—",
        )
        if diesel:
            c3.caption(f"Diesel na UF: {formatar(diesel.valor, 'R$/L')}")


def _grafico_coe(resultado: Resultado, base: Base) -> None:
    coe_fato = resultado.memoria.valor("coe")
    if not coe_fato or coe_fato.valor <= 0:
        return

    st.subheader("Composição do Custo Operacional Efetivo (COE)")
    dados = []
    for chave, rotulo in ITENS_COE:
        f = resultado.memoria.valor(chave)
        if f is not None and f.valor > 0:
            pct = (f.valor / coe_fato.valor) * 100
            dados.append(
                {
                    "Componente": rotulo,
                    "Valor (R$)": f.valor,
                    "Participação (%)": pct,
                }
            )

    if not dados:
        return

    df = pd.DataFrame(dados).sort_values("Participação (%)", ascending=False)
    col1, col2 = st.columns([5, 4])

    with col1:
        st.altair_chart(_colunas_coe(df), width="stretch")

    with col2:
        df_tabela = df.copy()
        df_tabela["Valor (R$)"] = df_tabela["Valor (R$)"].apply(
            lambda v: formatar(v, "R$")
        )
        df_tabela["Participação (%)"] = df_tabela["Participação (%)"].apply(_percentual)
        st.dataframe(
            df_tabela.rename(columns={"Participação (%)": "%"}),
            hide_index=True,
            column_config={
                "Componente": st.column_config.TextColumn(width=150),
                "Valor (R$)": st.column_config.TextColumn(width=100),
                "%": st.column_config.TextColumn(width=60),
            },
        )


def _colunas_coe(df: pd.DataFrame) -> alt.LayerChart:
    """Colunas verticais da participação no COE, na ordem em que o df chega."""
    # Vega formata com ponto decimal; o texto já sai formatado em pt-BR.
    df = df.assign(
        rotulo=df["Participação (%)"].map(_percentual),
        valor_fmt=df["Valor (R$)"].map(lambda v: formatar(v, "R$")),
    )
    # Folga no topo para o rótulo da coluna mais alta não ser cortado.
    topo = df["Participação (%)"].max() * 1.15
    base = alt.Chart(df).encode(
        x=alt.X(
            "Componente:N",
            sort=None,
            title=None,
            axis=alt.Axis(labelAngle=-40, labelLimit=160, labelOverlap=False),
        ),
        y=alt.Y(
            "Participação (%):Q",
            title="Participação no COE (%)",
            scale=alt.Scale(domain=[0, topo]),
        ),
        tooltip=[
            alt.Tooltip("Componente:N"),
            alt.Tooltip("valor_fmt:N", title="Valor"),
            alt.Tooltip("rotulo:N", title="Participação"),
        ],
    )
    colunas = base.mark_bar(color=VERDE, cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    # O Vega não herda a cor de texto do tema; cinza médio lê bem no claro e no escuro.
    rotulos = base.mark_text(dy=-8, fontWeight="bold", color="#808495").encode(
        text="rotulo:N"
    )
    return (colunas + rotulos).properties(height=320)


def _causas_e_recomendacoes(resultado: Resultado, base: Base) -> None:
    st.subheader("Causas Prováveis e Recomendações")
    c_esq, c_dir = st.columns(2)

    causas = sorted(
        resultado.memoria.valores("causa"), key=lambda f: f.cf, reverse=True
    )
    with c_esq:
        st.markdown("#### Causas Prováveis")
        if not causas:
            st.caption("Nenhuma causa crítica identificada pelo motor.")
        for f in causas:
            st.markdown(f"• **{rotulo_amigavel(f.valor)}** — Confiança {f.cf:.0%}")
            st.progress(f.cf)
            _renderizar_como(resultado, base, "causa", f.valor)

    recs = sorted(
        resultado.memoria.valores("recomendacao"),
        key=lambda f: f.cf,
        reverse=True,
    )
    with c_dir:
        st.markdown("#### Recomendações Técnicas")
        if not recs:
            st.caption("Nenhuma recomendação gerada com os dados atuais.")
        for f in recs:
            st.markdown(f"• **{rotulo_amigavel(f.valor)}** — Confiança {f.cf:.0%}")
            st.progress(f.cf)
            _renderizar_como(resultado, base, "recomendacao", f.valor)


def _diagnostico_indicadores(resultado: Resultado, base: Base) -> None:
    st.subheader("Avaliação dos Indicadores")
    indicadores_avaliados = [
        f
        for var in base.variaveis.values()
        if var.grupo == "conclusoes" and var.camada == "indicador"
        for f in resultado.memoria.valores(var.nome)
    ]
    indicadores_avaliados.sort(key=lambda f: f.cf, reverse=True)

    if not indicadores_avaliados:
        st.caption("Nenhuma avaliação de indicador disparada.")
        return

    for f in indicadores_avaliados:
        desc = base.variaveis[f.nome].descricao if f.nome in base.variaveis else f.nome
        st.markdown(f"**{desc}**: {rotulo_amigavel(f.valor)} · Confiança {f.cf:.0%}")
        _renderizar_como(resultado, base, f.nome, f.valor)


def _dados_opcionais_pendentes(resultado: Resultado, base: Base) -> None:
    """Explica 'Por que a pergunta?' para perguntas opcionais não informadas que travam regras."""
    opcionais = [p for p in base.perguntas if not p.obrigatoria]
    faltando = [p for p in opcionais if not resultado.memoria.tem(p.id)]
    motivos_relevantes: list[tuple[str, str, list[str]]] = []

    for p in faltando:
        # Verifica se há regras que esperam esta variável ou variáveis calculadas dela
        calculadas = [v for v in base.variaveis.values() if v.grupo == "calculadas"]
        deps = {p.id}
        for c in calculadas:
            if any(d in deps for d in c.entradas + c.opcionais):
                deps.add(c.nome)

        regras_esperando: list[str] = []
        for var in deps:
            for m in por_que(base, var, resultado):
                regras_esperando.append(
                    f"**{m.regra.id}** ({m.regra.camada}): {m.regra.descricao}"
                )

        if regras_esperando:
            motivos_relevantes.append(
                (
                    p.texto,
                    p.id,
                    list(dict.fromkeys(regras_esperando)),
                )
            )

    if motivos_relevantes:
        with st.expander("Por que pergunto sobre dados opcionais não informados?"):
            st.write(
                "O preenchimento dos campos opcionais abaixo permitiria ao sistema especialista "
                "avaliar regras e recomendações adicionais:"
            )
            for texto_pergunta, _, regras in motivos_relevantes:
                st.markdown(f"• **{texto_pergunta}**")
                for r in regras:
                    st.markdown(f"  - Destrava a regra {r}")


def _renderizar_como(resultado: Resultado, base: Base, fato: str, valor: Any) -> None:
    with st.expander("Como cheguei aqui?"):
        nos = como(resultado, fato, valor)
        if not nos:
            st.caption("Fato informado ou sem regra disparada.")
            return
        for no in nos:
            _renderizar_no_como(no, base)


def _renderizar_no_como(no: NoComo, base: Base, nivel: int = 0) -> None:
    indent = "    " * nivel
    if no.regra:
        st.markdown(
            f"{indent}• Concluído pela regra **{no.regra.id}** (*{no.regra.descricao}*):"
        )
        st.markdown(
            f"{indent}  - **Fonte**: {no.regra.fonte}\n"
            f"{indent}  - **Confiança**: {no.cf:.0%} (regra: {no.regra.cf:.0%})"
        )
        if no.premissas:
            st.markdown(f"{indent}  - **Premissas avaliadas**:")
            for p in no.premissas:
                val_f = formatar(p.valor_fato)
                val_a = formatar(p.valor_alvo)
                st.markdown(
                    f"{indent}    · `{p.premissa.fato}` ({val_f}) {p.premissa.operador} `{p.premissa.alvo}` ({val_a}) "
                    f"→ **{'verdadeira' if p.verdadeira else 'falsa'}** (CF {p.cf:.0%})"
                )
        if no.conflitos:
            st.markdown(
                f"{indent}  - **Conflito resolvido contra**: {', '.join(no.conflitos)}"
            )
        if no.bloqueios:
            bloq_str = ", ".join(
                f"{b.regra} ({b.valor_pretendido})" for b in no.bloqueios
            )
            st.markdown(f"{indent}  - **Regras gerais bloqueadas**: {bloq_str}")
    else:
        orig = no.origem
        desc = (
            base.variaveis[no.fato].descricao if no.fato in base.variaveis else no.fato
        )
        detalhe_str = f" — *{orig.detalhe}*" if orig.detalhe else ""
        st.markdown(
            f"{indent}• **{desc}** (`{no.fato}`): {formatar(no.valor)} "
            f"(origem: {orig.tipo}, CF {no.cf:.0%}){detalhe_str}"
        )

    for filho in no.filhos:
        _renderizar_no_como(filho, base, nivel + 1)


def _indicadores(resultado: Resultado, base: Base) -> None:
    st.subheader("Indicadores calculados")
    calculados = [
        f for f in resultado.memoria.fatos() if f.origens[-1].tipo == "calculado"
    ]
    linhas = {}
    for f in calculados:
        desc = base.variaveis[f.nome].descricao
        valor_fmt = formatar(f.valor, base.variaveis[f.nome].unidade)
        if f.cf < 1.0:
            valor_fmt = f"{valor_fmt} (CF {f.cf:.0%})"
        linhas[desc] = valor_fmt
    st.table(linhas)


def _memoria_trabalho(resultado: Resultado, base: Base) -> None:
    with st.expander("Memória de trabalho (todos os fatos)"):
        fatos = resultado.memoria.fatos()
        linhas = []
        for f in fatos:
            desc = (
                base.variaveis[f.nome].descricao
                if f.nome in base.variaveis
                else (
                    next(
                        (p.texto for p in base.perguntas if p.id == f.nome),
                        f.nome,
                    )
                )
            )
            unidade = (
                base.variaveis[f.nome].unidade if f.nome in base.variaveis else None
            )
            linhas.append(
                {
                    "Variável": f.nome,
                    "Descrição": desc,
                    "Valor": formatar(f.valor, unidade),
                    "CF": f"{f.cf:.0%}",
                    "Origem": ", ".join(o.tipo for o in f.origens),
                    "Detalhe": "; ".join(o.detalhe for o in f.origens if o.detalhe),
                }
            )
        st.dataframe(pd.DataFrame(linhas), hide_index=True)


def _data_snapshot_conab() -> str:
    fontes_path = Path(__file__).resolve().parent.parent / "dados" / "raw" / "FONTES.md"
    if fontes_path.exists():
        texto = fontes_path.read_text(encoding="utf-8")
        match = re.search(r"Data do download:\*\*\s*(\d{2}/\d{2}/\d{4})", texto)
        if match:
            return match.group(1)
    return "20/10/2026"


def _rodape(base: Base) -> None:
    st.markdown(
        f'<div class="el-rodape">'
        f"Base de conhecimento v{base.versao} · Snapshot CONAB de {_data_snapshot_conab()} · "
        f"Sistema especialista 100% determinístico e auditável"
        f"</div>",
        unsafe_allow_html=True,
    )
