"""Testes dos contratos da base de conhecimento, da memória de trabalho e das APIs do motor."""

import ast
from pathlib import Path

import pytest

from dominio.benchmark import fatos_benchmark
from dominio.mercado import fatos_mercado
from motor.inferencia import inferir, perguntas_pendentes
from motor.memoria import Memoria
from motor.regras import carregar_base

RAIZ = Path(__file__).resolve().parent.parent
PASTA_FIXTURE = RAIZ / "tests" / "fixtures" / "base_exemplo"
PASTA_CONHECIMENTO = RAIZ / "conhecimento"


def test_base_exemplo_carrega():
    base = carregar_base(PASTA_FIXTURE)
    assert base.versao == "0.1"
    assert len(base.regras) == 4
    assert len(base.perguntas) == 3
    assert len(base.secoes) == 2
    assert "preco_leite_uf" in base.variaveis
    assert "situacao_economica" in base.variaveis
    assert len(base.regras_pendentes) == 3
    usadas = [r.id for r in base.regras_que_usam("preco_leite_fazenda")]
    assert usadas == ["R-IND-01"]


def test_base_real_carrega():
    base = carregar_base(PASTA_CONHECIMENTO)
    assert base.versao == "1.1"
    assert len(base.regras) == 31
    assert len(base.perguntas) == 22
    assert len(base.secoes) == 6
    assert "preco_leite_uf" in base.variaveis
    assert "receita_total" in base.variaveis
    assert "situacao_economica" in base.variaveis


def test_toda_pergunta_tem_ajuda_e_faixa_nas_numericas():
    base = carregar_base(PASTA_CONHECIMENTO)
    for p in base.perguntas:
        assert p.ajuda and p.ajuda.strip(), f"Pergunta '{p.id}' sem ajuda"
        if p.tipo in ("numero", "inteiro"):
            assert p.faixa is not None, (
                f"Pergunta numérica '{p.id}' sem faixa declarada"
            )
            assert p.faixa[0] < p.faixa[1], f"Pergunta '{p.id}' com faixa inválida"


def test_todas_calculadas_tem_entradas_validas():
    base = carregar_base(PASTA_CONHECIMENTO)
    calculadas = [v for v in base.variaveis.values() if v.grupo == "calculadas"]
    assert len(calculadas) == 21
    for c in calculadas:
        assert c.formula and c.formula.strip()
        assert c.entradas, f"Calculada '{c.nome}' sem entradas"
        assert set(c.entradas).isdisjoint(set(c.opcionais)), (
            f"Calculada '{c.nome}' com sobreposição entre entradas e opcionais"
        )
        for entrada in c.entradas:
            assert entrada in base.variaveis, (
                f"Entrada '{entrada}' de '{c.nome}' não existe"
            )
            assert base.variaveis[entrada].grupo != "conclusoes"
        for opt in c.opcionais:
            assert opt in base.variaveis, f"Opcional '{opt}' de '{c.nome}' não existe"
            assert base.variaveis[opt].grupo != "conclusoes"

    assert base.variaveis["receita_total"].opcionais == ("outras_receitas",)
    assert base.variaveis["custo_alimentar"].opcionais == ("custo_mineral",)
    assert base.variaveis["coe"].opcionais == (
        "custo_mineral",
        "custo_sanidade_reproducao",
        "custo_energia_combustivel",
        "custo_outros",
    )


def test_externas_batem_com_fatos_mercado():
    base = carregar_base(PASTA_CONHECIMENTO)
    externas = {nome: v for nome, v in base.variaveis.items() if v.grupo == "externas"}
    fatos = {**fatos_mercado("MG"), **fatos_benchmark("MG", 2026)}
    assert set(externas.keys()) == set(fatos.keys())
    for nome, fato in fatos.items():
        assert externas[nome].unidade == fato["unidade"]


