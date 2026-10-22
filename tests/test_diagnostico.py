"""Testes da ponta a ponta (#10, #13, #16): respostas -> mercado -> indicadores -> motor -> tela."""

from pathlib import Path

import pytest
import yaml
from streamlit.testing.v1 import AppTest

from dominio.diagnostico import diagnosticar
from interface.formulario import CHAVE_ESTIMADOS, CHAVE_RESULTADO
from motor.inferencia import Resultado
from motor.regras import carregar_base

RAIZ = Path(__file__).resolve().parent.parent
CASOS_ARQUIVOS = [
    "01_lucro.yaml",
    "02_medio_prazo.yaml",
    "03_curto_prazo_alimentacao.yaml",
    "04_prejuizo_preco_reproducao.yaml",
]
CASO_LUCRO = yaml.safe_load(
    (RAIZ / "dados" / "casos" / "01_lucro.yaml").read_text(encoding="utf-8")
)["entradas"]


def _sem(chave: str) -> dict:
    return {k: v for k, v in CASO_LUCRO.items() if k != chave}


def test_cada_fato_entra_com_a_sua_origem():
    memoria = diagnosticar(CASO_LUCRO).memoria

    def origem(nome):
        return memoria.valor(nome).origens[-1]

    assert (origem("producao_litros").tipo, origem("producao_litros").detalhe) == (
        "usuario",
        "",
    )
    assert origem("preco_leite_uf").tipo == "externo"
    assert origem("preco_leite_uf").detalhe.endswith("MG, 09/2026")
    assert origem("receita_total").tipo == "calculado"
    assert (
        origem("receita_total").detalhe == "R$ 93000.00 (leite) + R$ 2000.00 (outras)"
    )
    assert origem("situacao_economica").tipo == "regra"
    assert origem("situacao_economica").detalhe == "R-SIT-01"


def test_resposta_estimada_derruba_o_cf_da_cadeia():
    memoria = diagnosticar(
        CASO_LUCRO, estimados=frozenset({"preco_leite_fazenda"})
    ).memoria

    preco = memoria.valor("preco_leite_fazenda")
    assert (preco.cf, preco.origens[-1].detalhe) == (0.7, "estimado")
    assert memoria.valor("receita_total").cf == 0.7  # herda o menor CF (D7)
    assert memoria.valor("coe").cf == 1.0  # não depende do preço
    assert memoria.valor("situacao_economica").cf == 0.7


@pytest.mark.parametrize(
    "respostas",
    [_sem("capital_investido"), {**CASO_LUCRO, "capital_investido": None}],
    ids=["ausente", "none"],
)
def test_opcional_vazio_nao_vira_fato(respostas):
    memoria = diagnosticar(respostas).memoria

    assert not memoria.tem("capital_investido")
    assert not memoria.tem("ct")  # sem capital não há CT
    # A receita cobre o COT, mas sem CT nem lucro nem médio prazo disparam (#8).
    assert memoria.valor("situacao_economica") is None


def test_sem_mes_nao_ha_fatos_de_mercado():
    memoria = diagnosticar(_sem("mes_referencia")).memoria

    assert not any(f.origens[-1].tipo == "externo" for f in memoria.fatos())
    assert not memoria.tem("preco_leite_relativo_uf")
    assert memoria.valor("situacao_economica").valor == "lucro"


def test_resposta_sem_pergunta_na_base_da_erro():
    with pytest.raises(ValueError, match=r"sem pergunta na base: \['preco_leite'\]"):
        diagnosticar({**CASO_LUCRO, "preco_leite": 3.1})


def test_diagnosticar_rejeita_estimado_desconhecido():
    with pytest.raises(ValueError, match=r"sem pergunta na base: \['inexistente'\]"):
        diagnosticar(CASO_LUCRO, estimados=frozenset({"inexistente"}))


def _clicar(botoes, rotulo: str) -> None:
    next(b for b in botoes if b.label == rotulo).click().run()


def test_fazenda_exemplo_gera_parecer_real_na_tela():
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()
    _clicar(app.sidebar.button, "Carregar fazenda-exemplo")
    # Clicar em "Avançar": mudar só a etapa não basta, as pills voltam à etapa 0.
    for _ in carregar_base().secoes:
        _clicar(app.button, "Avançar")
    _clicar(app.button, "Gerar diagnóstico")

    assert not app.exception
    resultado = app.session_state[CHAVE_RESULTADO]
    assert isinstance(resultado, Resultado)
    assert resultado.memoria.valor("situacao_economica").valor == "lucro"
    tela = " ".join(m.value for m in app.markdown)
    assert '<div class="el-situacao">lucro</div>' in tela
    assert "Confiança 100% · R-SIT-01" in tela
    assert "MOCK" not in tela


def test_app_base_de_conhecimento_lista_todas_as_regras():
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()
    app.sidebar.radio[0].set_value("Base de conhecimento").run()

    assert not app.exception
    tela = " ".join(m.value for m in app.markdown)
    assert f"Versão {carregar_base().versao}" in " ".join(
        c.value for c in app.caption
    )
    assert all(regra.id in tela for regra in carregar_base().regras)
    assert all(regra.fonte in tela for regra in carregar_base().regras)


