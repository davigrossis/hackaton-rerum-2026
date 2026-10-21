"""Testes dos 21 indicadores econômicos e zootécnicos (dominio/indicadores.py)."""

from __future__ import annotations

import pytest

from dominio.indicadores import (
    DIAS_NO_MES,
    INDICADORES,
    TAXA_CAPITAL_MENSAL,
    calcular_indicadores,
)
from motor.regras import carregar_base

ENTRADAS_FAZENDA_PADRAO: dict[str, float] = {
    "producao_litros": 24000.0,
    "preco_leite_fazenda": 2.90,
    "outras_receitas": 1500.0,
    "vacas_lactacao": 40.0,
    "vacas_secas": 8.0,
    "custo_concentrado": 24000.0,
    "concentrado_kg": 16000.0,
    "custo_volumoso": 12000.0,
    "custo_mineral": 1500.0,
    "custo_mao_obra_contratada": 9000.0,
    "custo_sanidade_reproducao": 2500.0,
    "custo_energia_combustivel": 3000.0,
    "custo_outros": 2000.0,
    "depreciacao": 5000.0,
    "pro_labore": 7000.0,
    "capital_investido": 1200000.0,
    "area_ha": 50.0,
    "pessoas": 3.0,
}

EXTERNOS_PADRAO: dict[str, float] = {
    "preco_leite_uf": 3.04,
}


def test_constantes_dominio():
    assert DIAS_NO_MES == 30
    assert TAXA_CAPITAL_MENSAL == 0.005


def test_fazenda_padrao_calculada_a_mao():
    res = calcular_indicadores(ENTRADAS_FAZENDA_PADRAO, EXTERNOS_PADRAO)
    assert len(res) == 21

    # 1. receita_leite
    assert res["receita_leite"]["valor"] == pytest.approx(69600.00, abs=0.01)
    assert res["receita_leite"]["unidade"] == "R$"
    assert res["receita_leite"]["entradas"] == (
        "producao_litros",
        "preco_leite_fazenda",
    )

    # 2. receita_total
    assert res["receita_total"]["valor"] == pytest.approx(71100.00, abs=0.01)
    assert res["receita_total"]["unidade"] == "R$"
    assert res["receita_total"]["entradas"] == ("receita_leite", "outras_receitas")

    # 3. custo_alimentar
    assert res["custo_alimentar"]["valor"] == pytest.approx(37500.00, abs=0.01)
    assert res["custo_alimentar"]["unidade"] == "R$"
    assert res["custo_alimentar"]["entradas"] == (
        "custo_concentrado",
        "custo_volumoso",
        "custo_mineral",
    )

    # 4. coe
    assert res["coe"]["valor"] == pytest.approx(54000.00, abs=0.01)
    assert res["coe"]["unidade"] == "R$"
    assert res["coe"]["entradas"] == (
        "custo_concentrado",
        "custo_volumoso",
        "custo_mao_obra_contratada",
        "custo_mineral",
        "custo_sanidade_reproducao",
        "custo_energia_combustivel",
        "custo_outros",
    )

    # 5. cot
    assert res["cot"]["valor"] == pytest.approx(66000.00, abs=0.01)
    assert res["cot"]["unidade"] == "R$"
    assert res["cot"]["entradas"] == ("coe", "depreciacao", "pro_labore")

    # 6. remuneracao_capital
    assert res["remuneracao_capital"]["valor"] == pytest.approx(6000.00, abs=0.01)
    assert res["remuneracao_capital"]["unidade"] == "R$"
    assert res["remuneracao_capital"]["entradas"] == ("capital_investido",)

    # 7. ct
    assert res["ct"]["valor"] == pytest.approx(72000.00, abs=0.01)
    assert res["ct"]["unidade"] == "R$"
    assert res["ct"]["entradas"] == ("cot", "remuneracao_capital")

    # 8. coe_por_litro
    assert res["coe_por_litro"]["valor"] == pytest.approx(2.25, abs=0.01)
    assert res["coe_por_litro"]["unidade"] == "R$/L"
    assert res["coe_por_litro"]["entradas"] == ("coe", "producao_litros")

    # 9. cot_por_litro
    assert res["cot_por_litro"]["valor"] == pytest.approx(2.75, abs=0.01)
    assert res["cot_por_litro"]["unidade"] == "R$/L"
    assert res["cot_por_litro"]["entradas"] == ("cot", "producao_litros")

    # 10. ct_por_litro
    assert res["ct_por_litro"]["valor"] == pytest.approx(3.00, abs=0.01)
    assert res["ct_por_litro"]["unidade"] == "R$/L"
    assert res["ct_por_litro"]["entradas"] == ("ct", "producao_litros")

    # 11. margem_bruta
    assert res["margem_bruta"]["valor"] == pytest.approx(17100.00, abs=0.01)
    assert res["margem_bruta"]["unidade"] == "R$"
    assert res["margem_bruta"]["entradas"] == ("receita_total", "coe")

    # 12. margem_liquida
    assert res["margem_liquida"]["valor"] == pytest.approx(5100.00, abs=0.01)
    assert res["margem_liquida"]["unidade"] == "R$"
    assert res["margem_liquida"]["entradas"] == ("receita_total", "cot")

    # 13. lucro
    assert res["lucro"]["valor"] == pytest.approx(-900.00, abs=0.01)
    assert res["lucro"]["unidade"] == "R$"
    assert res["lucro"]["entradas"] == ("receita_total", "ct")

    # 14. pct_vacas_lactacao
    assert res["pct_vacas_lactacao"]["valor"] == pytest.approx(83.33, abs=0.01)
    assert res["pct_vacas_lactacao"]["unidade"] == "%"
    assert res["pct_vacas_lactacao"]["entradas"] == ("vacas_lactacao", "vacas_secas")

    # 15. litros_vaca_dia
    assert res["litros_vaca_dia"]["valor"] == pytest.approx(20.00, abs=0.01)
    assert res["litros_vaca_dia"]["unidade"] == "L/dia"
    assert res["litros_vaca_dia"]["entradas"] == ("producao_litros", "vacas_lactacao")

    # 16. pct_alimentacao_coe
    assert res["pct_alimentacao_coe"]["valor"] == pytest.approx(69.44, abs=0.01)
    assert res["pct_alimentacao_coe"]["unidade"] == "%"
    assert res["pct_alimentacao_coe"]["entradas"] == ("custo_alimentar", "coe")

    # 17. pct_concentrado_receita
    assert res["pct_concentrado_receita"]["valor"] == pytest.approx(33.76, abs=0.01)
    assert res["pct_concentrado_receita"]["unidade"] == "%"
    assert res["pct_concentrado_receita"]["entradas"] == (
        "custo_concentrado",
        "receita_total",
    )

    # 18. litros_ha
    assert res["litros_ha"]["valor"] == pytest.approx(480.00, abs=0.01)
    assert res["litros_ha"]["unidade"] == "L/ha"
    assert res["litros_ha"]["entradas"] == ("producao_litros", "area_ha")

    # 19. litros_dia_homem
    assert res["litros_dia_homem"]["valor"] == pytest.approx(266.67, abs=0.01)
    assert res["litros_dia_homem"]["unidade"] == "L/dia-homem"
    assert res["litros_dia_homem"]["entradas"] == ("producao_litros", "pessoas")

    # 20. preco_concentrado_kg
    assert res["preco_concentrado_kg"]["valor"] == pytest.approx(1.50, abs=0.01)
    assert res["preco_concentrado_kg"]["unidade"] == "R$/kg"
    assert res["preco_concentrado_kg"]["entradas"] == (
        "custo_concentrado",
        "concentrado_kg",
    )

    # 21. preco_leite_relativo_uf
    assert res["preco_leite_relativo_uf"]["valor"] == pytest.approx(0.95, abs=0.01)
    assert res["preco_leite_relativo_uf"]["unidade"] == "razão"
    assert res["preco_leite_relativo_uf"]["entradas"] == (
        "preco_leite_fazenda",
        "preco_leite_uf",
    )