def _escrever_base(
    tmp_path: Path, perguntas_txt: str, variaveis_txt: str, regras_txt: str
) -> Path:
    pasta = tmp_path / "base"
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "perguntas.yaml").write_text(perguntas_txt, encoding="utf-8")
    (pasta / "variaveis.yaml").write_text(variaveis_txt, encoding="utf-8")
    (pasta / "regras.yaml").write_text(regras_txt, encoding="utf-8")
    return pasta


BASE_VALIDA_TXT = {
    "perguntas": """
versao: "0.1"
secoes:
  - {id: sec1, titulo: Seção 1}
perguntas:
  - id: p_num
    secao: sec1
    texto: Pergunta numérica?
    tipo: numero
    unidade: L
    faixa: [0, 100]
    obrigatoria: true
  - id: p_cat
    secao: sec1
    texto: Pergunta escolha?
    tipo: escolha
    opcoes: [opcao_a, opcao_b]
    obrigatoria: true
""",
    "variaveis": """
versao: "0.1"
calculadas:
  - nome: v_calc
    descricao: Calculada
    tipo: numero
    unidade: L
    formula: p_num * 2
    entradas: [p_num]
externas:
  - nome: v_ext
    descricao: Externa
    tipo: numero
    unidade: L
conclusoes:
  - nome: c_ind
    camada: indicador
    tipo: categoria
    unico: true
    valores: [bom, ruim]
  - nome: c_sit
    camada: situacao
    tipo: categoria
    unico: true
    valores: [ok, alerta]
  - nome: c_multi
    camada: causa
    tipo: categoria
    unico: false
    valores: [c1, c2]
""",
    "regras": """
versao: "0.1"
regras:
  - id: R-IND-01
    descricao: Indicador
    camada: indicador
    prioridade: 10
    se:
      - [p_num, ">", 50]
    entao:
      fato: c_ind
      valor: bom
    cf: 1.0
    fonte: Oficial
  - id: R-SIT-01
    descricao: Situação
    camada: situacao
    prioridade: 10
    se:
      - [c_ind, "==", bom]
    entao:
      fato: c_sit
      valor: ok
    cf: 0.9
    fonte: Oficial
""",
}


