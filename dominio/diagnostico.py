"""Liga respostas, mercado, indicadores e motor num diagnóstico explicável."""

from __future__ import annotations

from motor.inferencia import Resultado
from motor.regras import Base


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

    A ser implementado na issue #10.
    """
    raise NotImplementedError("diagnosticar será implementado na issue #10")
