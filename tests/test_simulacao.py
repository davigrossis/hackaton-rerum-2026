"""Testes da simulação de cenários sem mutação do parecer original."""

from pathlib import Path

from dominio.diagnostico import diagnosticar, simular
from motor.regras import carregar_base

RAIZ = Path(__file__).resolve().parent.parent
CASO = RAIZ / "dados" / "casos" / "02_medio_prazo.yaml"


def _entradas() -> dict:
    import yaml

    return yaml.safe_load(CASO.read_text(encoding="utf-8"))["entradas"]


def test_simulacao_cruza_limiar_e_preserva_parecer_original():
    base = carregar_base()
    respostas = _entradas()
    original = diagnosticar(respostas, base=base)
    memoria_antes = original.memoria.fatos()
    traco_antes = original.traco

    simulado = simular(
        original,
        {"preco_leite_fazenda": 0.30},
        base=base,
    )

    assert original.memoria.fatos() == memoria_antes
    assert original.traco == traco_antes
    assert simulado is not original
    assert simulado.memoria.valor("situacao_economica").valor != (
        original.memoria.valor("situacao_economica").valor
    )
