"""O catálogo conhecimento/mercado.yaml confere com a base da CONAB.

Cada produto do catálogo vira seus próprios casos de teste (parametrize): para
testar um produto novo, basta declará-lo no YAML.
"""

import pytest

from dados.rascunho_catalogo import rascunho
from dominio.mercado import carregar_catalogo, ler_linhas

PRODUTOS_DO_CATALOGO = carregar_catalogo()["produtos"]


@pytest.fixture(scope="module")
def linhas():
    return list(ler_linhas())


def _linhas_do_produto(produto: dict, linhas: list[dict]) -> list[dict]:
    chave = (produto["id_produto"], produto["nivel"])
    return [linha for linha in linhas if (linha["id_produto"], linha["nivel"]) == chave]


@pytest.mark.parametrize("produto", PRODUTOS_DO_CATALOGO, ids=lambda p: p["nome"])
def test_id_existe_na_base_com_o_nome_declarado(produto, linhas):
    # Pega id trocado: o 4744 também é "preço recebido", mas é SOJA, não MILHO.
    do_produto = _linhas_do_produto(produto, linhas)
    assert do_produto, (
        f"id {produto['id_produto']} com nível '{produto['nivel']}' não existe na base"
    )
    na_base = {f"{linha['produto']} / {linha['classificacao']}" for linha in do_produto}
    declarado = f"{produto['produto_conab']} / {produto['classificacao_conab']}"
    assert na_base == {declarado}, (
        f"id {produto['id_produto']} na base é {', '.join(sorted(na_base))}; "
        f"o catálogo diz {declarado}"
    )


@pytest.mark.parametrize("produto", PRODUTOS_DO_CATALOGO, ids=lambda p: p["nome"])
def test_valores_da_base_ficam_dentro_da_faixa(produto, linhas):
    validas = [
        linha
        for linha in _linhas_do_produto(produto, linhas)
        if linha["valor"] is not None
    ]
    assert validas, f"id {produto['id_produto']} só tem cotações vazias ou zeradas"
    minimo, maximo = produto["faixa"]
    fora = [
        f"{linha['uf']} {linha['periodo'][1]:02d}/{linha['periodo'][0]}: {linha['valor']}"
        for linha in validas
        if not minimo <= linha["valor"] <= maximo
    ]
    assert not fora, (
        f"{len(fora)} cotações fora da faixa {produto['faixa']} serão descartadas: "
        + "; ".join(fora[:10])
    )


# Erros de preenchimento: parte de um catálogo mínimo válido e quebra um campo.
CATALOGO_MINIMO = """\
fonte: CONAB
produtos:
"""
PRODUTO_MINIMO = """\
  - nome: leite
    descricao: Leite de vaca in natura
    id_produto: "6542"
    produto_conab: LEITE DE VACA
    classificacao_conab: IN NATURA
    nivel: PREÇO RECEBIDO P/ PRODUTOR
    unidade: R$/L
    sem_preco_no_mes: omite
    faixa: [0.5, 20.0]
    fonte_faixa: PENDENTE
"""


def _escrever(tmp_path, texto: str):
    arquivo = tmp_path / "mercado.yaml"
    arquivo.write_text(texto, encoding="utf-8")
    return arquivo


def test_catalogo_minimo_e_valido(tmp_path):
    catalogo = carregar_catalogo(_escrever(tmp_path, CATALOGO_MINIMO + PRODUTO_MINIMO))
    assert [produto["nome"] for produto in catalogo["produtos"]] == ["leite"]


@pytest.mark.parametrize(
    ("trecho", "troca", "mensagem"),
    [
        ("unidade: R$/L", "unidade: PREENCHER", "falta preencher 'unidade'"),
        ('id_produto: "6542"', "id_produto: 6542", "id_produto deve ser só dígitos"),
        ("sem_preco_no_mes: omite", "sem_preco_no_mes: talvez", "sem_preco_no_mes"),
        ("faixa: [0.5, 20.0]", "faixa: [20.0, 0.5]", "faixa deve ser"),
    ],
    ids=[
        "campo_a_preencher",
        "id_sem_aspas",
        "regra_do_mes_invalida",
        "faixa_invertida",
    ],
)
def test_produto_mal_preenchido_da_erro_claro(tmp_path, trecho, troca, mensagem):
    texto = CATALOGO_MINIMO + PRODUTO_MINIMO.replace(trecho, troca)
    with pytest.raises(ValueError, match=mensagem):
        carregar_catalogo(_escrever(tmp_path, texto))


def test_produto_repetido_da_erro_claro(tmp_path):
    texto = CATALOGO_MINIMO + PRODUTO_MINIMO + PRODUTO_MINIMO
    with pytest.raises(ValueError, match="repetido"):
        carregar_catalogo(_escrever(tmp_path, texto))


# Script de rascunho (dados/rascunho_catalogo.py).
def test_rascunho_traz_o_produto_da_base_e_campos_a_preencher(linhas):
    texto = rascunho("6542", linhas)
    assert 'id_produto: "6542"' in texto
    assert 'produto_conab: "LEITE DE VACA"' in texto
    assert 'nivel: "PREÇO RECEBIDO P/ PRODUTOR"' in texto
    assert "unidade: PREENCHER" in texto
    assert rascunho("produto que não existe", linhas) == ""


def test_rascunho_so_entra_no_catalogo_depois_de_preenchido(tmp_path, linhas):
    texto = rascunho("6542", linhas)
    with pytest.raises(ValueError, match="falta preencher"):
        carregar_catalogo(_escrever(tmp_path, CATALOGO_MINIMO + texto))
    preenchido = (
        texto.replace("nome: PREENCHER", "nome: leite")
        .replace("sem_preco_no_mes: PREENCHER", "sem_preco_no_mes: omite")
        .replace("faixa: [PREENCHER, PREENCHER]", "faixa: [0.5, 20.0]")
        .replace("PREENCHER", "preenchido")
    )
    catalogo = carregar_catalogo(_escrever(tmp_path, CATALOGO_MINIMO + preenchido))
    assert catalogo["produtos"][0]["produto_conab"] == "LEITE DE VACA"