def test_app_entrada_estimada_reduz_confianca_ponta_a_ponta():
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()
    _clicar(app.sidebar.button, "Carregar fazenda-exemplo")

    # Navega até a seção 2 (Faturamento e Receitas), onde fica preco_leite_fazenda
    _clicar(app.button, "Avançar")  # etapa 1 (Rebanho)
    _clicar(app.button, "Avançar")  # etapa 2 (Receitas)

    # Marca o checkbox de preco_leite_fazenda como estimado
    cb = next(c for c in app.checkbox if c.key == "estimado_preco_leite_fazenda")
    cb.check().run()
    assert cb.value is True

    # Avança pelas 4 seções restantes até a Revisão (etapa 6)
    for _ in range(4):
        _clicar(app.button, "Avançar")

    # Na revisão, preco_leite_fazenda deve constar como estimado
    assert "preco_leite_fazenda" in app.session_state[CHAVE_ESTIMADOS]

    # Verifica se a tabela de revisão traz o sufixo de estimado
    tabelas_revisao = " ".join(str(t.value.to_dict()) for t in app.table)
    assert "(estimado · CF 70%)" in tabelas_revisao

    # Clica em Gerar diagnóstico
    _clicar(app.button, "Gerar diagnóstico")
    assert not app.exception

    resultado = app.session_state[CHAVE_RESULTADO]
    assert isinstance(resultado, Resultado)
    assert resultado.memoria.valor("preco_leite_fazenda").cf == pytest.approx(0.7)
    assert resultado.memoria.valor("situacao_economica").cf == pytest.approx(0.7)

    tela = " ".join(m.value for m in app.markdown)
    assert "Confiança 70% · R-SIT-01" in tela

    tabelas_parecer = " ".join(str(t.value.to_dict()) for t in app.table)
    assert "(CF 70%)" in tabelas_parecer


def test_app_limpar_respostas_zera_estimados():
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()
    _clicar(app.sidebar.button, "Carregar fazenda-exemplo")
    _clicar(app.button, "Avançar")  # etapa 1 (Rebanho)

    cb = next(c for c in app.checkbox if c.key == "estimado_vacas_lactacao")
    cb.check().run()
    assert "vacas_lactacao" in app.session_state[CHAVE_ESTIMADOS]

    _clicar(app.sidebar.button, "Limpar respostas")
    assert app.session_state[CHAVE_ESTIMADOS] == set()


def test_app_carregar_exemplo_zera_estimados():
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()
    _clicar(app.sidebar.button, "Carregar fazenda-exemplo")
    _clicar(app.button, "Avançar")  # etapa 1 (Rebanho)

    cb = next(c for c in app.checkbox if c.key == "estimado_vacas_lactacao")
    cb.check().run()
    assert "vacas_lactacao" in app.session_state[CHAVE_ESTIMADOS]

    _clicar(app.sidebar.button, "Carregar fazenda-exemplo")
    assert app.session_state[CHAVE_ESTIMADOS] == set()


@pytest.mark.parametrize("nome_arquivo", CASOS_ARQUIVOS)
def test_quatro_casos_renderizam_parecer_sem_erro(nome_arquivo):
    caso = yaml.safe_load(
        (RAIZ / "dados" / "casos" / nome_arquivo).read_text(encoding="utf-8")
    )
    entradas = caso["entradas"]
    situacao_esperada = caso["esperado"]["situacao_economica"]

    base = carregar_base()
    resultado = diagnosticar(entradas, base=base)

    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()
    app.session_state[CHAVE_RESULTADO] = resultado
    app.run()

    assert not app.exception
    assert resultado.memoria.valor("situacao_economica").valor == situacao_esperada

    subheaders = [s.value for s in app.subheader]
    assert "Diagnóstico Econômico" in subheaders
    assert "Fazenda × Mercado da UF (CONAB)" in subheaders
    assert "Composição do Custo Operacional Efetivo (COE)" in subheaders
    expanders = [e.label for e in app.expander]
    assert "Memória de trabalho (todos os fatos)" in expanders
    assert "Como cheguei aqui?" in expanders

    tela = " ".join(m.value for m in app.markdown)
    assert f'<div class="el-situacao">{situacao_esperada}</div>' in tela
    assert "Base de conhecimento v" in tela
    assert "Snapshot CONAB de 20/10/2026" in tela


def test_como_e_memoria_aparecem_no_parecer():
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()
    _clicar(app.sidebar.button, "Carregar fazenda-exemplo")
    for _ in carregar_base().secoes:
        _clicar(app.button, "Avançar")
    _clicar(app.button, "Gerar diagnóstico")

    assert not app.exception
    tela = " ".join(m.value for m in app.markdown)
    assert "Concluído pela regra" in tela
    assert "Premissas avaliadas" in tela
    assert "Memória de trabalho (todos os fatos)" in [e.label for e in app.expander]


def test_por_que_aparece_no_formulario():
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()
    _clicar(app.button, "Avançar")  # etapa 1 (Rebanho)

    expanders = [e.label for e in app.expander]
    assert "Por que pergunto?" in expanders

    tela = " ".join(m.value for m in app.markdown)
    assert "R-IND-" in tela or "R-CAU-" in tela
