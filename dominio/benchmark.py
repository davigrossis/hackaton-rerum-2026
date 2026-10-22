"""Produtividade de leite por vaca na UF, a partir dos snapshots da PPM/IBGE em dados/raw/.

Tabela 74: produção de leite (mil litros). Tabela 94: vacas ordenhadas (cabeças).
Consultas originais e atualização em dados/raw/FONTES.md.
"""

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_PRODUCAO = RAIZ / "dados" / "raw" / "ibge_ppm_74.json"
ARQUIVO_VACAS = RAIZ / "dados" / "raw" / "ibge_ppm_94.json"
FONTE = "IBGE – PPM, tabelas 74 e 94"
DIAS_NO_ANO = 365

# O SIDRA identifica a UF pelo código do IBGE (31 = Minas Gerais), não pela sigla.
CODIGO_UF = {
    "RO": 11, "AC": 12, "AM": 13, "RR": 14, "PA": 15, "AP": 16, "TO": 17,
    "MA": 21, "PI": 22, "CE": 23, "RN": 24, "PB": 25, "PE": 26, "AL": 27,
    "SE": 28, "BA": 29, "MG": 31, "ES": 32, "RJ": 33, "SP": 35,
    "PR": 41, "SC": 42, "RS": 43, "MS": 50, "MT": 51, "GO": 52, "DF": 53,
}  # fmt: skip

# {(código da UF, ano): valor}
Tabela = dict[tuple[int, int], float]


def ler_tabela(arquivo: Path) -> Tabela:
    """Valores por UF e ano de um JSON do SIDRA (a primeira linha é o cabeçalho).

    Símbolos no lugar do número (-, ..., X) ficam de fora: não viram zero.
    """
    tabela: Tabela = {}
    for linha in json.loads(arquivo.read_text(encoding="utf-8"))[1:]:
        try:
            tabela[int(linha["D1C"]), int(linha["D3C"])] = float(linha["V"])
        except ValueError:
            continue
    return tabela


def fatos_benchmark(
    uf: str,
    ano: int,
    producao: Tabela | None = None,
    vacas: Tabela | None = None,
) -> dict[str, dict]:
    """Produtividade média da UF no último ano da PPM anterior a `ano`, em L/vaca/dia.

    Mil litros × 1.000 ÷ vacas ordenhadas ÷ 365. O ano do mês fica de fora porque a
    PPM de um ano só sai no ano seguinte. Sem dado, o fato não entra.
    """
    producao = ler_tabela(ARQUIVO_PRODUCAO) if producao is None else producao
    vacas = ler_tabela(ARQUIVO_VACAS) if vacas is None else vacas
    codigo = CODIGO_UF.get(uf.strip().upper())
    anos = [
        a for c, a in producao if c == codigo and a < ano and vacas.get((c, a), 0) > 0
    ]
    if not anos:
        return {}
    ultimo = max(anos)
    valor = producao[codigo, ultimo] * 1000 / vacas[codigo, ultimo] / DIAS_NO_ANO
    return {
        "produtividade_regional_ibge": {
            "valor": round(valor, 4),
            "unidade": "L/vaca/dia",
            "fonte": FONTE,
            "periodo": str(ultimo),
        }
    }
