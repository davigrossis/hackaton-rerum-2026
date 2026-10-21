"""Indicadores econômicos e zootécnicos: COE, COT, CT, custo por litro, margens, % de vacas em lactação."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from motor.regras import Base

DIAS_NO_MES: int = 30
TAXA_CAPITAL_MENSAL: float = (
    0.005  # PENDENTE: custo de oportunidade de 6% a.a. / 12 meses
)


@dataclass(frozen=True)
class Indicador:
    """Definição de um indicador calculado no domínio leiteiro."""

    nome: str
    unidade: str
    formula: str
    entradas: tuple[str, ...]
    opcionais: tuple[str, ...] = ()


INDICADORES: tuple[Indicador, ...] = (
    Indicador(
        nome="receita_leite",
        unidade="R$",
        formula="producao_litros * preco_leite_fazenda",
        entradas=("producao_litros", "preco_leite_fazenda"),
    ),
    Indicador(
        nome="receita_total",
        unidade="R$",
        formula="receita_leite + outras_receitas",
        entradas=("receita_leite",),
        opcionais=("outras_receitas",),
    ),
    Indicador(
        nome="custo_alimentar",
        unidade="R$",
        formula="custo_concentrado + custo_volumoso + custo_mineral",
        entradas=("custo_concentrado", "custo_volumoso"),
        opcionais=("custo_mineral",),
    ),
    Indicador(
        nome="coe",
        unidade="R$",
        formula="custo_concentrado + custo_volumoso + custo_mineral + custo_mao_obra_contratada + custo_sanidade_reproducao + custo_energia_combustivel + custo_outros",
        entradas=(
            "custo_concentrado",
            "custo_volumoso",
            "custo_mao_obra_contratada",
        ),
        opcionais=(
            "custo_mineral",
            "custo_sanidade_reproducao",
            "custo_energia_combustivel",
            "custo_outros",
        ),
    ),
    Indicador(
        nome="cot",
        unidade="R$",
        formula="coe + depreciacao + pro_labore",
        entradas=("coe", "depreciacao", "pro_labore"),
    ),
    Indicador(
        nome="remuneracao_capital",
        unidade="R$",
        formula="capital_investido * 0.005",
        entradas=("capital_investido",),
    ),
    Indicador(
        nome="ct",
        unidade="R$",
        formula="cot + remuneracao_capital",
        entradas=("cot", "remuneracao_capital"),
    ),
    Indicador(
        nome="coe_por_litro",
        unidade="R$/L",
        formula="coe / producao_litros",
        entradas=("coe", "producao_litros"),
    ),
    Indicador(
        nome="cot_por_litro",
        unidade="R$/L",
        formula="cot / producao_litros",
        entradas=("cot", "producao_litros"),
    ),
    Indicador(
        nome="ct_por_litro",
        unidade="R$/L",
        formula="ct / producao_litros",
        entradas=("ct", "producao_litros"),
    ),
    Indicador(
        nome="margem_bruta",
        unidade="R$",
        formula="receita_total - coe",
        entradas=("receita_total", "coe"),
    ),
    Indicador(
        nome="margem_liquida",
        unidade="R$",
        formula="receita_total - cot",
        entradas=("receita_total", "cot"),
    ),
    Indicador(
        nome="lucro",
        unidade="R$",
        formula="receita_total - ct",
        entradas=("receita_total", "ct"),
    ),
    Indicador(
        nome="pct_vacas_lactacao",
        unidade="%",
        formula="(vacas_lactacao / (vacas_lactacao + vacas_secas)) * 100",
        entradas=("vacas_lactacao", "vacas_secas"),
    ),
    Indicador(
        nome="litros_vaca_dia",
        unidade="L/dia",
        formula="producao_litros / (vacas_lactacao * 30)",
        entradas=("producao_litros", "vacas_lactacao"),
    ),
    Indicador(
        nome="pct_alimentacao_coe",
        unidade="%",
        formula="(custo_alimentar / coe) * 100",
        entradas=("custo_alimentar", "coe"),
    ),
    Indicador(
        nome="pct_concentrado_receita",
        unidade="%",
        formula="(custo_concentrado / receita_total) * 100",
        entradas=("custo_concentrado", "receita_total"),
    ),
    Indicador(
        nome="litros_ha",
        unidade="L/ha",
        formula="producao_litros / area_ha",
        entradas=("producao_litros", "area_ha"),
    ),
    Indicador(
        nome="litros_dia_homem",
        unidade="L/dia-homem",
        formula="(producao_litros / 30) / pessoas",
        entradas=("producao_litros", "pessoas"),
    ),
    Indicador(
        nome="preco_concentrado_kg",
        unidade="R$/kg",
        formula="custo_concentrado / concentrado_kg",
        entradas=("custo_concentrado", "concentrado_kg"),
    ),
    Indicador(
        nome="preco_leite_relativo_uf",
        unidade="razão",
        formula="preco_leite_fazenda / preco_leite_uf",
        entradas=("preco_leite_fazenda", "preco_leite_uf"),
    ),
)


def calcular_indicadores(
    entradas: dict[str, float | None],
    externos: dict[str, float | None],
    base: Base | None = None,
) -> dict[str, dict]:
    """Calcula indicadores econômicos e zootécnicos do tema T3.

    Devolve {nome: {"valor": float, "unidade": str, "formula": str, "entradas": tuple[str, ...], "detalhe": str}}
    apenas para os indicadores cujas entradas obrigatórias estejam presentes e válidas.
    Entrada ausente ou divisor zero faz com que o indicador não entre (não vira zero nem quebra).
    """
    contexto: dict[str, float] = {}
    for fonte in (entradas, externos):
        for k, v in fonte.items():
            if v is not None:
                contexto[k] = float(v)

    resultado: dict[str, dict] = {}

    for ind in INDICADORES:
        # 1. Verifica se todas as entradas obrigatórias estão presentes
        if not all(e in contexto for e in ind.entradas):
            continue

        nome = ind.nome
        valor: float | None = None
        usadas: list[str] = list(ind.entradas)
        detalhe: str = ""

        if nome == "receita_leite":
            p_litros = contexto["producao_litros"]
            p_preco = contexto["preco_leite_fazenda"]
            valor = p_litros * p_preco
            detalhe = f"{p_litros:.2f} L * R$ {p_preco:.2f}/L"

        elif nome == "receita_total":
            r_leite = contexto["receita_leite"]
            if "outras_receitas" in contexto:
                outras = contexto["outras_receitas"]
                valor = r_leite + outras
                usadas.append("outras_receitas")
                detalhe = f"R$ {r_leite:.2f} (leite) + R$ {outras:.2f} (outras)"
            else:
                valor = r_leite
                detalhe = f"R$ {r_leite:.2f} (leite); outras receitas não informadas"

        elif nome == "custo_alimentar":
            c_conc = contexto["custo_concentrado"]
            c_vol = contexto["custo_volumoso"]
            if "custo_mineral" in contexto:
                c_min = contexto["custo_mineral"]
                valor = c_conc + c_vol + c_min
                usadas.append("custo_mineral")
                detalhe = f"Concentrado (R$ {c_conc:.2f}) + Volumoso (R$ {c_vol:.2f}) + Mineral (R$ {c_min:.2f})"
            else:
                valor = c_conc + c_vol
                detalhe = f"Concentrado (R$ {c_conc:.2f}) + Volumoso (R$ {c_vol:.2f}); mineral não informado"

        elif nome == "coe":
            c_conc = contexto["custo_concentrado"]
            c_vol = contexto["custo_volumoso"]
            c_mo = contexto["custo_mao_obra_contratada"]
            soma = c_conc + c_vol + c_mo
            partes_detalhe = [
                f"Concentrado (R$ {c_conc:.2f})",
                f"Volumoso (R$ {c_vol:.2f})",
                f"Mão de obra (R$ {c_mo:.2f})",
            ]
            opcionais_omitidos = []
            for opt, rotulo in (
                ("custo_mineral", "Mineral"),
                ("custo_sanidade_reproducao", "Sanidade"),
                ("custo_energia_combustivel", "Energia"),
                ("custo_outros", "Outros"),
            ):
                if opt in contexto:
                    val_opt = contexto[opt]
                    soma += val_opt
                    usadas.append(opt)
                    partes_detalhe.append(f"{rotulo} (R$ {val_opt:.2f})")
                else:
                    opcionais_omitidos.append(rotulo.lower())

            valor = soma
            detalhe = " + ".join(partes_detalhe)
            if opcionais_omitidos:
                detalhe += f"; não informados: {', '.join(opcionais_omitidos)}"

        elif nome == "cot":
            v_coe = contexto["coe"]
            v_dep = contexto["depreciacao"]
            v_pl = contexto["pro_labore"]
            valor = v_coe + v_dep + v_pl
            detalhe = f"COE (R$ {v_coe:.2f}) + Depreciação (R$ {v_dep:.2f}) + Pró-labore (R$ {v_pl:.2f})"

        elif nome == "remuneracao_capital":
            cap = contexto["capital_investido"]
            valor = cap * TAXA_CAPITAL_MENSAL
            detalhe = f"R$ {cap:.2f} * {TAXA_CAPITAL_MENSAL} (taxa mensal)"

        elif nome == "ct":
            v_cot = contexto["cot"]
            v_rem = contexto["remuneracao_capital"]
            valor = v_cot + v_rem
            detalhe = f"COT (R$ {v_cot:.2f}) + Remuneração Capital (R$ {v_rem:.2f})"

        elif nome == "coe_por_litro":
            p_litros = contexto["producao_litros"]
            if p_litros <= 0:
                continue
            valor = contexto["coe"] / p_litros
            detalhe = f"R$ {contexto['coe']:.2f} / {p_litros:.2f} L"

        elif nome == "cot_por_litro":
            p_litros = contexto["producao_litros"]
            if p_litros <= 0:
                continue
            valor = contexto["cot"] / p_litros
            detalhe = f"R$ {contexto['cot']:.2f} / {p_litros:.2f} L"

        elif nome == "ct_por_litro":
            p_litros = contexto["producao_litros"]
            if p_litros <= 0:
                continue
            valor = contexto["ct"] / p_litros
            detalhe = f"R$ {contexto['ct']:.2f} / {p_litros:.2f} L"

        elif nome == "margem_bruta":
            v_rec = contexto["receita_total"]
            v_coe = contexto["coe"]
            valor = v_rec - v_coe
            detalhe = f"Receita Total (R$ {v_rec:.2f}) - COE (R$ {v_coe:.2f})"

        elif nome == "margem_liquida":
            v_rec = contexto["receita_total"]
            v_cot = contexto["cot"]
            valor = v_rec - v_cot
            detalhe = f"Receita Total (R$ {v_rec:.2f}) - COT (R$ {v_cot:.2f})"

        elif nome == "lucro":
            v_rec = contexto["receita_total"]
            v_ct = contexto["ct"]
            valor = v_rec - v_ct
            detalhe = f"Receita Total (R$ {v_rec:.2f}) - CT (R$ {v_ct:.2f})"

        elif nome == "pct_vacas_lactacao":
            vl = contexto["vacas_lactacao"]
            vs = contexto["vacas_secas"]
            total_vacas = vl + vs
            if total_vacas <= 0:
                continue
            valor = (vl / total_vacas) * 100
            detalhe = f"({vl:.0f} lactação / {total_vacas:.0f} total) * 100"

        elif nome == "litros_vaca_dia":
            vl = contexto["vacas_lactacao"]
            denominador = vl * DIAS_NO_MES
            if denominador <= 0:
                continue
            valor = contexto["producao_litros"] / denominador
            detalhe = f"{contexto['producao_litros']:.2f} L / ({vl:.0f} vacas * {DIAS_NO_MES} dias)"

        elif nome == "pct_alimentacao_coe":
            v_coe = contexto["coe"]
            if v_coe <= 0:
                continue
            valor = (contexto["custo_alimentar"] / v_coe) * 100
            detalhe = f"(R$ {contexto['custo_alimentar']:.2f} / R$ {v_coe:.2f}) * 100"

        elif nome == "pct_concentrado_receita":
            v_rec = contexto["receita_total"]
            if v_rec <= 0:
                continue
            valor = (contexto["custo_concentrado"] / v_rec) * 100
            detalhe = f"(R$ {contexto['custo_concentrado']:.2f} / R$ {v_rec:.2f}) * 100"

        elif nome == "litros_ha":
            ha = contexto["area_ha"]
            if ha <= 0:
                continue
            valor = contexto["producao_litros"] / ha
            detalhe = f"{contexto['producao_litros']:.2f} L / {ha:.2f} ha"

        elif nome == "litros_dia_homem":
            pessoas = contexto["pessoas"]
            if pessoas <= 0:
                continue
            valor = (contexto["producao_litros"] / DIAS_NO_MES) / pessoas
            detalhe = f"({contexto['producao_litros']:.2f} L / {DIAS_NO_MES} dias) / {pessoas:.1f} pessoas"

        elif nome == "preco_concentrado_kg":
            kg = contexto["concentrado_kg"]
            if kg <= 0:
                continue
            valor = contexto["custo_concentrado"] / kg
            detalhe = f"R$ {contexto['custo_concentrado']:.2f} / {kg:.2f} kg"

        elif nome == "preco_leite_relativo_uf":
            uf = contexto["preco_leite_uf"]
            if uf <= 0:
                continue
            valor = contexto["preco_leite_fazenda"] / uf
            detalhe = f"R$ {contexto['preco_leite_fazenda']:.2f} / R$ {uf:.2f}"

        if valor is not None:
            contexto[nome] = valor
            resultado[nome] = {
                "valor": valor,
                "unidade": ind.unidade,
                "formula": ind.formula,
                "entradas": tuple(usadas),
                "detalhe": detalhe,
            }

    return resultado
