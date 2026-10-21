"""Fatos de mercado por UF a partir do snapshot da CONAB em dados/raw/ (ver base.md).

Quais produtos são lidos, e como, fica no catálogo conhecimento/mercado.yaml.
"""

import csv
from collections.abc import Iterator
from pathlib import Path
from statistics import mean

import yaml

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_CONAB = RAIZ / "dados" / "raw" / "PrecosMensalUF.txt"
ARQUIVO_CATALOGO = RAIZ / "conhecimento" / "mercado.yaml"

CAMPOS_PRODUTO = (
    "nome",
    "descricao",
    "id_produto",
    "produto_conab",
    "classificacao_conab",
    "nivel",
    "unidade",
    "sem_preco_no_mes",
    "faixa",
    "fonte_faixa",
)
SEM_PRECO_NO_MES = ("omite", "usa_ultimo")
PREENCHER = "PREENCHER"  # marcador de campo que uma pessoa ainda precisa preencher

Periodo = tuple[int, int]  # (ano, mes)
# {(produto, uf): {(ano, mes): preço}}
Precos = dict[tuple[str, str], dict[Periodo, float]]


def carregar_catalogo(arquivo: Path = ARQUIVO_CATALOGO) -> dict:
    """Lê o catálogo de produtos e confere o preenchimento; erro vira ValueError."""
    arquivo = Path(arquivo)
    catalogo = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
    if not isinstance(catalogo, dict) or not {"fonte", "produtos"} <= catalogo.keys():
        raise ValueError(f"{arquivo.name}: precisa dos campos 'fonte' e 'produtos'")
    nomes: set[str] = set()
    chaves: set[tuple[str, str]] = set()
    for produto in catalogo["produtos"]:
        onde = f"{arquivo.name}, produto '{produto.get('nome', '?')}'"
        _validar_produto(produto, onde)
        chave = (produto["id_produto"], produto["nivel"])
        if produto["nome"] in nomes or chave in chaves:
            raise ValueError(f"{onde}: nome ou id_produto + nivel repetido")
        nomes.add(produto["nome"])
        chaves.add(chave)
    return catalogo


def _validar_produto(produto: dict, onde: str) -> None:
    for campo in CAMPOS_PRODUTO:
        if produto.get(campo) in (None, "", PREENCHER):
            raise ValueError(f"{onde}: falta preencher '{campo}'")
    id_produto = produto["id_produto"]
    if not (isinstance(id_produto, str) and id_produto.isdigit()):
        raise ValueError(f"{onde}: id_produto deve ser só dígitos e entre aspas")
    if produto["sem_preco_no_mes"] not in SEM_PRECO_NO_MES:
        raise ValueError(f"{onde}: sem_preco_no_mes deve ser omite ou usa_ultimo")
    faixa = produto["faixa"]
    if not (
        isinstance(faixa, list)
        and len(faixa) == 2
        and all(isinstance(v, int | float) for v in faixa)
        and faixa[0] < faixa[1]
    ):
        raise ValueError(
            f"{onde}: faixa deve ser [mínimo, máximo], com mínimo < máximo"
        )


def ler_linhas(arquivo: Path = ARQUIVO_CONAB) -> Iterator[dict]:
    """Percorre o snapshot com o formato já tratado (base.md, seção 2).

    Tira os espaços da largura fixa, troca a vírgula decimal por ponto e devolve
    valor None quando a cotação está vazia ou zerada.
    """
    with open(arquivo, encoding="latin-1", newline="") as f:
        for linha in csv.DictReader(f, delimiter=";"):
            texto = linha["valor_produto_kg"].strip()
            valor = float(texto.replace(",", ".")) if texto else 0.0
            yield {
                "id_produto": linha["id_produto"].strip(),
                "produto": linha["produto"].strip(),
                # o nome da coluna vem com erro de digitação na CONAB
                "classificacao": linha["classificao_produto"].strip(),
                "nivel": linha["dsc_nivel_comercializacao"].strip(),
                "uf": linha["uf"].strip(),
                "periodo": (int(linha["ano"]), int(linha["mes"])),
                "valor": valor if valor > 0 else None,
            }


