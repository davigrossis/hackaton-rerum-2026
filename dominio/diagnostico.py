"""Liga respostas, mercado, indicadores e motor num diagnóstico explicável."""

from __future__ import annotations

from dominio.indicadores import calcular_indicadores
from dominio.mercado import Periodo, fatos_mercado
from motor.inferencia import Resultado, inferir
from motor.memoria import Memoria
from motor.regras import Base, carregar_base

CF_ESTIMADO = 0.7  # D7: resposta que o usuário marcou como estimada


def diagnosticar(
    respostas: dict,
    estimados: frozenset[str] = frozenset(),
    base: Base | None = None,
) -> Resultado:
    """Orquestrador do diagnóstico completo da fazenda leiteira.

    respostas: dicionário com {nome_variavel: valor}; campos ausentes ou None não viram fatos.
    estimados: conjunto de variáveis marcadas com incerteza pelo usuário (entram com CF=0.7).
    base: base de conhecimento (padrão: carregada de conhecimento/).

    Ordem de execução:
    1. Memória de trabalho <- respostas informadas (origem='usuario', CF 1.0 ou 0.7)
    2. Consulta fatos_mercado(uf, mes) da CONAB (origem='externo')
    3. Calcula indicadores em dominio/indicadores.py (origem='calculado')
    4. Dispara a inferência no motor (inferir) e retorna o Resultado com memória e traço.

    Chave de resposta que não é pergunta da base gera ValueError.
    """
    base = carregar_base() if base is None else base
    ids_perguntas = {p.id for p in base.perguntas}
    sobrando = sorted(set(respostas) - ids_perguntas)
    if sobrando:
        raise ValueError(f"Respostas sem pergunta na base: {sobrando}")

    estimados_invalidos = sorted(set(estimados) - ids_perguntas)
    if estimados_invalidos:
        raise ValueError(f"Estimados sem pergunta na base: {estimados_invalidos}")

    memoria = Memoria()
    cfs: dict[str, float] = {}  # CF de cada fato, herdado pelos calculados (D7)

    # 1. Respostas, na ordem do formulário
    for pergunta in base.perguntas:
        valor = respostas.get(pergunta.id)
        if valor is None:
            continue
        estimado = pergunta.id in estimados
        cfs[pergunta.id] = CF_ESTIMADO if estimado else 1.0
        memoria.adicionar(
            pergunta.id,
            valor,
            cf=cfs[pergunta.id],
            origem="usuario",
            detalhe="estimado" if estimado else "",
        )

    # 2. Mercado da UF no mês (CONAB)
    externos = _mercado(respostas)
    for nome, fato in externos.items():
        cfs[nome] = 1.0
        memoria.adicionar(
            nome,
            fato["valor"],
            origem="externo",
            detalhe=f"{fato['fonte']}, {respostas['uf']}, {fato['periodo']}",
        )

    # 3. Indicadores: o CF é o menor CF das entradas usadas (D7)
    numericas = {
        p.id: respostas[p.id]
        for p in base.perguntas
        if p.tipo in ("numero", "inteiro") and respostas.get(p.id) is not None
    }
    precos = {nome: fato["valor"] for nome, fato in externos.items()}
    for nome, indicador in calcular_indicadores(numericas, precos).items():
        cfs[nome] = min(cfs[e] for e in indicador["entradas"])
        memoria.adicionar(
            nome,
            indicador["valor"],
            cf=cfs[nome],
            origem="calculado",
            detalhe=indicador["detalhe"],
        )

    # 4. Motor
    return inferir(base, memoria)


def _mercado(respostas: dict) -> dict[str, dict]:
    """Sem UF ou sem mês, não há fatos de mercado (não se chuta o último mês)."""
    uf, mes = respostas.get("uf"), respostas.get("mes_referencia")
    if uf is None or mes is None:
        return {}
    return fatos_mercado(uf, _periodo(mes))


def _periodo(mes_referencia: str) -> Periodo:
    """'09/2026' -> (2026, 9), o formato de período do dominio/mercado.py."""
    mes, ano = mes_referencia.split("/")
    return int(ano), int(mes)