@pytest.mark.parametrize(
    ("arquivo", "trecho_original", "trecho_trocado", "match_erro"),
    [
        ("perguntas", "id: p_num", "id: p-num", "snake_case"),
        (
            "perguntas",
            "secao: sec1",
            "secao: sec_fantasma",
            "secao 'sec_fantasma' não declarada",
        ),
        (
            "perguntas",
            "tipo: numero",
            "tipo: desconhecido",
            "tipo 'desconhecido' inválido",
        ),
        ("perguntas", "unidade: L", "unidade: ''", "tipo 'numero' exige 'unidade'"),
        ("perguntas", "faixa: [0, 100]", "faixa: [100, 0]", "mín < máx"),
        (
            "perguntas",
            "opcoes: [opcao_a, opcao_b]",
            "opcoes: []",
            "tipo 'escolha' exige 'opcoes'",
        ),
        (
            "variaveis",
            "entradas: [p_num]",
            "entradas: [nao_existe]",
            "entrada 'nao_existe' não declarada",
        ),
        (
            "variaveis",
            "entradas: [p_num]",
            "entradas: [p_num]\n    opcionais: [fantasma]",
            "opcional 'fantasma' não declarada",
        ),
        (
            "variaveis",
            "entradas: [p_num]",
            "entradas: [p_num]\n    opcionais: [p_num]",
            "não pode estar em 'entradas' e 'opcionais' simultaneamente",
        ),
        (
            "variaveis",
            "entradas: [p_num]",
            "entradas: [c_ind]",
            "entrada 'c_ind' não pode ser do grupo 'conclusoes'",
        ),
        (
            "variaveis",
            "entradas: [p_num]",
            "entradas: [p_num]\n    opcionais: [c_ind]",
            "opcional 'c_ind' não pode ser do grupo 'conclusoes'",
        ),
        (
            "variaveis",
            "entradas: [p_num]",
            "entradas: [v_calc]",
            "ciclo detectado nas variáveis calculadas: v_calc -> v_calc",
        ),
        (
            "variaveis",
            "unico: true",
            "unico: talvez",
            "campo 'unico' obrigatório e deve ser booleano",
        ),
        (
            "variaveis",
            "valores: [bom, ruim]",
            "valores: []",
            "tipo 'categoria' exige 'valores'",
        ),
        ("regras", "id: R-IND-01", "id: R-SIT-01", "id deve começar com 'R-IND-'"),
        ("regras", "cf: 1.0", "cf: 1.5", "entre 0.0 e 1.0"),
        (
            "regras",
            "prioridade: 10",
            "prioridade: alta",
            "campo 'prioridade' deve ser um número inteiro",
        ),
        ("regras", "fonte: Oficial", "fonte: ''", "campo 'fonte' obrigatório"),
        (
            "regras",
            "fato: c_ind",
            "fato: p_num",
            "deve ser uma variável de 'conclusoes'",
        ),
        ("regras", "valor: bom", "valor: excelente", "não permitido"),
        (
            "regras",
            "camada: indicador",
            "camada: recomendacao",
            "id deve começar com 'R-REC-'",
        ),
        (
            "regras",
            '- [c_ind, "==", bom]',
            '- [c_sit, "==", ok]',
            "não pode ter premissa que lê fato da camada 'situacao'",
        ),
        (
            "regras",
            '- [c_ind, "==", bom]',
            '- [c_ind, "==", $c_sit]',
            "não pode ter premissa que lê fato da camada 'situacao'",
        ),
        ("regras", '[p_num, ">", 50]', '[p_num, "=~", 50]', "operador '=~' inválido"),
        (
            "regras",
            '[p_num, ">", 50]',
            '[p_num, ">", $c_multi]',
            "a variável referenciada deve ser 'unico: true'",
        ),
        (
            "regras",
            '[p_num, ">", 50]',
            '[p_num, ">", $fantasma]',
            "variável referenciada 'fantasma' não existe",
        ),
        (
            "regras",
            '[p_num, ">", 50]',
            '[p_cat, ">", 50]',
            "operador '>' só é permitido em variáveis do tipo 'numero'",
        ),
    ],
    ids=[
        "nome_invalido",
        "secao_inexistente",
        "tipo_pergunta_invalido",
        "pergunta_numero_sem_unidade",
        "faixa_invertida",
        "escolha_sem_opcoes",
        "calculada_com_entrada_inexistente",
        "calculada_com_opcional_inexistente",
        "calculada_com_opcional_duplicado_em_entradas",
        "calculada_com_conclusao_em_entradas",
        "calculada_com_conclusao_em_opcionais",
        "calculada_com_ciclo",
        "conclusao_sem_unico_booleano",
        "categoria_sem_valores",
        "prefixo_id_incoerente_camada",
        "cf_fora_da_faixa",
        "prioridade_nao_inteira",
        "fonte_vazia",
        "conclusao_em_pergunta",
        "valor_concluido_invalido",
        "camada_regra_diferente_id",
        "premissa_le_camada_posterior",
        "referencia_le_camada_posterior",
        "operador_invalido",
        "referencia_a_variavel_multivalorada",
        "referencia_a_variavel_inexistente",
        "comparacao_numerica_em_categoria",
    ],
)
def test_base_mal_preenchida_da_erro_claro(
    tmp_path, arquivo, trecho_original, trecho_trocado, match_erro
):
    textos = dict(BASE_VALIDA_TXT)
    assert trecho_original in textos[arquivo], (
        f"Trecho original não encontrado em {arquivo}: {trecho_original}"
    )
    textos[arquivo] = textos[arquivo].replace(trecho_original, trecho_trocado, 1)
    pasta = _escrever_base(
        tmp_path, textos["perguntas"], textos["variaveis"], textos["regras"]
    )
    with pytest.raises(ValueError, match=match_erro):
        carregar_base(pasta)


