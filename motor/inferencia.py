"""Encadeamento progressivo: casa regras com fatos, resolve conflito e dispara."""

from __future__ import annotations

import operator
from dataclasses import dataclass
from typing import Any

from motor.memoria import Fato, Memoria
from motor.regras import CAMADAS, Base, Pergunta, Premissa, Regra

LIMIAR_CF = 0.2

# O "!=" fica de fora: com vários valores, ele exige que nenhum seja igual (D6).
_COMPARACOES = {
    "==": operator.eq,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
    "in": lambda valor, alvo: valor in alvo,
}


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
    regra: Regra
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


def _conferir_entrada(base: Base, memoria: Memoria) -> None:
    """Só as regras concluem (D8): a memória de entrada não pode trazer conclusões."""
    nomes_conclusao = {n for n, v in base.variaveis.items() if v.grupo == "conclusoes"}
    trazidas = sorted({f.nome for f in memoria.fatos()} & nomes_conclusao)
    if trazidas:
        raise ValueError(
            "A memória de entrada não pode trazer conclusões; só as regras concluem "
            f"(D8): {trazidas}"
        )


def _chave_conflito(regra: Regra) -> tuple[int, int, int]:
    """Maior prioridade, depois mais condições, depois a primeira no arquivo."""
    return (-regra.prioridade, -len(regra.se), regra.ordem)


def _conjunto_de_conflito(
    regras: list[Regra], memoria: Memoria, encerradas: set[str]
) -> list[tuple[Regra, list[PremissaAvaliada]]]:
    """Regras na disputa com todas as premissas verdadeiras, na ordem da resolução."""
    conjunto = []
    for regra in regras:
        if regra.id in encerradas:
            continue
        premissas = avaliar_premissas(regra, memoria)
        if all(p.verdadeira for p in premissas):
            conjunto.append((regra, premissas))
    return sorted(conjunto, key=lambda par: _chave_conflito(par[0]))


def _bloqueios(
    base: Base, vencedora: Regra, demais: list[Regra]
) -> tuple[Bloqueio, ...]:
    """Fato único: as regras do conjunto que concluiriam outro valor ficam bloqueadas.

    Basta olhar o conjunto atual: quem conclui um fato está na camada dele (D4), e
    dentro da camada nenhuma regra entra na disputa depois do primeiro disparo.
    """
    if not base.variaveis[vencedora.fato].unico:
        return ()
    return tuple(
        Bloqueio(
            regra=regra.id,
            fato=regra.fato,
            valor_pretendido=regra.valor,
            valor_existente=vencedora.valor,
            motivo=(
                f"'{regra.fato}' só admite um valor, e a {vencedora.id} "
                f"já concluiu '{vencedora.valor}'"
            ),
        )
        for regra in demais
        if regra.fato == vencedora.fato and regra.valor != vencedora.valor
    )


def inferir(base: Base, memoria: Memoria) -> Resultado:
    """Executa o encadeamento progressivo, camada por camada, até o ponto fixo.

    Em cada camada (D3), repete casar -> resolver o conflito -> disparar até o conjunto
    de conflito ficar vazio; cada regra dispara no máximo uma vez, e em fato único a
    vencedora bloqueia as que concluiriam outro valor. Não altera a memória recebida:
    trabalha numa cópia, devolvida no Resultado junto com o traço.
    """
    _conferir_entrada(base, memoria)
    memoria = memoria.copia()
    traco: list[Ciclo] = []
    encerradas: set[str] = set()  # dispararam ou foram bloqueadas: saem da disputa
    for camada in CAMADAS:
        regras = [r for r in base.regras if r.camada == camada]
        while True:
            conjunto = _conjunto_de_conflito(regras, memoria, encerradas)
            if not conjunto:
                break  # camada esgotada: a próxima já lê CFs definitivos
            regra, premissas = conjunto[0]
            cf_premissas = min(p.cf for p in premissas)
            cf_conclusao = round(regra.cf * cf_premissas, 4)
            fato = memoria.adicionar(
                regra.fato,
                regra.valor,
                cf=cf_conclusao,
                origem="regra",
                detalhe=regra.id,
            )
            bloqueadas = _bloqueios(base, regra, [r for r, _ in conjunto[1:]])
            encerradas.add(regra.id)
            encerradas.update(b.regra for b in bloqueadas)
            traco.append(
                Ciclo(
                    numero=len(traco) + 1,
                    camada=camada,
                    conjunto_conflito=tuple(r.id for r, _ in conjunto),
                    escolhida=regra.id,
                    regra=regra,
                    premissas=tuple(premissas),
                    fato=regra.fato,
                    valor=regra.valor,
                    cf_regra=regra.cf,
                    cf_premissas=cf_premissas,
                    cf_conclusao=cf_conclusao,
                    cf_fato=fato.cf,
                    bloqueadas=bloqueadas,
                )
            )
    return Resultado(memoria=memoria, traco=tuple(traco), versao_base=base.versao)


