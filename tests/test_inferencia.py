"""Testes do motor de inferência: premissas, ciclo por camada, conflito, fato único e CF."""

import shutil
from pathlib import Path

import pytest

from motor.inferencia import PremissaAvaliada, avaliar_premissas, inferir
from motor.memoria import Memoria
from motor.regras import Base, Premissa, Regra, carregar_base

RAIZ = Path(__file__).resolve().parent.parent
PASTA_FIXTURE = RAIZ / "tests" / "fixtures" / "base_exemplo"

# Fazenda de exemplo do guia (docs/sistema-especialista.md, seção 8).
FAZENDA = {
    "uf": "MG",
    "preco_leite_fazenda": 2.90,
    "producao_litros": 24000.0,
    "receita_total": 69600.0,
    "coe": 62000.0,
    "cot": 74000.0,
    "preco_leite_uf": 3.04,
}


def _regra(*premissas: list) -> Regra:
    """Regra mínima para testar premissas sem passar pelo YAML."""
    return Regra(
        id="R-CAU-99",
        descricao="Regra de teste",
        camada="causa",
        prioridade=50,
        se=tuple(Premissa(*p) for p in premissas),
        fato="causa",
        valor="preco_recebido_baixo",
        cf=1.0,
        fonte="teste",
        ordem=0,
    )


def _avaliar_uma(premissa: list, memoria: Memoria) -> PremissaAvaliada:
    (avaliada,) = avaliar_premissas(_regra(premissa), memoria)
    return avaliada


def _memoria_da_fazenda(cf_preco: float = 1.0, **trocas: float | str | None) -> Memoria:
    """Memória com a fazenda do guia; `trocas` muda um valor, e None tira o fato."""
    mem = Memoria()
    for nome, valor in (FAZENDA | trocas).items():
        if valor is not None:
            cf = cf_preco if nome == "preco_leite_fazenda" else 1.0
            mem.adicionar(nome, valor, cf=cf)
    return mem


def _base_com_regras(tmp_path: Path, regras_txt: str) -> Base:
    """Base de exemplo com outras regras: mesmas perguntas e variáveis da fixture."""
    for nome in ("perguntas.yaml", "variaveis.yaml"):
        shutil.copy(PASTA_FIXTURE / nome, tmp_path / nome)
    (tmp_path / "regras.yaml").write_text(regras_txt, encoding="utf-8")
    return carregar_base(tmp_path)


def test_premissa_sobre_fato_ausente_e_falsa():
    mem = Memoria()
    for premissa in (["preco_leite_fazenda", "<", 3.0], ["uf", "!=", "SP"]):
        avaliada = _avaliar_uma(premissa, mem)
        assert not avaliada.verdadeira, premissa
        assert avaliada.valor_fato is None
        assert avaliada.cf == 0.0


def test_premissa_com_referencia_usa_o_menor_cf():
    mem = Memoria()
    mem.adicionar("preco_leite_fazenda", 2.90, cf=0.7)
    premissa = ["preco_leite_fazenda", "<", "$preco_leite_uf"]

    sem_referencia = _avaliar_uma(premissa, mem)
    assert not sem_referencia.verdadeira
    assert sem_referencia.valor_fato == 2.90
    assert sem_referencia.valor_alvo is None

    mem.adicionar("preco_leite_uf", 3.04, origem="externo")
    avaliada = _avaliar_uma(premissa, mem)
    assert avaliada.verdadeira
    assert (avaliada.valor_fato, avaliada.valor_alvo) == (2.90, 3.04)
    assert avaliada.cf == 0.7  # min(0,7 do fato; 1,0 da referência)


def test_premissa_abaixo_do_limite_de_cf_conta_como_falsa():
    abaixo, no_limite = Memoria(), Memoria()
    abaixo.adicionar("uf", "MG", cf=0.19)
    no_limite.adicionar("uf", "MG", cf=0.2)
    premissa = ["uf", "==", "MG"]
    assert not _avaliar_uma(premissa, abaixo).verdadeira
    assert _avaliar_uma(premissa, no_limite).verdadeira


def test_fato_com_varios_valores():
    mem = Memoria()
    mem.adicionar("causa", "preco_recebido_baixo", cf=0.7, origem="regra")
    mem.adicionar("causa", "custo_alimentar_alto", cf=0.56, origem="regra")

    igual = _avaliar_uma(["causa", "==", "preco_recebido_baixo"], mem)
    assert igual.verdadeira
    assert igual.cf == 0.7
    assert igual.valor_fato == ("preco_recebido_baixo", "custo_alimentar_alto")

    assert not _avaliar_uma(["causa", "!=", "preco_recebido_baixo"], mem).verdadeira

    na_lista = _avaliar_uma(["causa", "in", ["custo_alimentar_alto"]], mem)
    assert na_lista.verdadeira
    assert na_lista.cf == 0.56

    diferente = _avaliar_uma(["causa", "!=", "outra_causa"], mem)
    assert diferente.verdadeira
    assert diferente.cf == 0.56  # o menor CF entre os valores


