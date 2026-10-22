"""Testes das explicações derivadas do traço do motor."""

from pathlib import Path

from motor.explicacao import como, por_que
from motor.inferencia import inferir
from motor.memoria import Memoria
from motor.regras import carregar_base
from tests.test_inferencia import (
    REGRAS_COM_EXCECAO,
    _base_com_regras,
    _memoria_da_fazenda,
)

RAIZ = Path(__file__).resolve().parent.parent
FIXTURE = RAIZ / "tests" / "fixtures" / "base_exemplo"


def test_como_mostra_cadeia_indicador_situacao_com_valores():
    base = carregar_base(FIXTURE)
    resultado = inferir(base, _memoria_da_fazenda())

    [situacao] = como(resultado, "situacao_economica", "curto_prazo")

    assert situacao.regra.id == "R-SIT-03"
    assert [(p.valor_fato, p.valor_alvo) for p in situacao.premissas] == [
        (69600.0, 62000.0),
        (69600.0, 74000.0),
    ]
    assert {filho.fato for filho in situacao.filhos} == {
        "receita_total",
        "coe",
        "cot",
    }
    assert all(filho.origem.tipo == "usuario" for filho in situacao.filhos)


def test_como_mostra_formula_e_regra_bloqueada(tmp_path):
    base = _base_com_regras(tmp_path, REGRAS_COM_EXCECAO)
    memoria = _memoria_da_fazenda(receita_total=60000.0)
    memoria.adicionar(
        "receita_total", 60000.0, origem="calculado", detalhe="receita_total"
    )
    resultado = inferir(base, memoria)

    [situacao] = como(resultado, "situacao_economica", "prejuizo")

    assert situacao.regra.id == "R-SIT-02"
    assert situacao.conflitos == ("R-SIT-01",)
    assert situacao.bloqueios[0].regra == "R-SIT-01"
    receita = next(filho for filho in situacao.filhos if filho.fato == "receita_total")
    assert receita.origem.tipo == "calculado"
    assert receita.origem.detalhe == "receita_total"


def test_por_que_no_formulario_lista_regras_que_usam_variavel():
    base = carregar_base(FIXTURE)

    motivos = por_que(base, "preco_leite_fazenda")

    assert [
        (motivo.regra.id, motivo.premissa.fato, motivo.esperando) for motivo in motivos
    ] == [("R-IND-01", "preco_leite_fazenda", True)]


def test_por_que_com_resultado_marca_regra_que_esta_esperando_dado(tmp_path):
    base = _base_com_regras(
        tmp_path,
        """
versao: "0.1"
regras:
  - id: R-SIT-01
    descricao: Receita abaixo do COT
    camada: situacao
    prioridade: 50
    se: [[receita_total, "<", $cot]]
    entao: {fato: situacao_economica, valor: curto_prazo}
    cf: 1.0
    fonte: teste
""",
    )
    memoria = Memoria()
    memoria.adicionar("receita_total", 60000.0)
    resultado = inferir(base, memoria)

    motivos = por_que(base, "cot", resultado)

    assert len(motivos) == 1
    assert motivos[0].regra.id == "R-SIT-01"
    assert motivos[0].esperando is True