def _valores_validos(memoria: Memoria, nome: str) -> list[Fato]:
    """Valores do fato com CF >= LIMIAR_CF; abaixo do limite, o valor conta como ausente."""
    return [f for f in memoria.valores(nome) if f.cf >= LIMIAR_CF]


def _valor_lido(fatos: list[Fato]) -> Any:
    """Valor mostrado no traço: o valor, uma tupla se houver vários, None se nenhum."""
    if len(fatos) == 1:
        return fatos[0].valor
    return tuple(f.valor for f in fatos) or None


def _avaliar(premissa: Premissa, memoria: Memoria) -> PremissaAvaliada:
    """Avalia uma premissa; fato ou referência ausente torna a premissa falsa (D6)."""
    fatos = _valores_validos(memoria, premissa.fato)
    alvo, cf_alvo = premissa.alvo, 1.0
    if isinstance(alvo, str) and alvo.startswith("$"):
        # $nome só aponta para variável única (D5): há no máximo um valor.
        referencia = _valores_validos(memoria, alvo[1:])
        alvo, cf_alvo = (
            (referencia[0].valor, referencia[0].cf) if referencia else (None, 0.0)
        )

    verdadeira, cf = False, 0.0
    if fatos and cf_alvo >= LIMIAR_CF:
        if premissa.operador == "!=":
            # Nenhum valor pode ser igual; vale o menor CF entre eles.
            verdadeira = all(f.valor != alvo for f in fatos)
            cf = min(f.cf for f in fatos)
        else:
            # Basta um valor satisfazer; vale o maior CF entre os que satisfazem.
            comparar = _COMPARACOES[premissa.operador]
            cfs = [f.cf for f in fatos if comparar(f.valor, alvo)]
            verdadeira = bool(cfs)
            cf = max(cfs, default=0.0)

    return PremissaAvaliada(
        premissa=premissa,
        valor_fato=_valor_lido(fatos),
        valor_alvo=alvo,
        cf=min(cf, cf_alvo) if verdadeira else 0.0,
        verdadeira=verdadeira,
    )


def avaliar_premissas(regra: Regra, memoria: Memoria) -> list[PremissaAvaliada]:
    """Avalia cada premissa da regra contra a memória, sem parar na primeira falsa.

    Assim o traço e o diálogo da #26 enxergam todas as premissas, inclusive as que faltam.
    """
    return [_avaliar(premissa, memoria) for premissa in regra.se]


def perguntas_pendentes(
    base: Base, memoria: Memoria, resultado: Resultado | None = None
) -> list[Pergunta]:
    """Retorna perguntas que ainda não foram respondidas na memória.

    v0 (issue #2): devolve perguntas cuja variável não está na memória, na ordem do arquivo.
    v1 (issue #26): com resultado, seleciona só as que destravam regras quase satisfeitas.
    """
    ausentes = [p for p in base.perguntas if not memoria.tem(p.id)]
    if resultado is None:
        return ausentes

    pendentes: list[Pergunta] = []
    for pergunta in ausentes:
        for regra in base.regras_que_usam(pergunta.id):
            avaliadas = avaliar_premissas(regra, resultado.memoria)
            faltantes = [
                avaliada
                for premissa, avaliada in zip(regra.se, avaliadas)
                if (
                    premissa.fato == pergunta.id
                    or premissa.alvo == f"${pergunta.id}"
                )
                and (
                    avaliada.valor_fato is None
                    if premissa.fato == pergunta.id
                    else avaliada.valor_alvo is None
                )
            ]
            outras = [
                avaliada
                for premissa, avaliada in zip(regra.se, avaliadas)
                if not (
                    premissa.fato == pergunta.id
                    or premissa.alvo == f"${pergunta.id}"
                )
            ]
            if faltantes and all(avaliada.verdadeira for avaliada in outras):
                pendentes.append(pergunta)
                break
    return pendentes
