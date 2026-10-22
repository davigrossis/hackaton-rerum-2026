"""Validação compartilhada e formulário da issue #14."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from dominio.diagnostico import diagnosticar, validar_respostas
from interface.formulario import estados_das_etapas, problemas, progresso_obrigatorias
from motor.regras import carregar_base

BASE = carregar_base()
NUMERICAS = [p for p in BASE.perguntas if p.faixa]
SECOES = [(s, [p for p in BASE.perguntas if p.secao == s.id]) for s in BASE.secoes]
RAIZ = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("p", NUMERICAS, ids=lambda p: p.id)
def test_limites_da_base(p):
    for valor in p.faixa:
        assert not validar_respostas({p.id: valor}, [p])
    for valor in (p.faixa[0] - 1, p.faixa[1] + 1):
        erro = validar_respostas({p.id: valor}, [p])[p.id]
        assert "entre" in erro
        assert p.unidade in erro


@pytest.mark.parametrize(
    "valor", [True, False, "10", float("nan"), float("inf"), -float("inf"), [], {}]
)
def test_numero_invalido_rejeitado_antes_do_mercado(valor, monkeypatch):
    def nao_consultar(*args):
        pytest.fail("Entradas inválidas não devem consultar mercado")

    monkeypatch.setattr("dominio.diagnostico.fatos_mercado", nao_consultar)
    with pytest.raises(ValueError, match="número finito"):
        diagnosticar({"vacas_lactacao": valor, "uf": "MG", "mes_referencia": "09/2026"})


def test_inteiro_nao_trunca_fracao():
    with pytest.raises(ValueError, match="inteiro"):
        diagnosticar({"vacas_lactacao": 1.5})
    assert (
        diagnosticar({"vacas_lactacao": 1.0}).memoria.valor("vacas_lactacao").valor == 1
    )


@pytest.mark.parametrize(
    "mes", ["00/2026", "13/2026", "1/2026", "01/0000", "01/26", "01/2026x", 92026]
)
def test_mes_invalido(mes):
    with pytest.raises(ValueError, match="MM/AAAA"):
        diagnosticar({"mes_referencia": mes})


@pytest.mark.parametrize("mes", ["01/0001", "12/9999", "09/2026"])
def test_mes_valido_independe_de_snapshot(mes):
    assert not validar_respostas(
        {"mes_referencia": mes}, BASE.perguntas, exigir_obrigatorias=False
    )


def test_uf_invalida():
    with pytest.raises(ValueError, match="opções"):
        diagnosticar({"uf": "XX"})


@pytest.mark.parametrize("vazio", [None, "", "   "])
def test_ausencia_normalizada_sem_mutacao(vazio):
    respostas = {"capital_investido": vazio, "mes_referencia": vazio, "uf": " MG "}
    original = respostas.copy()
    memoria = diagnosticar(
        respostas, estimados=frozenset({"capital_investido"})
    ).memoria
    assert respostas == original
    assert not memoria.tem("capital_investido")
    assert not memoria.tem("ct")
    assert not memoria.tem("mes_referencia")
    assert memoria.valor("uf").valor == "MG"
    assert not any(f.origens[-1].tipo == "externo" for f in memoria.fatos())
    assert "mes_referencia" in validar_respostas(respostas, BASE.perguntas)
    assert "capital_investido" not in validar_respostas(respostas, BASE.perguntas)


def test_diagnostico_vazio_e_zeros_permitidos():
    assert diagnosticar({}).memoria.fatos() == []
    respostas = {p.id: 0 for p in NUMERICAS if p.faixa[0] == 0}
    memoria = diagnosticar(respostas).memoria
    assert all(memoria.valor(nome).valor == 0 for nome in respostas)
    assert memoria.valor("coe").valor == 0
    assert memoria.valor("ct").valor == 0
    assert not memoria.tem("pct_alimentacao_coe")
    assert not memoria.tem("preco_concentrado_kg")


def test_zero_vacas_e_opcional_invalido_marcam_etapas():
    respostas = {"vacas_lactacao": 0, "ccs": -1}
    erros = validar_respostas(respostas, BASE.perguntas)
    assert "vacas_lactacao" in erros and "ccs" in erros
    with pytest.raises(ValueError, match="entre 1 e 5000"):
        diagnosticar(respostas)
    assert progresso_obrigatorias(SECOES, respostas)[0] == 0
    assert problemas(SECOES, respostas)
    assert "alerta" in estados_das_etapas(SECOES, respostas, len(SECOES))


def _clicar(app, rotulo):
    next(b for b in app.button if b.label == rotulo).click().run()


def test_formulario_vazio_chega_a_revisao_sem_quebrar():
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()
    for _ in BASE.secoes:
        _clicar(app, "Avançar")
    assert not app.exception
    assert next(b for b in app.button if b.label == "Gerar diagnóstico").disabled
    assert app.warning
    assert app.session_state["resultado"] is None


def test_revisao_bloqueia_zero_vacas_e_corrige_sem_perder_estimativa():
    app = AppTest.from_file(str(RAIZ / "app.py"), default_timeout=30).run()
    _clicar(app, "Carregar fazenda-exemplo")
    for _ in BASE.secoes:
        _clicar(app, "Avançar")
    # Injeta na revisão para exercitar a validação independente dos limites do widget.
    app.session_state["dados"]["vacas_lactacao"] = 0
    app.session_state["estimados"] = {"preco_leite_fazenda"}
    app.run()
    assert not app.exception
    assert next(b for b in app.button if b.label == "Gerar diagnóstico").disabled
    app.session_state["dados"]["vacas_lactacao"] = 30
    app.run()
    _clicar(app, "Gerar diagnóstico")
    assert not app.exception
    assert app.session_state["resultado"].memoria.valor("preco_leite_fazenda").cf == 0.7


def test_callback_revalida_e_descarta_resultado_anterior(monkeypatch):
    import app as entrada

    estado = {"resultado": object()}
    mensagens = []
    monkeypatch.setattr(entrada.st, "session_state", estado)
    monkeypatch.setattr(entrada.st, "error", mensagens.append)
    monkeypatch.setattr(entrada, "obter_base", lambda: BASE)

    def nao_diagnosticar(*args, **kwargs):
        pytest.fail("Callback não deve diagnosticar respostas inválidas")

    monkeypatch.setattr(entrada, "diagnosticar", nao_diagnosticar)
    entrada._gerar({"vacas_lactacao": 0})
    assert estado["resultado"] is None
    assert any("entre 1 e 5000" in m for m in mensagens)
