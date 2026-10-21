"""Encadeamento progressivo: casa regras com fatos, resolve conflito e dispara."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from motor.memoria import Memoria
from motor.regras import Base, Pergunta, Premissa, Regra

LIMIAR_CF = 0.2


@dataclass(frozen=True)
class PremissaAvaliada:
    """Resultado da avaliação de uma premissa contra a memória de trabalho."""

    premissa: Premissa
    valor_fato: Any
    valor_alvo: Any
    cf: float
    verdadeira: bool


@dataclass(frozen=True)
class Bloqueio:
    """Registro de regra que não pôde concluir por colisão em fato único."""

    regra: str
    fato: str
    valor_pretendido: Any
    valor_existente: Any
    motivo: str


@dataclass(frozen=True)
class Ciclo:
    """Registro de um ciclo de inferência no traço."""

    numero: int
    camada: str
    conjunto_conflito: tuple[str, ...]  # ids na ordem da resolução
    escolhida: str
    premissas: tuple[PremissaAvaliada, ...]
    fato: str
    valor: Any
    cf_regra: float
    cf_premissas: float
    cf_conclusao: float  # cf_regra * cf_premissas
    cf_fato: float  # CF combinado com fatos anteriores
    bloqueadas: tuple[Bloqueio, ...]


@dataclass(frozen=True)
class Resultado:
    """Resultado da inferência com a memória final e o traço auditável."""

    memoria: Memoria
    traco: tuple[Ciclo, ...]
    versao_base: str


def inferir(base: Base, memoria: Memoria) -> Resultado:
    """Executa o ciclo de inferência progressiva até atingir o ponto fixo.

    Nota: Não altera a memória de trabalho recebida (opera em uma cópia).
    A ser implementado na issue #5.
    """
    raise NotImplementedError("inferir será implementado na issue #5")


def avaliar_premissas(regra: Regra, memoria: Memoria) -> list[PremissaAvaliada]:
    """Avalia cada premissa da regra contra a memória.

    A ser implementado na issue #5.
    """
    raise NotImplementedError("avaliar_premissas será implementado na issue #5")


def perguntas_pendentes(
    base: Base, memoria: Memoria, resultado: Resultado | None = None
) -> list[Pergunta]:
    """Retorna perguntas que ainda não foram respondidas na memória.

    v0 (issue #2): devolve perguntas cuja variável não está na memória, na ordem do arquivo.
    v1 (issue #26): com resultado, seleciona só as que destravam regras quase satisfeitas.
    """
    return [p for p in base.perguntas if not memoria.tem(p.id)]