def test_opcionais_ausentes():
    entradas = dict(ENTRADAS_FAZENDA_PADRAO)
    del entradas["custo_mineral"]
    del entradas["custo_sanidade_reproducao"]
    del entradas["custo_energia_combustivel"]
    del entradas["custo_outros"]

    res = calcular_indicadores(entradas, EXTERNOS_PADRAO)

    # custo_alimentar sem mineral: 24000 + 12000 = 36000
    assert res["custo_alimentar"]["valor"] == pytest.approx(36000.00, abs=0.01)
    assert res["custo_alimentar"]["entradas"] == (
        "custo_concentrado",
        "custo_volumoso",
    )
    assert "mineral não informado" in res["custo_alimentar"]["detalhe"]

    # coe sem opcionais: 24000 + 12000 + 9000 = 45000
    assert res["coe"]["valor"] == pytest.approx(45000.00, abs=0.01)
    assert res["coe"]["entradas"] == (
        "custo_concentrado",
        "custo_volumoso",
        "custo_mao_obra_contratada",
    )
    assert "não informados" in res["coe"]["detalhe"]


def test_sem_outras_receitas():
    entradas = dict(ENTRADAS_FAZENDA_PADRAO)
    del entradas["outras_receitas"]

    res = calcular_indicadores(entradas, EXTERNOS_PADRAO)
    assert res["receita_total"]["valor"] == res["receita_leite"]["valor"]
    assert res["receita_total"]["entradas"] == ("receita_leite",)
    assert "outras receitas não informadas" in res["receita_total"]["detalhe"]


