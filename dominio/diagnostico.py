"""Liga respostas, mercado, indicadores e motor num diagnóstico explicável."""

from __future__ import annotations

from typing import Any

from dominio.indicadores import calcular_indicadores
from dominio.mercado import fatos_mercado
from motor.inferencia import Resultado, inferir
from motor.memoria import Memoria
from motor.regras import Base, carregar_base

CF_ESTIMADO = 0.7
LIMITES_SIMULACAO: dict[str, float] = {
    "preco_leite_fazenda": 0.30,
    "custo_concentrado": 0.30,
    "producao_litros": 0.20,
}
_SO_IDENTIFICACAO = {"uf", "mes_referencia"}


def _periodo(texto: str) -> tuple[int, int]:
    mes, ano = texto.strip().split("/")
    return int(ano), int(mes)


def _mercado(respostas: dict[str, Any]) -> dict[str, dict]:
    """Sem UF ou mês, não há fatos de mercado; não se chuta o último mês."""
    uf, mes = respostas.get("uf"), respostas.get("mes_referencia")
    if uf is None or mes is None:
        return {}
    return fatos_mercado(str(uf), _periodo(str(mes)))


def _executar(
    respostas: dict[str, Any],
    base: Base,
    externos: dict[str, dict],
    estimados: frozenset[str],
) -> Resultado:
    memoria = Memoria()
    cfs: dict[str, float] = {}
    ids_perguntas = {p.id for p in base.perguntas}
    for nome in respostas:
        if nome not in ids_perguntas:
            raise ValueError(
                f"Respostas sem pergunta na base: {sorted(set(respostas) - ids_perguntas)}"
            )
    for nome in estimados:
        if nome not in ids_perguntas:
            raise ValueError(
                f"Estimados sem pergunta na base: {sorted(set(estimados) - ids_perguntas)}"
            )

    for pergunta in base.perguntas:
        valor = respostas.get(pergunta.id)
        if valor is None:
            continue
        cf = CF_ESTIMADO if pergunta.id in estimados else 1.0
        cfs[pergunta.id] = cf
        memoria.adicionar(
            pergunta.id,
            valor,
            cf=cf,
            origem="usuario",
            detalhe="estimado" if cf < 1.0 else "",
        )

    for nome, fato in externos.items():
        cf = 1.0
        cfs[nome] = cf
        memoria.adicionar(
            nome,
            fato["valor"],
            cf=cf,
            origem="externo",
            detalhe=f"{fato['fonte']}, {respostas.get('uf', '')}, {fato['periodo']}",
        )

    numericas = {
        p.id: respostas[p.id]
        for p in base.perguntas
        if p.tipo in ("numero", "inteiro") and respostas.get(p.id) is not None
    }
    precos = {nome: fato["valor"] for nome, fato in externos.items()}
    for nome, indicador in calcular_indicadores(numericas, precos, base).items():
        cfs[nome] = min(cfs.get(entrada, 1.0) for entrada in indicador["entradas"])
        memoria.adicionar(
            nome,
            indicador["valor"],
            cf=cfs[nome],
            origem="calculado",
            detalhe=indicador["detalhe"],
        )
    return inferir(base, memoria)


def diagnosticar(
    respostas: dict,
    estimados: frozenset[str] = frozenset(),
    base: Base | None = None,
) -> Resultado:
    """Executa diagnóstico, mercado local, indicadores e inferência."""
    base = carregar_base() if base is None else base
    return _executar(respostas, base, _mercado(respostas), estimados)


def _validar_variacoes(variacoes: dict[str, float]) -> None:
    desconhecidas = set(variacoes) - set(LIMITES_SIMULACAO)
    if desconhecidas:
        raise ValueError(f"Variáveis não simuláveis: {sorted(desconhecidas)}")
    for nome, fracao in variacoes.items():
        if abs(fracao) > LIMITES_SIMULACAO[nome] + 1e-9:
            raise ValueError(f"{nome}: variação fora do limite ({fracao:+.0%})")


def _reconstruir_entradas(
    resultado: Resultado,
) -> tuple[dict[str, Any], dict[str, dict], frozenset[str]]:
    respostas: dict[str, Any] = {}
    externos: dict[str, dict] = {}
    estimados: set[str] = set()
    for fato in resultado.memoria.fatos():
        origem = fato.origens[0]
        if origem.tipo == "usuario":
            respostas[fato.nome] = fato.valor
            if fato.cf < 1.0:
                estimados.add(fato.nome)
        elif origem.tipo == "externo":
            externos[fato.nome] = {
                "valor": float(fato.valor),
                "fonte": origem.detalhe,
                "periodo": "",
            }
    return respostas, externos, frozenset(estimados)


def simular(
    resultado_original: Resultado,
    variacoes: dict[str, float],
    base: Base | None = None,
) -> Resultado:
    """Recalcula um cenário sem modificar o parecer original."""
    _validar_variacoes(variacoes)
    base = carregar_base() if base is None else base
    respostas, externos, estimados = _reconstruir_entradas(resultado_original)
    for nome, fracao in variacoes.items():
        if nome in respostas:
            respostas[nome] = float(respostas[nome]) * (1 + fracao)
    return _executar(respostas, base, externos, estimados)