def ler_precos(arquivo: Path = ARQUIVO_CONAB, catalogo: dict | None = None) -> Precos:
    """Preços dos produtos do catálogo: {(produto, uf): {(ano, mes): preço médio}}.

    Descarta vazios, zeros e valores fora da faixa do produto (provável erro de
    unidade); cotações repetidas na mesma chave viram a média.
    """
    catalogo = carregar_catalogo() if catalogo is None else catalogo
    produtos = {(p["id_produto"], p["nivel"]): p for p in catalogo["produtos"]}
    cotacoes: dict[tuple[str, str], dict[Periodo, list[float]]] = {}
    for linha in ler_linhas(arquivo):
        produto = produtos.get((linha["id_produto"], linha["nivel"]))
        if produto is None or linha["valor"] is None:
            continue
        minimo, maximo = produto["faixa"]
        if not minimo <= linha["valor"] <= maximo:
            continue
        serie = cotacoes.setdefault((produto["nome"], linha["uf"]), {})
        serie.setdefault(linha["periodo"], []).append(linha["valor"])
    return {
        chave: {periodo: mean(valores) for periodo, valores in serie.items()}
        for chave, serie in cotacoes.items()
    }


def _texto(periodo: Periodo) -> str:
    return f"{periodo[1]:02d}/{periodo[0]}"


def _texto_intervalo(periodos: list[Periodo]) -> str:
    """Ex.: "10/2025 a 09/2026 (8 meses)": a contagem mostra os meses sem cotação."""
    meses = "1 mês" if len(periodos) == 1 else f"{len(periodos)} meses"
    return f"{_texto(min(periodos))} a {_texto(max(periodos))} ({meses})"


def _fato(valor: float, unidade: str, periodo: str, fonte: str) -> dict:
    return {
        "valor": round(valor, 4),
        "unidade": unidade,
        "fonte": fonte,
        "periodo": periodo,
    }


def _nos_12_meses(periodo: Periodo, referencia: Periodo) -> bool:
    """Se `periodo` está na janela de 12 meses que termina em `referencia`."""
    distancia = (referencia[0] - periodo[0]) * 12 + referencia[1] - periodo[1]
    return 0 <= distancia < 12


def _ultimo_ate(serie: dict[Periodo, float], periodo: Periodo) -> Periodo | None:
    """Último mês com cotação até `periodo` (inclusive); None se não houver."""
    anteriores = [p for p in serie if p <= periodo]
    return max(anteriores) if anteriores else None


def fatos_mercado(
    uf: str,
    periodo: Periodo | None = None,
    precos: Precos | None = None,
    catalogo: dict | None = None,
) -> dict[str, dict]:
    """Fatos de mercado da UF no mês `periodo` (padrão: último mês com preço do leite).

    Cada fato é {valor, unidade, fonte, periodo}. Sem cotação, o fato não entra.
    Produto com `sem_preco_no_mes: usa_ultimo` usa o último preço até o mês pedido,
    e o período diz qual foi.
    """
    uf = uf.strip().upper()
    catalogo = carregar_catalogo() if catalogo is None else catalogo
    precos = ler_precos(catalogo=catalogo) if precos is None else precos
    fonte = catalogo["fonte"]
    leite = precos.get(("leite", uf), {})
    milho = precos.get(("milho", uf), {})
    if periodo is None:
        if not leite:
            return {}
        periodo = max(leite)

    fatos: dict[str, dict] = {}
    for produto in catalogo["produtos"]:
        serie = precos.get((produto["nome"], uf), {})
        if produto["sem_preco_no_mes"] == "usa_ultimo":
            mes = _ultimo_ate(serie, periodo)
        else:
            mes = periodo
        if mes in serie:
            fatos[f"preco_{produto['nome']}_uf"] = _fato(
                serie[mes], produto["unidade"], _texto(mes), fonte
            )

    # Fatos derivados: calculados aqui e dependem de leite e milho no catálogo.
    meses_leite = [p for p in leite if _nos_12_meses(p, periodo)]
    if meses_leite:
        fatos["preco_leite_uf_media_12m"] = _fato(
            mean(leite[p] for p in meses_leite),
            "R$/L",
            _texto_intervalo(meses_leite),
            fonte,
        )

    # Troca leite:milho = kg de milho que 1 L de leite compra, só em meses com os dois preços.
    trocas = {
        p: leite[p] / milho[p]
        for p in leite
        if p in milho and _nos_12_meses(p, periodo)
    }
    if periodo in trocas:
        fatos["troca_leite_milho_uf"] = _fato(
            trocas[periodo], "kg/L", _texto(periodo), fonte
        )
    if trocas:
        fatos["troca_leite_milho_uf_media_12m"] = _fato(
            mean(trocas.values()), "kg/L", _texto_intervalo(list(trocas)), fonte
        )
    return fatos
