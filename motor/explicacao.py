"""Módulo de explicação: responde 'como?' e 'por quê?' a partir do traço de inferência."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from motor.inferencia import (
    LIMIAR_CF,
    Bloqueio,
    Ciclo,
    PremissaAvaliada,
    Resultado,
    avaliar_premissas,
)
from motor.memoria import Fato, Memoria, Origem
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
    conflitos: tuple[str, ...] = ()
    bloqueios: tuple[Bloqueio, ...] = ()


@dataclass(frozen=True)
class MotivoPergunta:
    """Explica a relevância de uma pergunta para as regras da base."""

    regra: Regra
    premissa: Premissa
    esperando: bool  # True se só falta este dado para destravar o disparo


def como(resultado: Resultado, fato: str, valor: Any = None) -> list[NoComo]:
    """Explica como uma conclusão foi obtida, descendo pelas premissas e fatos antecedentes.

    Retorna um nó para cada valor solicitado. Os filhos são os fatos usados nas
    premissas, incluindo fatos calculados e referências ``$variavel``.
    """
    ciclos: dict[tuple[str, Any], Ciclo] = {
        (c.fato, c.valor): c for c in resultado.traco
    }
    fatos = [
        f
        for f in resultado.memoria.valores(fato)
        if f.cf >= LIMIAR_CF and (valor is None or f.valor == valor)
    ]
    return [
        _montar_no(resultado.memoria, ciclos, fato_memoria, set())
        for fato_memoria in fatos
    ]


def por_que(
    base: Base, variavel: str, resultado: Resultado | None = None
) -> list[MotivoPergunta]:
    """Explica por que uma pergunta está sendo feita ao usuário (quais regras dependem dela).

    Sem resultado, lista toda regra que menciona a variável. Com resultado,
    marca ``esperando`` somente quando essa premissa está ausente (ou abaixo
    do limiar de CF) e todas as demais da regra já são verdadeiras.
    """
    regras = base.regras_que_usam(variavel)
    if resultado is None:
        return [
            MotivoPergunta(regra=regra, premissa=premissa, esperando=True)
            for regra in regras
            for premissa in regra.se
            if _premissa_menciona(premissa, variavel)
        ]

    motivos: list[MotivoPergunta] = []
    for regra in regras:
        avaliadas = {
            id(premissa): avaliada
            for premissa, avaliada in zip(
                regra.se, avaliar_premissas(regra, resultado.memoria)
            )
        }
        for premissa in regra.se:
            if not _premissa_menciona(premissa, variavel):
                continue
            avaliada = avaliadas[id(premissa)]
            outras = [
                avaliada_out
                for outra, avaliada_out in zip(
                    regra.se, avaliar_premissas(regra, resultado.memoria)
                )
                if outra is not premissa
            ]
            faltando = (
                avaliada.valor_fato is None
                if premissa.fato == variavel
                else avaliada.valor_alvo is None
            )
            motivos.append(
                MotivoPergunta(
                    regra=regra,
                    premissa=premissa,
                    esperando=faltando and all(p.verdadeira for p in outras),
                )
            )
    return motivos


def _premissa_menciona(premissa: Premissa, variavel: str) -> bool:
    return premissa.fato == variavel or premissa.alvo == f"${variavel}"


def _origem(fato: Fato) -> Origem:
    return fato.origens[-1]


def _fatos_validos(memoria: Memoria, nome: str, valor: Any = None) -> list[Fato]:
    return [
        fato
        for fato in memoria.valores(nome)
        if fato.cf >= LIMIAR_CF and (valor is None or fato.valor == valor)
    ]


def _montar_no(
    memoria: Memoria,
    ciclos: dict[tuple[str, Any], Ciclo],
    fato_memoria: Fato,
    caminho: set[tuple[str, Any]],
) -> NoComo:
    chave = (fato_memoria.nome, fato_memoria.valor)
    if chave in caminho:
        return NoComo(
            fato=fato_memoria.nome,
            valor=fato_memoria.valor,
            cf=fato_memoria.cf,
            origem=_origem(fato_memoria),
        )

    ciclo = ciclos.get(chave)
    if ciclo is None:
        return NoComo(
            fato=fato_memoria.nome,
            valor=fato_memoria.valor,
            cf=fato_memoria.cf,
            origem=_origem(fato_memoria),
        )

    novos_caminho = caminho | {chave}
    filhos: list[NoComo] = []
    for avaliada in ciclo.premissas:
        valor_fato = (
            None if isinstance(avaliada.valor_fato, tuple) else avaliada.valor_fato
        )
        filhos.extend(
            _montar_no(memoria, ciclos, antecedente, novos_caminho)
            for antecedente in _fatos_validos(
                memoria, avaliada.premissa.fato, valor_fato
            )
        )
        if isinstance(
            avaliada.premissa.alvo, str
        ) and avaliada.premissa.alvo.startswith("$"):
            nome_alvo = avaliada.premissa.alvo[1:]
            valor_alvo = (
                None if isinstance(avaliada.valor_alvo, tuple) else avaliada.valor_alvo
            )
            filhos.extend(
                _montar_no(memoria, ciclos, antecedente, novos_caminho)
                for antecedente in _fatos_validos(memoria, nome_alvo, valor_alvo)
            )

    return NoComo(
        fato=fato_memoria.nome,
        valor=fato_memoria.valor,
        cf=fato_memoria.cf,
        origem=_origem(fato_memoria),
        regra=ciclo.regra,
        premissas=ciclo.premissas,
        filhos=tuple(filhos),
        conflitos=tuple(
            regra_id
            for regra_id in ciclo.conjunto_conflito
            if regra_id != ciclo.escolhida
        ),
        bloqueios=ciclo.bloqueadas,
    )
