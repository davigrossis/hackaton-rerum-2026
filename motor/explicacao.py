"""Módulo de explicação: responde 'como?' e 'por quê?' a partir do traço de inferência."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from motor.inferencia import PremissaAvaliada, Resultado
from motor.memoria import Origem
from motor.regras import Base, Premissa, Regra


@dataclass(frozen=True)
class NoComo:
    """Nó da árvore de derivação explicativa para uma conclusão."""

    fato: str
    valor: Any
    cf: float
    origem: Origem
    regra: Regra | None = None
    premissas: tuple[PremissaAvaliada, ...] = ()
    filhos: tuple[NoComo, ...] = ()


@dataclass(frozen=True)
class MotivoPergunta:
    """Explica a relevância de uma pergunta para as regras da base."""

    regra: Regra
    premissa: Premissa
    esperando: bool  # True se só falta este dado para destravar o disparo


def como(resultado: Resultado, fato: str, valor: Any = None) -> list[NoComo]:
    """Explica como uma conclusão foi obtida, descendo pelas premissas e fatos antecedentes.

    A ser implementado na issue #9.
    """
    raise NotImplementedError("como será implementado na issue #9")


def por_que(
    base: Base, variavel: str, resultado: Resultado | None = None
) -> list[MotivoPergunta]:
    """Explica por que uma pergunta está sendo feita ao usuário (quais regras dependem dela).

    A ser implementado na issue #9.
    """
    raise NotImplementedError("por_que será implementado na issue #9")
