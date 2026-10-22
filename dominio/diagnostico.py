"""Liga respostas, mercado, indicadores e motor num diagnóstico explicável."""

from __future__ import annotations

from typing import Any

from dominio.indicadores import calcular_indicadores
from dominio.mercado import fatos_mercado
from motor.inferencia import Resultado, inferir
from motor.memoria import Memoria
from motor.regras import Base, carregar_base

# Variação relativa máxima aceita em cada variável simulável (0.30 = ±30%).
LIMITES_SIMULACAO: dict[str, float] = {
    "preco_leite_fazenda": 0.30,
    "custo_concentrado": 0.30,
    "producao_litros": 0.20,
}

# Respostas que identificam a fazenda/período e não entram como indicadores.
_SO_IDENTIFICACAO = {"uf", "mes_referencia"}


def _periodo(texto: str) -> tuple[int, int]:
    mes, ano = texto.strip().split("/")
    return int(ano), int(mes)


def _executar(
    respostas: dict[str, Any],
    base: Base,
    externos: dict[str, float],
    estimados: frozenset[str],
) -> Resultado:
    """Monta uma memória nova, calcula os indicadores e roda o motor.

    Compartilhado por `diagnosticar` e `simular`: o cenário simulado passa
    exatamente pelo mesmo caminho do diagnóstico original.
    """
    memoria = Memoria()
    for nome, valor in respostas.items():
        if valor is not None and nome != "mes_referencia":
            memoria.adicionar(
                nome,
                valor,
                cf=0.7 if nome in estimados else 1.0,
                origem="usuario",
                detalhe="resposta do formulário",
            )

    for nome, valor in externos.items():
        memoria.adicionar(nome, valor, origem="externo", detalhe="CONAB")

    entradas = {
        nome: valor
        for nome, valor in respostas.items()
        if nome not in _SO_IDENTIFICACAO and isinstance(valor, (int, float))
    }
    indicadores = calcular_indicadores(entradas, externos, base)
    for nome, indicador in indicadores.items():
        memoria.adicionar(
            nome,
            indicador["valor"],
            origem="calculado",
            detalhe=indicador["detalhe"],
        )
    return inferir(base, memoria)


def diagnosticar(
    respostas: dict,
    estimados: frozenset[str] = frozenset(),
    base: Base | None = None,
) -> Resultado:
    """Orquestrador do diagnóstico completo da fazenda leiteira.

    respostas: {nome_variavel: valor}; campos ausentes ou None não viram fatos.
    estimados: variáveis marcadas com incerteza pelo usuário (entram com CF 0.7).
    base: base de conhecimento (padrão: carregada de conhecimento/).

    Ordem de execução:
    1. Memória de trabalho <- respostas (origem='usuario', CF 1.0 ou 0.7)
    2. Fatos de mercado da CONAB para a UF e o mês (origem='externo')
    3. Indicadores de dominio/indicadores.py (origem='calculado')
    4. Inferência no motor, devolvendo o Resultado com memória e traço

    A base e os fatos externos são carregados localmente, sem rede.
    """
    base = carregar_base() if base is None else base
    uf = str(respostas.get("uf", "")).strip()
    mes = respostas.get("mes_referencia")
    externos_brutos = fatos_mercado(uf, _periodo(str(mes)) if mes else None)
    externos = {nome: fato["valor"] for nome, fato in externos_brutos.items()}
    return _executar(respostas, base, externos, estimados)


def _validar_variacoes(variacoes: dict[str, float]) -> None:
    desconhecidas = set(variacoes) - set(LIMITES_SIMULACAO)
    if desconhecidas:
        raise ValueError(f"Variáveis não simuláveis: {sorted(desconhecidas)}")
    for nome, fracao in variacoes.items():
        if abs(fracao) > LIMITES_SIMULACAO[nome] + 1e-9:
            raise ValueError(f"{nome}: variação fora do limite ({fracao:+.0%})")


def _reconstruir_entradas(
    resultado: Resultado,
) -> tuple[dict[str, Any], dict[str, float], frozenset[str]]:
    """Recupera respostas, externos e estimados a partir da memória do parecer.

    Só lê a memória original; nada nela é alterado. Indicadores e conclusões
    ficam de fora porque são recalculados pelo próprio diagnóstico.
    """
    respostas: dict[str, Any] = {}
    externos: dict[str, float] = {}
    estimados: set[str] = set()
    for fato in resultado.memoria.fatos():
        tipo = fato.origens[0].tipo
        if tipo == "usuario":
            respostas[fato.nome] = fato.valor
            if fato.cf < 1.0:
                estimados.add(fato.nome)
        elif tipo == "externo":
            externos[fato.nome] = float(fato.valor)
    return respostas, externos, frozenset(estimados)


def simular(
    resultado_original: Resultado,
    variacoes: dict[str, float],
    base: Base | None = None,
) -> Resultado:
    """Recalcula um cenário sem alterar o resultado original.

    `variacoes` são frações relativas: 0.10 aumenta 10% e -0.20 reduz 20%.
    Aceita só as chaves de LIMITES_SIMULACAO, dentro dos limites declarados;
    caso contrário levanta ValueError. Variável não informada pelo usuário
    é ignorada (ausente não vira zero). Respostas estimadas mantêm o CF 0.7.
    """
    _validar_variacoes(variacoes)
    base = carregar_base() if base is None else base
    respostas, externos, estimados = _reconstruir_entradas(resultado_original)

    for nome, fracao in variacoes.items():
        if nome in respostas:
            respostas[nome] = float(respostas[nome]) * (1 + fracao)

    return _executar(respostas, base, externos, estimados)