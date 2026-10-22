"""Testes dos casos conhecidos de fazendas (dados/casos/*.yaml).

Funciona como contrato executável entre formulário, mercado, indicadores,
regras de produção e motor de inferência.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from dominio.diagnostico import diagnosticar
from dominio.indicadores import calcular_indicadores
from dominio.mercado import fatos_mercado
from interface.formulario import problemas
from motor.inferencia import inferir
from motor.memoria import Memoria
from motor.regras import carregar_base

RAIZ = Path(__file__).resolve().parent.parent
PASTA_CONHECIMENTO = RAIZ / "conhecimento"
PASTA_CASOS = RAIZ / "dados" / "casos"


def carregar_casos() -> list[dict]:
    """Carrega todos os arquivos YAML de casos conhecidos em dados/casos/."""
    arquivos = sorted(PASTA_CASOS.glob("*.yaml"))
    casos = []
    for arq in arquivos:
        conteudo = yaml.safe_load(arq.read_text(encoding="utf-8"))
        if isinstance(conteudo, dict):
            casos.append(conteudo)
    return casos


CASOS = carregar_casos()
IDS_CASOS = [c["id"] for c in CASOS]


def _converter_periodo(mes_referencia: str) -> tuple[int, int]:
    """Converte 'MM/AAAA' para (AAAA, MM)."""
    partes = mes_referencia.strip().split("/")
    return (int(partes[1]), int(partes[0]))


def test_quatro_casos_conhecidos_existem():
    """Garante a existência e identificação dos 4 casos de referência."""
    assert len(CASOS) == 4
    nomes_arquivos = [p.name for p in sorted(PASTA_CASOS.glob("*.yaml"))]
    assert nomes_arquivos == [
        "01_lucro.yaml",
        "02_medio_prazo.yaml",
        "03_curto_prazo_alimentacao.yaml",
        "04_prejuizo_preco_reproducao.yaml",
    ]
    situacoes = [c["esperado"]["situacao_economica"] for c in CASOS]
    assert set(situacoes) == {"lucro", "medio_prazo", "curto_prazo", "prejuizo"}


@pytest.mark.parametrize("caso", CASOS, ids=IDS_CASOS)
def test_contrato_e_faixas_do_caso(caso: dict):
    """Valida formato, integridade, obrigatoriedade e limites zootécnicos das entradas."""
    assert {"id", "nome", "descricao", "entradas", "esperado"} <= caso.keys()
    base = carregar_base(PASTA_CONHECIMENTO)
    entradas = caso["entradas"]

    # 1. Todas as perguntas obrigatórias preenchidas e sem erros no formulário
    secoes_com_perguntas = [
        (s, [p for p in base.perguntas if p.secao == s.id]) for s in base.secoes
    ]
    erros = problemas(secoes_com_perguntas, entradas)
    assert erros == [], (
        f"Caso '{caso['id']}' possui pendências de preenchimento: {erros}"
    )

    # 2. Todas as variáveis de entrada respeitam tipos e faixas plausíveis declaradas
    perguntas_por_id = {p.id: p for p in base.perguntas}
    for chave, valor in entradas.items():
        assert chave in perguntas_por_id, (
            f"Chave '{chave}' não declarada em perguntas.yaml"
        )
        p = perguntas_por_id[chave]
        if p.tipo == "escolha":
            assert valor in (p.opcoes or ()), (
                f"Valor '{valor}' fora das opções de '{p.id}'"
            )
        elif p.tipo in ("numero", "inteiro") and p.faixa is not None:
            assert p.faixa[0] <= float(valor) <= p.faixa[1], (
                f"Valor {valor} de '{p.id}' fora da faixa permitida {p.faixa}"
            )

    # 3. Variáveis e categorias esperadas existem na base de conhecimento
    esperado = caso["esperado"]
    for nome_ind in esperado["indicadores"]:
        assert nome_ind in base.variaveis, f"Indicador '{nome_ind}' não existe na base"
        assert base.variaveis[nome_ind].grupo == "calculadas"

    var_sit = base.variaveis["situacao_economica"]
    assert esperado["situacao_economica"] in (var_sit.valores or ())

    for var_concl, val_concl in esperado.get("indicadores_concluidos", {}).items():
        assert var_concl in base.variaveis
        v = base.variaveis[var_concl]
        assert v.camada == "indicador"
        assert val_concl in (v.valores or ())

    for causa in esperado.get("causas", []):
        assert causa in (base.variaveis["causa"].valores or ())

    for rec in esperado.get("recomendacoes", []):
        assert rec in (base.variaveis["recomendacao"].valores or ())


@pytest.mark.parametrize("caso", CASOS, ids=IDS_CASOS)
def test_fatos_mercado_do_caso(caso: dict):
    """Confere os preços da CONAB recuperados para a UF e mês do caso."""
    uf = caso["entradas"]["uf"]
    periodo = _converter_periodo(caso["entradas"]["mes_referencia"])
    fatos = fatos_mercado(uf, periodo)

    externos_esperados = caso["esperado"]["externos"]
    for chave, valor_esperado in externos_esperados.items():
        assert chave in fatos, f"Fato de mercado '{chave}' ausente para {uf} {periodo}"
        assert fatos[chave]["valor"] == pytest.approx(valor_esperado, abs=1e-4)


@pytest.mark.parametrize("caso", CASOS, ids=IDS_CASOS)
def test_indicadores_calculados_a_mao(caso: dict):
    """Confere se todos os 21 indicadores batem com as contas feitas à mão em 2 casas decimais."""
    entradas_num = {
        k: float(v)
        for k, v in caso["entradas"].items()
        if isinstance(v, (int, float)) and not isinstance(v, bool)
    }
    periodo = _converter_periodo(caso["entradas"]["mes_referencia"])
    fatos = fatos_mercado(caso["entradas"]["uf"], periodo)
    externos_num = {k: v["valor"] for k, v in fatos.items()}

    resultado = calcular_indicadores(entradas_num, externos_num)
    assert len(resultado) == 21, (
        "Todos os 21 indicadores devem ser calculados nos casos padrão"
    )

    indicadores_esperados = caso["esperado"]["indicadores"]
    for nome_ind, valor_esperado in indicadores_esperados.items():
        assert nome_ind in resultado, f"Indicador '{nome_ind}' ausente no resultado"
        valor_obtido = resultado[nome_ind]["valor"]
        assert valor_obtido == pytest.approx(valor_esperado, abs=0.01), (
            f"Caso '{caso['id']}', indicador '{nome_ind}': esperado {valor_esperado:.2f}, "
            f"obtido {valor_obtido:.2f}"
        )


@pytest.mark.parametrize("caso", CASOS, ids=IDS_CASOS)
def test_enquadramento_matsunaga_e_sinais_dominio(caso: dict):
    """Valida a fundamentação econômica e os sinais de domínio característicos de cada perfil."""
    ind = caso["esperado"]["indicadores"]
    sit = caso["esperado"]["situacao_economica"]

    rec = ind["receita_total"]
    coe = ind["coe"]
    cot = ind["cot"]
    ct = ind["ct"]
    lucro = ind["lucro"]
    margem_liq = ind["margem_liquida"]
    margem_bruta = ind["margem_bruta"]

    if sit == "lucro":
        assert rec >= ct, "Lucro exige Receita Total >= CT"
        assert lucro >= 0.0
    elif sit == "medio_prazo":
        assert cot <= rec < ct, "Médio prazo exige COT <= Receita Total < CT"
        assert margem_liq >= 0.0 > lucro
    elif sit == "curto_prazo":
        assert coe <= rec < cot, "Curto prazo exige COE <= Receita Total < COT"
        assert margem_bruta >= 0.0 > margem_liq
    elif sit == "prejuizo":
        assert rec < coe, "Prejuízo exige Receita Total < COE"
        assert margem_bruta < 0.0

    # Sinais específicos dos casos com diagnóstico direcionado
    if caso["id"] == "curto_prazo_alimentacao":
        assert ind["pct_alimentacao_coe"] >= 70.0, (
            "Alimentação deve absorver >= 70% do COE"
        )
        assert ind["pct_concentrado_receita"] >= 40.0, (
            "Concentrado deve absorver >= 40% da receita"
        )
        assert ind["litros_vaca_dia"] <= 20.0, (
            "Produtividade moderada para não acionar exceção"
        )

    if caso["id"] == "prejuizo_preco_reproducao":
        assert ind["preco_leite_relativo_uf"] <= 0.85, (
            "Preço deve ser bem inferior à média da UF"
        )
        assert ind["pct_vacas_lactacao"] <= 65.0, (
            "Porcentagem de lactação deve indicar falha reprodutiva"
        )


@pytest.mark.parametrize("caso", CASOS, ids=IDS_CASOS)
def test_inferencia_regras_no_caso(caso: dict):
    """Executa a inferência quando as regras da camada estiverem carregadas na base.

    Permite que a suíte passe na Fase 2 antes do merge das regras da #8/#12 e as cobre automaticamente.
    """
    base = carregar_base(PASTA_CONHECIMENTO)
    regras_situacao = [r for r in base.regras if r.camada == "situacao"]
    if not regras_situacao:
        pytest.skip(
            "Base conhecimento/regras.yaml ainda sem regras de produção (issue #8)"
        )

    # 1. Popula memória de trabalho
    memoria = Memoria()
    for chave, valor in caso["entradas"].items():
        memoria.adicionar(chave, valor, cf=1.0, origem="usuario")

    periodo = _converter_periodo(caso["entradas"]["mes_referencia"])
    fatos = fatos_mercado(caso["entradas"]["uf"], periodo)
    for chave, fato in fatos.items():
        memoria.adicionar(chave, fato["valor"], cf=1.0, origem="externo")

    entradas_num = {
        k: float(v)
        for k, v in caso["entradas"].items()
        if isinstance(v, (int, float)) and not isinstance(v, bool)
    }
    externos_num = {k: v["valor"] for k, v in fatos.items()}
    indicadores = calcular_indicadores(entradas_num, externos_num)
    for nome_ind, dados_ind in indicadores.items():
        memoria.adicionar(nome_ind, dados_ind["valor"], cf=1.0, origem="calculado")

    # 2. Executa encadeamento progressivo do motor
    resultado = inferir(base, memoria)

    # 3. Valida situação econômica
    fato_sit = resultado.memoria.valor("situacao_economica")
    assert fato_sit is not None, "Inferência deve concluir situacao_economica"
    assert fato_sit.valor == caso["esperado"]["situacao_economica"]

    # 4. Valida conclusões de indicadores se regras existirem
    regras_indicador = [r for r in base.regras if r.camada == "indicador"]
    if regras_indicador:
        for var, val in caso["esperado"].get("indicadores_concluidos", {}).items():
            fato_ind = resultado.memoria.valor(var)
            if fato_ind is not None:
                assert fato_ind.valor == val

    # 5. Causas e recomendações (#12): o conjunto exato, nem a mais nem a menos
    for fato, chave in (("causa", "causas"), ("recomendacao", "recomendacoes")):
        obtidos = {f.valor for f in resultado.memoria.valores(fato)}
        assert obtidos == set(caso["esperado"][chave]), f"{caso['id']}: {chave}"

    # 6. Ponta a ponta (#10): diagnosticar chega ao mesmo traço da montagem manual
    res_diag = diagnosticar(caso["entradas"])
    assert [c.escolhida for c in res_diag.traco] == [
        c.escolhida for c in resultado.traco
    ]
    assert (
        res_diag.memoria.valor("situacao_economica").valor
        == caso["esperado"]["situacao_economica"]
    )
