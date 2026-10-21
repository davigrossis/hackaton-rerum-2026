"""Rascunho de produto para o conhecimento/mercado.yaml, a partir da base da CONAB.

Uso, na raiz do projeto: python -m dados.rascunho_catalogo <id ou parte do nome>
Exemplo: python -m dados.rascunho_catalogo sorgo

Só imprime: quem decide e cola no YAML é uma pessoa. O arquivo não informa a
unidade, então unidade, faixa e os outros campos PREENCHER ficam para ela.
"""

import json
import sys
import unicodedata
from collections.abc import Iterable

from dominio.mercado import PREENCHER, ler_linhas


def _sem_acento(texto: str) -> str:
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c)).upper()


def _mes(periodo: tuple[int, int]) -> str:
    return f"{periodo[1]:02d}/{periodo[0]}"


def _cotacao(linha: dict) -> str:
    return f"{linha['valor']} ({linha['uf']} {_mes(linha['periodo'])})"


def _aspas(texto: str) -> str:
    # Aspas no padrão JSON também são YAML válido, mesmo com ":" ou "#" no nome.
    return json.dumps(texto, ensure_ascii=False)


def _encontrados(termo: str, linhas: Iterable[dict]) -> dict[tuple[str, str], list]:
    """Linhas da base que batem com o id ou o nome, agrupadas por (id, nível)."""
    procurado = _sem_acento(termo.strip())
    grupos: dict[tuple[str, str], list] = {}
    for linha in linhas:
        if procurado.isdigit():
            achou = linha["id_produto"] == procurado
        else:
            nome = _sem_acento(f"{linha['produto']} {linha['classificacao']}")
            achou = procurado in nome
        if achou:
            grupos.setdefault((linha["id_produto"], linha["nivel"]), []).append(linha)
    return grupos


def _entrada(id_produto: str, nivel: str, linhas: list[dict]) -> str:
    validas = [linha for linha in linhas if linha["valor"] is not None]
    cobertura = f"{len(validas)} cotações válidas, {len(linhas) - len(validas)} vazias"
    observado = "nenhuma cotação válida: não serve como fato"
    if validas:
        ufs = {linha["uf"] for linha in validas}
        meses = sorted({linha["periodo"] for linha in validas})
        menor = min(validas, key=lambda linha: linha["valor"])
        maior = max(validas, key=lambda linha: linha["valor"])
        cobertura += f", {len(ufs)} UFs, {len(meses)} meses"
        cobertura += f" ({_mes(meses[0])} a {_mes(meses[-1])})"
        observado = f"mín {_cotacao(menor)}, máx {_cotacao(maior)}"
    primeira = linhas[0]
    return "\n".join(
        [
            f"# id {id_produto}, {nivel}: {cobertura}",
            f"# observado: {observado}",
            f"  - nome: {PREENCHER} # vira o fato preco_<nome>_uf",
            f"    descricao: {PREENCHER}",
            f'    id_produto: "{id_produto}"',
            f"    produto_conab: {_aspas(primeira['produto'])}",
            f"    classificacao_conab: {_aspas(primeira['classificacao'])}",
            f"    nivel: {_aspas(nivel)}",
            f"    unidade: {PREENCHER} # o arquivo não informa (base.md, seção 6)",
            f"    sem_preco_no_mes: {PREENCHER} # omite ou usa_ultimo",
            f"    faixa: [{PREENCHER}, {PREENCHER}] # valor fora é descartado",
            f"    fonte_faixa: {PREENCHER} # VALIDADO ou PENDENTE",
        ]
    )


def rascunho(termo: str, linhas: Iterable[dict]) -> str:
    """Entradas de catálogo para os produtos da base que batem com `termo`."""
    grupos = _encontrados(termo, linhas)
    return "\n\n".join(
        _entrada(id_produto, nivel, grupo)
        for (id_produto, nivel), grupo in sorted(grupos.items())
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python -m dados.rascunho_catalogo <id ou parte do nome>")
    texto = rascunho(sys.argv[1], ler_linhas())
    if not texto:
        raise SystemExit(f"Nenhum produto da base bate com '{sys.argv[1]}'.")
    print(texto)