def test_memoria_operacoes():
    mem = Memoria()
    assert mem.valores("fato_x") == []
    assert mem.valor("fato_x") is None
    assert not mem.tem("fato_x")

    with pytest.raises(ValueError, match="não vira fato nem zero"):
        mem.adicionar("preco", None)

    with pytest.raises(ValueError, match="CF deve estar entre 0.0 e 1.0"):
        mem.adicionar("preco", 10.0, cf=1.5)

    f1 = mem.adicionar(
        "causa", "preco_baixo", cf=0.7, origem="regra", detalhe="R-CAU-01"
    )
    assert f1.cf == 0.7
    assert len(f1.origens) == 1

    # Combinação de CF: 0.7 + 0.5 * (1 - 0.7) = 0.85
    f2 = mem.adicionar(
        "causa", "preco_baixo", cf=0.5, origem="regra", detalhe="R-CAU-02"
    )
    assert f2.cf == 0.85
    assert len(f2.origens) == 2
    assert [o.detalhe for o in f2.origens] == ["R-CAU-01", "R-CAU-02"]

    # Fato multivalorado (outro valor no mesmo nome)
    f3 = mem.adicionar(
        "causa", "custo_alto", cf=0.6, origem="regra", detalhe="R-CAU-03"
    )
    assert f3.valor == "custo_alto"
    assert len(mem.valores("causa")) == 2
    assert mem.tem("causa")
    assert mem.valor("causa").valor == "preco_baixo"

    # Ordem de inserção preservada em fatos()
    fatos = mem.fatos()
    assert len(fatos) == 2
    assert fatos[0].valor == "preco_baixo"
    assert fatos[1].valor == "custo_alto"

    # Cópia independente
    copia = mem.copia()
    copia.adicionar("causa", "outra_causa", cf=0.8)
    assert len(copia.valores("causa")) == 3
    assert len(mem.valores("causa")) == 2


def test_perguntas_pendentes_v0():
    base = carregar_base(PASTA_FIXTURE)
    mem = Memoria()
    pendentes = perguntas_pendentes(base, mem)
    assert [p.id for p in pendentes] == ["uf", "preco_leite_fazenda", "producao_litros"]

    mem.adicionar("uf", "MG")
    pendentes_depois = perguntas_pendentes(base, mem)
    assert [p.id for p in pendentes_depois] == [
        "preco_leite_fazenda",
        "producao_litros",
    ]


def test_perguntas_pendentes_destravam_regra_de_ccs():
    base = carregar_base()
    memoria = Memoria()
    resultado = inferir(base, memoria)

    pendentes = perguntas_pendentes(base, resultado.memoria, resultado)
    assert "ccs" in [p.id for p in pendentes]

    memoria.adicionar("ccs", 600.0)
    resultado_com_ccs = inferir(base, memoria)
    assert "ccs" not in [
        p.id
        for p in perguntas_pendentes(base, resultado_com_ccs.memoria, resultado_com_ccs)
    ]


def test_motor_nao_importa_dominio():
    motor_dir = RAIZ / "motor"
    for py_file in motor_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(
                        ("dominio", "interface", "streamlit")
                    ), f"{py_file.name} não pode importar {alias.name}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith(
                    ("dominio", "interface", "streamlit")
                ), f"{py_file.name} não pode importar de {node.module}"


def test_interface_so_usa_a_api_do_motor():
    # Critério da #10: a interface chega ao domínio só pelo diagnosticar e não lê YAML.
    proibidos = ("dominio.indicadores", "dominio.mercado", "dominio.benchmark", "yaml")
    for py_file in [RAIZ / "app.py", *(RAIZ / "interface").glob("*.py")]:
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                nomes = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                nomes = [node.module]
                nomes += [f"{node.module}.{alias.name}" for alias in node.names]
            else:
                continue
            for nome in nomes:
                assert not nome.startswith(proibidos), (
                    f"{py_file.name} não pode importar {nome}"
                )