def test_avalia_todas_as_premissas_sem_parar_na_primeira_falsa():
    mem = Memoria()
    mem.adicionar("uf", "MG")
    regra = _regra(["preco_leite_fazenda", "<", 3.0], ["uf", "==", "MG"])
    assert [a.verdadeira for a in avaliar_premissas(regra, mem)] == [False, True]


def test_encadeia_as_quatro_camadas_com_os_numeros_do_guia():
    resultado = inferir(carregar_base(PASTA_FIXTURE), _memoria_da_fazenda())

    assert [c.escolhida for c in resultado.traco] == [
        "R-IND-01",
        "R-SIT-03",
        "R-CAU-01",
        "R-REC-01",
    ]
    assert [c.camada for c in resultado.traco] == [
        "indicador",
        "situacao",
        "causa",
        "recomendacao",
    ]
    # D3: a R-SIT-03 só entra na disputa depois que a camada indicador acaba.
    assert resultado.traco[0].conjunto_conflito == ("R-IND-01",)
    assert [c.cf_fato for c in resultado.traco] == [1.0, 1.0, 0.7, 0.56]

    situacao = resultado.traco[1]
    assert [
        (p.valor_fato, p.premissa.operador, p.valor_alvo) for p in situacao.premissas
    ] == [(69600.0, ">=", 62000.0), (69600.0, "<", 74000.0)]

    recomendacao = resultado.traco[-1]
    assert (recomendacao.cf_regra, recomendacao.cf_premissas) == (0.8, 0.7)
    assert recomendacao.cf_conclusao == 0.56  # 0,8 × 0,7
    assert resultado.memoria.valor("recomendacao").valor == "negociar_com_laticinio"


def test_fato_ausente_interrompe_so_a_sua_cadeia():
    mem = _memoria_da_fazenda(preco_leite_fazenda=None)
    resultado = inferir(carregar_base(PASTA_FIXTURE), mem)
    # Sem o preço da fazenda, a R-IND-01 e as que dependem dela não disparam.
    assert [c.escolhida for c in resultado.traco] == ["R-SIT-03"]
    assert not resultado.memoria.tem("causa")


def test_limite_de_cf_corta_a_recomendacao():
    mem = _memoria_da_fazenda(cf_preco=0.25)
    resultado = inferir(carregar_base(PASTA_FIXTURE), mem)
    assert [c.escolhida for c in resultado.traco] == [
        "R-IND-01",
        "R-SIT-03",
        "R-CAU-01",
    ]
    assert resultado.memoria.valor("preco_leite").cf == 0.25
    assert resultado.memoria.valor("causa").cf == 0.175  # 0,7 × 0,25: abaixo de 0,2
    assert not resultado.memoria.tem("recomendacao")


def test_mesma_entrada_mesmo_traco_e_entrada_intacta():
    base = carregar_base(PASTA_FIXTURE)
    entrada = _memoria_da_fazenda()
    antes = entrada.fatos()

    primeiro, segundo = inferir(base, entrada), inferir(base, entrada)

    assert primeiro.traco == segundo.traco
    assert primeiro.memoria.fatos() == segundo.memoria.fatos()
    assert entrada.fatos() == antes  # o motor trabalha numa cópia (#15)


REGRAS_EM_CONFLITO = """
versao: "0.1"
regras:
  - id: R-CAU-A
    descricao: Uma condição, prioridade 50
    camada: causa
    prioridade: 50
    se: [[uf, "==", MG]]
    entao: {fato: causa, valor: preco_recebido_baixo}
    cf: 1.0
    fonte: teste
  - id: R-CAU-B
    descricao: Uma condição, prioridade maior
    camada: causa
    prioridade: 60
    se: [[uf, "==", MG]]
    entao: {fato: causa, valor: preco_recebido_baixo}
    cf: 1.0
    fonte: teste
  - id: R-CAU-C
    descricao: Duas condições, prioridade 50
    camada: causa
    prioridade: 50
    se: [[uf, "==", MG], [preco_leite_fazenda, "<", $preco_leite_uf]]
    entao: {fato: causa, valor: preco_recebido_baixo}
    cf: 1.0
    fonte: teste
  - id: R-CAU-D
    descricao: Uma condição, prioridade 50, depois da A no arquivo
    camada: causa
    prioridade: 50
    se: [[uf, "==", MG]]
    entao: {fato: causa, valor: preco_recebido_baixo}
    cf: 1.0
    fonte: teste
"""


def test_conflito_prioridade_depois_condicoes_depois_ordem(tmp_path):
    base = _base_com_regras(tmp_path, REGRAS_EM_CONFLITO)
    resultado = inferir(base, _memoria_da_fazenda())
    ordem = ("R-CAU-B", "R-CAU-C", "R-CAU-A", "R-CAU-D")
    assert resultado.traco[0].conjunto_conflito == ordem
    assert tuple(c.escolhida for c in resultado.traco) == ordem