def test_entradas_none_tem_mesmo_efeito_de_ausentes():
    entradas = dict(ENTRADAS_FAZENDA_PADRAO)
    entradas["outras_receitas"] = None
    entradas["custo_mineral"] = None
    entradas["custo_sanidade_reproducao"] = None
    entradas["custo_energia_combustivel"] = None
    entradas["custo_outros"] = None

    res = calcular_indicadores(entradas, EXTERNOS_PADRAO)
    assert res["receita_total"]["valor"] == res["receita_leite"]["valor"]
    assert res["receita_total"]["entradas"] == ("receita_leite",)
    assert res["custo_alimentar"]["valor"] == pytest.approx(36000.00, abs=0.01)
    assert res["coe"]["valor"] == pytest.approx(45000.00, abs=0.01)


def test_ausencia_de_capital_investido():
    entradas = dict(ENTRADAS_FAZENDA_PADRAO)
    del entradas["capital_investido"]

    res = calcular_indicadores(entradas, EXTERNOS_PADRAO)
    assert "remuneracao_capital" not in res
    assert "ct" not in res
    assert "ct_por_litro" not in res
    assert "lucro" not in res
    # Os outros 17 indicadores devem estar calculados
    assert len(res) == 17
    assert "cot" in res
    assert "margem_liquida" in res


def test_ausencia_de_zootecnicos_secundarios():
    entradas = dict(ENTRADAS_FAZENDA_PADRAO)
    del entradas["area_ha"]
    del entradas["pessoas"]
    del entradas["concentrado_kg"]

    res = calcular_indicadores(entradas, EXTERNOS_PADRAO)
    assert "litros_ha" not in res
    assert "litros_dia_homem" not in res
    assert "preco_concentrado_kg" not in res
    assert len(res) == 18


def test_divisores_zero_e_negativos_nao_quebram():
    # Produção zero
    entradas_zero_prod = dict(ENTRADAS_FAZENDA_PADRAO, producao_litros=0.0)
    del entradas_zero_prod["outras_receitas"]  # receita_total também zera
    res_zero = calcular_indicadores(entradas_zero_prod, EXTERNOS_PADRAO)

    assert "coe_por_litro" not in res_zero
    assert "cot_por_litro" not in res_zero
    assert "ct_por_litro" not in res_zero
    assert "pct_concentrado_receita" not in res_zero

    # Rebanho zerado
    entradas_zero_vacas = dict(
        ENTRADAS_FAZENDA_PADRAO, vacas_lactacao=0.0, vacas_secas=0.0
    )
    res_vacas = calcular_indicadores(entradas_zero_vacas, EXTERNOS_PADRAO)
    assert "pct_vacas_lactacao" not in res_vacas
    assert "litros_vaca_dia" not in res_vacas

    # COE zero
    entradas_custo_zero = dict(
        ENTRADAS_FAZENDA_PADRAO,
        custo_concentrado=0.0,
        custo_volumoso=0.0,
        custo_mineral=0.0,
        custo_mao_obra_contratada=0.0,
        custo_sanidade_reproducao=0.0,
        custo_energia_combustivel=0.0,
        custo_outros=0.0,
    )
    res_custos = calcular_indicadores(entradas_custo_zero, EXTERNOS_PADRAO)
    assert res_custos["coe"]["valor"] == 0.0
    assert "pct_alimentacao_coe" not in res_custos

    # Preço UF zero
    externos_zero_uf = {"preco_leite_uf": 0.0}
    res_uf = calcular_indicadores(ENTRADAS_FAZENDA_PADRAO, externos_zero_uf)
    assert "preco_leite_relativo_uf" not in res_uf


def test_imutabilidade_dos_argumentos():
    entradas_originais = dict(ENTRADAS_FAZENDA_PADRAO)
    externos_originais = dict(EXTERNOS_PADRAO)

    entradas_copia = dict(entradas_originais)
    externos_copia = dict(externos_originais)

    calcular_indicadores(entradas_copia, externos_copia)

    assert entradas_copia == entradas_originais
    assert externos_copia == externos_originais


def test_indicadores_sincronizados_com_variaveis_yaml():
    base = carregar_base()
    calculadas = {v.nome: v for v in base.variaveis.values() if v.grupo == "calculadas"}

    assert len(INDICADORES) == len(calculadas) == 21

    for ind in INDICADORES:
        assert ind.nome in calculadas, f"Indicador '{ind.nome}' não está no YAML"
        var_yaml = calculadas[ind.nome]
        assert ind.unidade == var_yaml.unidade, (
            f"Unidade de '{ind.nome}' diverge: {ind.unidade} != {var_yaml.unidade}"
        )
        assert ind.formula == var_yaml.formula, (
            f"Fórmula de '{ind.nome}' diverge: {ind.formula} != {var_yaml.formula}"
        )
        assert ind.entradas == var_yaml.entradas, (
            f"Entradas de '{ind.nome}' divergem: {ind.entradas} != {var_yaml.entradas}"
        )
        assert ind.opcionais == var_yaml.opcionais, (
            f"Opcionais de '{ind.nome}' divergem: {ind.opcionais} != {var_yaml.opcionais}"
        )
