"""Memória de trabalho: fatos da sessão atual, cada um com valor, CF e origem."""

from __future__ import annotations

from dataclasses import dataclass

TIPOS_ORIGEM = ("usuario", "calculado", "externo", "regra")


@dataclass(frozen=True)
class Origem:
    """Origem de uma derivação de fato."""

    tipo: str  # um de TIPOS_ORIGEM
    detalhe: (
        str  # id da regra | fórmula com valores | "CONAB, MG, 09/2026" | "estimado"
    )
    cf: float  # CF desta derivação, antes de combinar

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS_ORIGEM:
            raise ValueError(
                f"Origem inválida: {self.tipo}. Deve ser uma de {TIPOS_ORIGEM}"
            )
        if not (0.0 <= self.cf <= 1.0):
            raise ValueError(f"CF deve estar entre 0.0 e 1.0, recebido: {self.cf}")


@dataclass(frozen=True)
class Fato:
    """Fato na memória de trabalho."""

    nome: str
    valor: float | str | bool
    cf: float  # CF combinado de todas as origens
    origens: tuple[Origem, ...]  # histórico de origens que concluíram este valor


class Memoria:
    """Armazena os fatos da sessão atual (uma fazenda, um mês)."""

    def __init__(self) -> None:
        # nome -> list[Fato]
        self._por_nome: dict[str, list[Fato]] = {}
        # lista de fatos na ordem de inserção
        self._ordem: list[Fato] = []

    def adicionar(
        self,
        nome: str,
        valor: float | str | bool | None,
        cf: float = 1.0,
        origem: str = "usuario",
        detalhe: str = "",
    ) -> Fato:
        """Adiciona ou combina um fato na memória de trabalho.

        Campo vazio (valor is None) não vira fato nem zero e levanta ValueError.
        Se o fato já existe com o mesmo valor, combina o CF: cf1 + cf2 * (1 - cf1).
        """
        if valor is None:
            raise ValueError(
                f"Campo vazio não vira fato nem zero: fato '{nome}' recebeu None"
            )

        if not (0.0 <= cf <= 1.0):
            raise ValueError(f"CF deve estar entre 0.0 e 1.0, recebido: {cf}")

        nova_origem = Origem(tipo=origem, detalhe=detalhe, cf=cf)
        fatos_existentes = self._por_nome.setdefault(nome, [])

        for i, fato_existente in enumerate(fatos_existentes):
            if fato_existente.valor == valor:
                # Mesmo nome e mesmo valor -> combina CF: CF1 + CF2 * (1 - CF1)
                cf_combinado = min(
                    1.0, fato_existente.cf + cf * (1.0 - fato_existente.cf)
                )
                cf_combinado = round(cf_combinado, 4)
                fato_atualizado = Fato(
                    nome=nome,
                    valor=valor,
                    cf=cf_combinado,
                    origens=fato_existente.origens + (nova_origem,),
                )
                fatos_existentes[i] = fato_atualizado
                # Atualiza na lista de ordem
                idx_ordem = self._ordem.index(fato_existente)
                self._ordem[idx_ordem] = fato_atualizado
                return fato_atualizado

        novo_fato = Fato(
            nome=nome,
            valor=valor,
            cf=round(cf, 4),
            origens=(nova_origem,),
        )
        fatos_existentes.append(novo_fato)
        self._ordem.append(novo_fato)
        return novo_fato

    def valores(self, nome: str) -> list[Fato]:
        """Retorna todos os fatos para o nome dado (lista vazia se desconhecido)."""
        return list(self._por_nome.get(nome, []))

    def valor(self, nome: str) -> Fato | None:
        """Retorna o fato para variável única (ou o primeiro valor cadastrado)."""
        fatos = self._por_nome.get(nome)
        return fatos[0] if fatos else None

    def tem(self, nome: str) -> bool:
        """Verifica se o fato existe na memória."""
        return bool(self._por_nome.get(nome))

    def fatos(self) -> list[Fato]:
        """Retorna todos os fatos na ordem em que foram inseridos."""
        return list(self._ordem)

    def copia(self) -> Memoria:
        """Cria uma cópia independente da memória."""
        clone = Memoria()
        for f in self._ordem:
            clone._por_nome.setdefault(f.nome, []).append(f)
            clone._ordem.append(f)
        return clone
