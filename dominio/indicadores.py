"""Indicadores econômicos e zootécnicos: COE, COT, CT, custo por litro, margens, % de vacas em lactação."""

from __future__ import annotations


def calcular_indicadores(
    entradas: dict[str, float], externos: dict[str, float]
) -> dict[str, dict]:
    """Calcula indicadores econômicos e zootécnicos do tema T3.

    Devolve {nome: {"valor": float, "unidade": str, "formula": str, "entradas": tuple[str, ...]}}
    apenas para os indicadores cujas entradas obrigatórias estejam presentes e válidas.
    Entrada ausente ou divisor zero faz com que o indicador não entre (não vira zero nem quebra).

    A ser implementado na issue #6.
    """
    raise NotImplementedError("calcular_indicadores será implementado na issue #6")