def test_base_sem_regras_devolve_traco_vazio(tmp_path):
    base = _base_com_regras(tmp_path, 'versao: "0.1"\nregras: []\n')
    assert inferir(base, _memoria_da_fazenda()).traco == ()


def test_memoria_de_entrada_com_conclusao_da_erro():
    mem = _memoria_da_fazenda()
    mem.adicionar("situacao_economica", "lucro")
    with pytest.raises(ValueError, match="situacao_economica"):
        inferir(carregar_base(PASTA_FIXTURE), mem)


REGRAS_COM_EXCECAO = """
versao: "0.1"
regras:
  - id: R-SIT-01
    descricao: Regra geral, receita abaixo do COT
    camada: situacao
    prioridade: 50
    se: [[receita_total, "<", $cot]]
    entao: {fato: situacao_economica, valor: curto_prazo}
    cf: 1.0
    fonte: teste
  - id: R-SIT-02
    descricao: Exceção, receita abaixo do COT e também do COE
    camada: situacao
    prioridade: 50
    se: [[receita_total, "<", $cot], [receita_total, "<", $coe]]
    entao: {fato: situacao_economica, valor: prejuizo}
    cf: 1.0
    fonte: teste
"""


def test_excecao_mais_especifica_vence_e_a_geral_fica_bloqueada(tmp_path):
    base = _base_com_regras(tmp_path, REGRAS_COM_EXCECAO)
    resultado = inferir(base, _memoria_da_fazenda(receita_total=60000.0))

    situacao = resultado.memoria.valores("situacao_economica")
    assert [f.valor for f in situacao] == ["prejuizo"]

    (ciclo,) = resultado.traco  # a regra geral nunca dispara
    assert ciclo.conjunto_conflito == ("R-SIT-02", "R-SIT-01")
    assert ciclo.escolhida == "R-SIT-02"
    (bloqueio,) = ciclo.bloqueadas
    assert (bloqueio.regra, bloqueio.valor_pretendido, bloqueio.valor_existente) == (
        "R-SIT-01",
        "curto_prazo",
        "prejuizo",
    )


REGRAS_COM_DUAS_CAUSAS = """
versao: "0.1"
regras:
  - id: R-IND-01
    descricao: Preço recebido abaixo do preço da UF
    camada: indicador
    prioridade: 50
    se: [[preco_leite_fazenda, "<", $preco_leite_uf]]
    entao: {fato: preco_leite, valor: abaixo_mercado}
    cf: 1.0
    fonte: teste
  - id: R-SIT-03
    descricao: Receita cobre o COE mas não o COT
    camada: situacao
    prioridade: 50
    se: [[receita_total, ">=", $coe], [receita_total, "<", $cot]]
    entao: {fato: situacao_economica, valor: curto_prazo}
    cf: 1.0
    fonte: teste
  - id: R-CAU-01
    descricao: Curto prazo com preço abaixo do mercado
    camada: causa
    prioridade: 50
    se:
      - [situacao_economica, "==", curto_prazo]
      - [preco_leite, "==", abaixo_mercado]
    entao: {fato: causa, valor: preco_recebido_baixo}
    cf: 0.7
    fonte: teste
  - id: R-REC-01
    descricao: Escrita antes da R-CAU-02 de propósito
    camada: recomendacao
    prioridade: 50
    se: [[causa, "==", preco_recebido_baixo]]
    entao: {fato: recomendacao, valor: negociar_com_laticinio}
    cf: 0.8
    fonte: teste
  - id: R-CAU-02
    descricao: Preço abaixo do mercado, por si só
    camada: causa
    prioridade: 50
    se: [[preco_leite, "==", abaixo_mercado]]
    entao: {fato: causa, valor: preco_recebido_baixo}
    cf: 0.5
    fonte: teste
"""


def test_mesma_conclusao_combina_cf_antes_da_recomendacao(tmp_path):
    base = _base_com_regras(tmp_path, REGRAS_COM_DUAS_CAUSAS)
    resultado = inferir(base, _memoria_da_fazenda())

    assert [c.escolhida for c in resultado.traco] == [
        "R-IND-01",
        "R-SIT-03",
        "R-CAU-01",
        "R-CAU-02",
        "R-REC-01",
    ]
    segunda_causa = resultado.traco[3]
    assert segunda_causa.cf_conclusao == 0.5
    assert segunda_causa.cf_fato == 0.85  # 0,7 + 0,5 × (1 − 0,7)
    # A recomendação lê o CF já combinado da causa (0,85), não o primeiro (0,7).
    assert resultado.memoria.valor("recomendacao").cf == 0.68  # 0,8 × 0,85
