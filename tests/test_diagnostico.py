"""Testes da ponta a ponta (#10): respostas -> mercado -> indicadores -> motor -> tela."""

from pathlib import Path

import pytest
import yaml
from streamlit.testing.v1 import AppTest

from dominio.diagnostico import diagnosticar
from interface.formulario import CHAVE_RESULTADO
from motor.inferencia import Resultado
from motor.regras import carregar_base

RAIZ = Path(__file__).resolve().parent.parent
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
