"""Carrega e valida a base de conhecimento (conhecimento/*.yaml)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

RAIZ = Path(__file__).resolve().parent.parent
PASTA_CONHECIMENTO = RAIZ / "conhecimento"

CAMADAS = ("indicador", "situacao", "causa", "recomendacao")
OPERADORES = ("==", "!=", "<", "<=", ">", ">=", "in")
PREFIXOS_CAMADA = {
    "indicador": "R-IND-",
    "situacao": "R-SIT-",
    "causa": "R-CAU-",
    "recomendacao": "R-REC-",
}
TIPOS_VARIAVEL = ("numero", "categoria")
TIPOS_PERGUNTA = ("numero", "inteiro", "escolha", "mes")

PADRAO_IDENTIFICADOR = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class Premissa:
    """Premissa de uma regra de produção: [fato, operador, alvo]."""

    fato: str
    operador: str
    alvo: Any


@dataclass(frozen=True)
class Regra:
    """Regra de produção SE ... ENTÃO ..."""

    id: str
    descricao: str
    camada: str
    prioridade: int
    se: tuple[Premissa, ...]
    fato: str
    valor: Any
    cf: float
    fonte: str
    ordem: int  # posição no arquivo para desempate determinístico


@dataclass(frozen=True)
class Variavel:
    """Definição de uma variável do sistema."""

    nome: str
    grupo: str  # "perguntas" | "calculadas" | "externas" | "conclusoes"
    tipo: str  # "numero" | "categoria"
    unico: bool
    descricao: str
    unidade: str | None = None
    valores: tuple[Any, ...] | None = None
    camada: str | None = None
    formula: str | None = None
    entradas: tuple[str, ...] = ()
    opcionais: tuple[str, ...] = ()
    fonte: str | None = None


@dataclass(frozen=True)
class Pergunta:
    """Pergunta ao usuário cadastrada em perguntas.yaml."""

    id: str
    secao: str
    texto: str
    ajuda: str
    tipo: str
    unidade: str | None = None
    faixa: tuple[float, float] | None = None
    fonte_faixa: str | None = None
    opcoes: tuple[str, ...] | None = None
    obrigatoria: bool = True


@dataclass(frozen=True)
class Secao:
    """Seção do formulário."""

    id: str
    titulo: str


@dataclass(frozen=True)
class Base:
    """Base de conhecimento completa e validada."""

    versao: str
    regras: tuple[Regra, ...]
    perguntas: tuple[Pergunta, ...]
    secoes: tuple[Secao, ...]
    variaveis: dict[str, Variavel] = field(default_factory=dict)

    def regras_que_usam(self, variavel: str) -> list[Regra]:
        """Retorna regras que mencionam a variável em suas premissas."""
        alvo_ref = f"${variavel}"
        resultado = []
        for regra in self.regras:
            for p in regra.se:
                if p.fato == variavel or p.alvo == alvo_ref:
                    resultado.append(regra)
                    break
        return resultado

    @property
    def regras_pendentes(self) -> list[Regra]:
        """Retorna regras com fonte marcada como PENDENTE."""
        return [r for r in self.regras if r.fonte == "PENDENTE"]


def _validar_nome(nome: str, onde: str) -> None:
    if not isinstance(nome, str) or not PADRAO_IDENTIFICADOR.match(nome):
        raise ValueError(
            f"{onde}: nome '{nome}' inválido. Deve ser snake_case sem acento (^[a-z][a-z0-9_]*$)"
        )


def _detectar_ciclo_calculadas(calculadas: dict[str, Variavel]) -> None:
    """Verifica se há ciclos de dependência entre variáveis calculadas."""
    estado: dict[str, int] = {
        nome: 0 for nome in calculadas
    }  # 0=não visitado, 1=na pilha, 2=visitado
    caminho: list[str] = []

    def dfs(nome: str) -> None:
        estado[nome] = 1
        caminho.append(nome)
        v = calculadas[nome]
        for dep in v.entradas + v.opcionais:
            if dep in calculadas:
                if estado[dep] == 1:
                    idx = caminho.index(dep)
                    ciclo = " -> ".join(caminho[idx:] + [dep])
                    raise ValueError(
                        f"variaveis.yaml: ciclo detectado nas variáveis calculadas: {ciclo}"
                    )
                if estado[dep] == 0:
                    dfs(dep)
        caminho.pop()
        estado[nome] = 2

    for nome in calculadas:
        if estado[nome] == 0:
            dfs(nome)


def carregar_base(pasta: Path = PASTA_CONHECIMENTO) -> Base:
    """Carrega e valida a base de conhecimento a partir dos arquivos YAML."""
    pasta = Path(pasta)
    arq_perguntas = pasta / "perguntas.yaml"
    arq_variaveis = pasta / "variaveis.yaml"
    arq_regras = pasta / "regras.yaml"

    for arq in (arq_perguntas, arq_variaveis, arq_regras):
        if not arq.exists():
            raise ValueError(f"Arquivo obrigatório não encontrado: {arq.name}")

    dados_perguntas = yaml.safe_load(arq_perguntas.read_text(encoding="utf-8")) or {}
    dados_variaveis = yaml.safe_load(arq_variaveis.read_text(encoding="utf-8")) or {}
    dados_regras = yaml.safe_load(arq_regras.read_text(encoding="utf-8")) or {}

    # 1. Validação de estrutura básica e versões
    for nome_arq, dados in (
        ("perguntas.yaml", dados_perguntas),
        ("variaveis.yaml", dados_variaveis),
        ("regras.yaml", dados_regras),
    ):
        if (
            not isinstance(dados, dict)
            or "versao" not in dados
            or not str(dados["versao"]).strip()
        ):
            raise ValueError(f"{nome_arq}: campo 'versao' obrigatório e não vazio")

    versao = str(dados_regras["versao"])

    # Listas básicas
    secoes_raw = dados_perguntas.get("secoes", [])
    perguntas_raw = dados_perguntas.get("perguntas", [])
    calculadas_raw = dados_variaveis.get("calculadas", [])
    externas_raw = dados_variaveis.get("externas", [])
    conclusoes_raw = dados_variaveis.get("conclusoes", [])
    regras_raw = dados_regras.get("regras", [])

    for nome_campo, val, arq in (
        ("secoes", secoes_raw, "perguntas.yaml"),
        ("perguntas", perguntas_raw, "perguntas.yaml"),
        ("calculadas", calculadas_raw, "variaveis.yaml"),
        ("externas", externas_raw, "variaveis.yaml"),
        ("conclusoes", conclusoes_raw, "variaveis.yaml"),
        ("regras", regras_raw, "regras.yaml"),
    ):
        if not isinstance(val, list):
            raise ValueError(f"{arq}: campo '{nome_campo}' deve ser uma lista")  # noqa: TRY004

    # 2. Seções
    secoes_dict: dict[str, Secao] = {}
    for i, s in enumerate(secoes_raw):
        onde = f"perguntas.yaml, secao [{i}]"
        if not isinstance(s, dict) or not s.get("id") or not s.get("titulo"):
            raise ValueError(f"{onde}: precisa de 'id' e 'titulo'")
        sid = s["id"]
        _validar_nome(sid, onde)
        if sid in secoes_dict:
            raise ValueError(f"{onde}: secao '{sid}' repetida")
        secoes_dict[sid] = Secao(id=sid, titulo=str(s["titulo"]))

    # Dicionário geral de variáveis (perguntas + variaveis.yaml)
    todas_vars: dict[str, Variavel] = {}

    # 3. Perguntas
    perguntas_lista: list[Pergunta] = []
    for i, p in enumerate(perguntas_raw):
        onde = f"perguntas.yaml, pergunta '{p.get('id', i)}'"
        if not isinstance(p, dict):
            raise ValueError(f"{onde}: deve ser um dicionário")  # noqa: TRY004
        pid = p.get("id")
        if not pid:
            raise ValueError(f"{onde}: 'id' obrigatório")
        _validar_nome(pid, onde)
        if pid in todas_vars:
            raise ValueError(
                f"{onde}: id '{pid}' colide com outra pergunta ou variável"
            )

        secao = p.get("secao")
        if secao not in secoes_dict:
            raise ValueError(f"{onde}: secao '{secao}' não declarada em secoes")

        tipo = p.get("tipo")
        if tipo not in TIPOS_PERGUNTA:
            raise ValueError(
                f"{onde}: tipo '{tipo}' inválido. Deve ser um de {TIPOS_PERGUNTA}"
            )

        texto = p.get("texto")
        if not texto or not str(texto).strip():
            raise ValueError(f"{onde}: 'texto' obrigatório")

        ajuda = p.get("ajuda", "")
        obrigatoria = bool(p.get("obrigatoria", True))
        unidade = p.get("unidade")
        faixa = p.get("faixa")
        fonte_faixa = p.get("fonte_faixa")
        opcoes = p.get("opcoes")

        if tipo in ("numero", "inteiro") and (not unidade or not str(unidade).strip()):
            raise ValueError(f"{onde}: tipo '{tipo}' exige 'unidade'")
        if tipo == "escolha" and (not isinstance(opcoes, list) or not opcoes):
            raise ValueError(
                f"{onde}: tipo 'escolha' exige 'opcoes' como lista não vazia"
            )

        faixa_tuple: tuple[float, float] | None = None
        if faixa is not None:
            if (
                not isinstance(faixa, list)
                or len(faixa) != 2
                or not all(isinstance(v, (int, float)) for v in faixa)
                or faixa[0] >= faixa[1]
            ):
                raise ValueError(f"{onde}: 'faixa' deve ser [mín, máx] com mín < máx")
            faixa_tuple = (float(faixa[0]), float(faixa[1]))

        opcoes_tuple = tuple(str(o) for o in opcoes) if opcoes else None

        pergunta_obj = Pergunta(
            id=pid,
            secao=secao,
            texto=str(texto),
            ajuda=str(ajuda),
            tipo=tipo,
            unidade=str(unidade) if unidade else None,
            faixa=faixa_tuple,
            fonte_faixa=str(fonte_faixa) if fonte_faixa else None,
            opcoes=opcoes_tuple,
            obrigatoria=obrigatoria,
        )
        perguntas_lista.append(pergunta_obj)

        var_tipo = "numero" if tipo in ("numero", "inteiro") else "categoria"
        todas_vars[pid] = Variavel(
            nome=pid,
            grupo="perguntas",
            tipo=var_tipo,
            unico=True,
            descricao=str(texto),
            unidade=str(unidade) if unidade else None,
            valores=opcoes_tuple,
            fonte="usuário",
        )

    # 4. Variáveis externas
    for i, v in enumerate(externas_raw):
        onde = f"variaveis.yaml, externas '{v.get('nome', i)}'"
        if not isinstance(v, dict):
            raise ValueError(f"{onde}: deve ser um dicionário")  # noqa: TRY004
        nome = v.get("nome")
        if not nome:
            raise ValueError(f"{onde}: 'nome' obrigatório")
        _validar_nome(nome, onde)
        if nome in todas_vars:
            raise ValueError(f"{onde}: nome '{nome}' repetido ou colide com pergunta")

        tipo = v.get("tipo", "numero")
        if tipo not in TIPOS_VARIAVEL:
            raise ValueError(f"{onde}: tipo '{tipo}' inválido")
        unidade = v.get("unidade")
        if tipo == "numero" and (not unidade or not str(unidade).strip()):
            raise ValueError(f"{onde}: tipo 'numero' exige 'unidade'")

        todas_vars[nome] = Variavel(
            nome=nome,
            grupo="externas",
            tipo=tipo,
            unico=True,
            descricao=str(v.get("descricao", "")),
            unidade=str(unidade) if unidade else None,
            fonte=str(v.get("fonte", "")),
        )

    # 5. Variáveis calculadas
    for i, v in enumerate(calculadas_raw):
        onde = f"variaveis.yaml, calculadas '{v.get('nome', i)}'"
        if not isinstance(v, dict):
            raise ValueError(f"{onde}: deve ser um dicionário")  # noqa: TRY004
        nome = v.get("nome")
        if not nome:
            raise ValueError(f"{onde}: 'nome' obrigatório")
        _validar_nome(nome, onde)
        if nome in todas_vars:
            raise ValueError(f"{onde}: nome '{nome}' repetido ou colide com pergunta")

        tipo = v.get("tipo", "numero")
        if tipo not in TIPOS_VARIAVEL:
            raise ValueError(f"{onde}: tipo '{tipo}' inválido")
        unidade = v.get("unidade")
        if tipo == "numero" and (not unidade or not str(unidade).strip()):
            raise ValueError(f"{onde}: tipo 'numero' exige 'unidade'")

        formula = v.get("formula")
        if not formula or not str(formula).strip():
            raise ValueError(f"{onde}: 'formula' obrigatória")

        entradas = v.get("entradas")
        if not isinstance(entradas, list) or not entradas:
            raise ValueError(f"{onde}: 'entradas' deve ser uma lista não vazia")
        for e in entradas:
            _validar_nome(str(e), f"{onde}, entrada")
        if len(entradas) != len(set(entradas)):
            raise ValueError(f"{onde}: 'entradas' possui itens duplicados")

        opcionais_raw = v.get("opcionais")
        if opcionais_raw is None:
            opcionais_tuple: tuple[str, ...] = ()
        elif isinstance(opcionais_raw, list):
            for opt in opcionais_raw:
                _validar_nome(str(opt), f"{onde}, opcional")
            if len(opcionais_raw) != len(set(opcionais_raw)):
                raise ValueError(f"{onde}: 'opcionais' possui itens duplicados")
            opcionais_tuple = tuple(str(o) for o in opcionais_raw)
        else:
            raise ValueError(f"{onde}: 'opcionais' deve ser uma lista")

        intersecao = set(entradas) & set(opcionais_tuple)
        if intersecao:
            nomes_inter = ", ".join(sorted(intersecao))
            raise ValueError(
                f"{onde}: variável '{nomes_inter}' não pode estar em 'entradas' e 'opcionais' simultaneamente"
            )

        todas_vars[nome] = Variavel(
            nome=nome,
            grupo="calculadas",
            tipo=tipo,
            unico=True,
            descricao=str(v.get("descricao", "")),
            unidade=str(unidade) if unidade else None,
            formula=str(formula),
            entradas=tuple(str(e) for e in entradas),
            opcionais=opcionais_tuple,
            fonte=str(v.get("fonte", "")),
        )

    # 6. Variáveis de conclusão
    for i, v in enumerate(conclusoes_raw):
        onde = f"variaveis.yaml, conclusoes '{v.get('nome', i)}'"
        if not isinstance(v, dict):
            raise ValueError(f"{onde}: deve ser um dicionário")  # noqa: TRY004
        nome = v.get("nome")
        if not nome:
            raise ValueError(f"{onde}: 'nome' obrigatório")
        _validar_nome(nome, onde)
        if nome in todas_vars:
            raise ValueError(
                f"{onde}: nome '{nome}' repetido ou colide com outra variável"
            )

        camada = v.get("camada")
        if camada not in CAMADAS:
            raise ValueError(
                f"{onde}: camada '{camada}' inválida. Deve ser uma de {CAMADAS}"
            )

        tipo = v.get("tipo", "categoria")
        if tipo not in TIPOS_VARIAVEL:
            raise ValueError(f"{onde}: tipo '{tipo}' inválido")

        if "unico" not in v or not isinstance(v["unico"], bool):
            raise ValueError(f"{onde}: campo 'unico' obrigatório e deve ser booleano")
        unico = bool(v["unico"])

        valores_tuple = None
        if tipo == "categoria":
            valores = v.get("valores")
            if not isinstance(valores, list) or not valores:
                raise ValueError(
                    f"{onde}: tipo 'categoria' exige 'valores' como lista não vazia"
                )
            valores_tuple = tuple(valores)
        else:
            unidade = v.get("unidade")
            if not unidade or not str(unidade).strip():
                raise ValueError(f"{onde}: tipo 'numero' exige 'unidade'")

        todas_vars[nome] = Variavel(
            nome=nome,
            grupo="conclusoes",
            tipo=tipo,
            unico=unico,
            camada=camada,
            descricao=str(v.get("descricao", "")),
            unidade=str(v.get("unidade")) if v.get("unidade") else None,
            valores=valores_tuple,
            fonte=str(v.get("fonte", "")),
        )

    # Validar se as entradas e opcionais das calculadas existem e não são conclusões, e se não há ciclos
    calculadas_dict: dict[str, Variavel] = {
        k: v for k, v in todas_vars.items() if v.grupo == "calculadas"
    }
    for cv in calculadas_dict.values():
        for e in cv.entradas:
            if e not in todas_vars:
                raise ValueError(
                    f"variaveis.yaml, calculadas '{cv.nome}': entrada '{e}' não declarada"
                )
            if todas_vars[e].grupo == "conclusoes":
                raise ValueError(
                    f"variaveis.yaml, calculadas '{cv.nome}': entrada '{e}' não pode ser do grupo 'conclusoes'"
                )
        for opt in cv.opcionais:
            if opt not in todas_vars:
                raise ValueError(
                    f"variaveis.yaml, calculadas '{cv.nome}': opcional '{opt}' não declarada"
                )
            if todas_vars[opt].grupo == "conclusoes":
                raise ValueError(
                    f"variaveis.yaml, calculadas '{cv.nome}': opcional '{opt}' não pode ser do grupo 'conclusoes'"
                )

    _detectar_ciclo_calculadas(calculadas_dict)

    # 7. Regras de produção
    regras_lista: list[Regra] = []
    ids_regras: set[str] = set()

    camada_indices = {c: idx for idx, c in enumerate(CAMADAS)}

    for ordem, r in enumerate(regras_raw):
        onde = f"regras.yaml, regra [{ordem}]"
        if not isinstance(r, dict):
            raise ValueError(f"{onde}: deve ser um dicionário")  # noqa: TRY004

        rid = r.get("id")
        if not rid or not str(rid).strip():
            raise ValueError(f"{onde}: campo 'id' obrigatório")
        rid = str(rid)
        onde = f"regras.yaml, regra '{rid}'"

        if rid in ids_regras:
            raise ValueError(f"{onde}: id repetido")
        ids_regras.add(rid)

        camada = r.get("camada")
        if camada not in CAMADAS:
            raise ValueError(
                f"{onde}: camada '{camada}' inválida. Deve ser uma de {CAMADAS}"
            )

        prefixo_esperado = PREFIXOS_CAMADA[camada]
        if not rid.startswith(prefixo_esperado):
            raise ValueError(
                f"{onde}: id deve começar com '{prefixo_esperado}' para a camada '{camada}'"
            )

        descricao = r.get("descricao")
        if not descricao or not str(descricao).strip():
            raise ValueError(f"{onde}: campo 'descricao' obrigatório")

        prioridade = r.get("prioridade")
        if not isinstance(prioridade, int) or isinstance(prioridade, bool):
            raise ValueError(f"{onde}: campo 'prioridade' deve ser um número inteiro")  # noqa: TRY004

        cf = r.get("cf")
        if (
            not isinstance(cf, (int, float))
            or isinstance(cf, bool)
            or not (0.0 <= cf <= 1.0)
        ):
            raise ValueError(f"{onde}: campo 'cf' deve ser float entre 0.0 e 1.0")

        fonte = r.get("fonte")
        if not fonte or not str(fonte).strip():
            raise ValueError(f"{onde}: campo 'fonte' obrigatório")

        # Conclusão (entao)
        entao = r.get("entao")
        if not isinstance(entao, dict) or "fato" not in entao or "valor" not in entao:
            raise ValueError(f"{onde}: 'entao' deve ser dict com 'fato' e 'valor'")

        fato_concluido = entao["fato"]
        if fato_concluido not in todas_vars:
            raise ValueError(
                f"{onde}: fato de conclusão '{fato_concluido}' não existe em variaveis.yaml"
            )

        var_concluida = todas_vars[fato_concluido]
        if var_concluida.grupo != "conclusoes":
            raise ValueError(
                f"{onde}: 'entao.fato' deve ser uma variável de 'conclusoes', "
                f"recebeu '{var_concluida.grupo}'"
            )

        if var_concluida.camada != camada:
            raise ValueError(
                f"{onde}: camada da regra ('{camada}') deve ser igual à camada da "
                f"variável de conclusão '{fato_concluido}' ('{var_concluida.camada}')"
            )

        valor_concluido = entao["valor"]
        if (
            var_concluida.tipo == "categoria"
            and var_concluida.valores
            and valor_concluido not in var_concluida.valores
        ):
            raise ValueError(
                f"{onde}: valor concluído '{valor_concluido}' não permitido para "
                f"'{fato_concluido}'. Permitidos: {list(var_concluida.valores)}"
            )

        # Premissas (se)
        se = r.get("se")
        if not isinstance(se, list) or not se:
            raise ValueError(f"{onde}: 'se' deve ser uma lista não vazia de premissas")

        premissas_lista: list[Premissa] = []
        for j, cond in enumerate(se):
            onde_cond = f"{onde}, premissa [{j}]"
            if not isinstance(cond, list) or len(cond) != 3:
                raise ValueError(
                    f"{onde_cond}: premissa deve ter exatamente 3 elementos [fato, operador, alvo]"
                )

            p_fato, p_op, p_alvo = cond
            if p_fato not in todas_vars:
                raise ValueError(f"{onde_cond}: fato '{p_fato}' não declarado")

            if p_op not in OPERADORES:
                raise ValueError(
                    f"{onde_cond}: operador '{p_op}' inválido. Deve ser um de {OPERADORES}"
                )

            var_p_fato = todas_vars[p_fato]

            # Estratificação D4: premissa não pode ler conclusão de camada posterior ou da mesma camada posterior
            if var_p_fato.grupo == "conclusoes" and var_p_fato.camada is not None:
                idx_fato_camada = camada_indices[var_p_fato.camada]
                idx_regra_camada = camada_indices[camada]
                if idx_fato_camada >= idx_regra_camada:
                    raise ValueError(
                        f"{onde_cond}: regra da camada '{camada}' não pode ter premissa "
                        f"que lê fato da camada '{var_p_fato.camada}'"
                    )

            # Validação do alvo
            if isinstance(p_alvo, str) and p_alvo.startswith("$"):
                ref_nome = p_alvo[1:]
                if ref_nome not in todas_vars:
                    raise ValueError(
                        f"{onde_cond}: variável referenciada '{ref_nome}' não existe"
                    )
                ref_var = todas_vars[ref_nome]
                if not ref_var.unico:
                    raise ValueError(
                        f"{onde_cond}: referência '${ref_nome}' inválida: a variável "
                        f"referenciada deve ser 'unico: true'"
                    )
                if p_op in ("<", "<=", ">", ">=") and (
                    var_p_fato.tipo != "numero" or ref_var.tipo != "numero"
                ):
                    raise ValueError(
                        f"{onde_cond}: operador numérico '{p_op}' exige que ambos "
                        f"'{p_fato}' e '{ref_nome}' sejam do tipo 'numero'"
                    )
            else:
                # Alvo literal
                if p_op in ("<", "<=", ">", ">="):
                    if var_p_fato.tipo != "numero":
                        raise ValueError(
                            f"{onde_cond}: operador '{p_op}' só é permitido em variáveis do tipo 'numero'"
                        )
                    if not isinstance(p_alvo, (int, float)) or isinstance(p_alvo, bool):
                        raise ValueError(
                            f"{onde_cond}: operador '{p_op}' exige alvo numérico literal"
                        )
                elif p_op == "in":
                    if not isinstance(p_alvo, list):
                        raise ValueError(
                            f"{onde_cond}: operador 'in' exige alvo como lista"
                        )
                    if var_p_fato.tipo == "categoria" and var_p_fato.valores:
                        for item in p_alvo:
                            if item not in var_p_fato.valores:
                                raise ValueError(
                                    f"{onde_cond}: item '{item}' em 'in' não é um valor "
                                    f"permitido para '{p_fato}'"
                                )
                elif (
                    p_op in ("==", "!=")
                    and var_p_fato.tipo == "categoria"
                    and var_p_fato.valores
                    and p_alvo not in var_p_fato.valores
                ):
                    raise ValueError(
                        f"{onde_cond}: valor '{p_alvo}' não é permitido para "
                        f"'{p_fato}'. Permitidos: {list(var_p_fato.valores)}"
                    )

            premissas_lista.append(Premissa(fato=p_fato, operador=p_op, alvo=p_alvo))

        regras_lista.append(
            Regra(
                id=rid,
                descricao=str(descricao),
                camada=camada,
                prioridade=int(prioridade),
                se=tuple(premissas_lista),
                fato=fato_concluido,
                valor=valor_concluido,
                cf=float(cf),
                fonte=str(fonte),
                ordem=ordem,
            )
        )

    return Base(
        versao=versao,
        regras=tuple(regras_lista),
        perguntas=tuple(perguntas_lista),
        secoes=tuple(secoes_dict.values()),
        variaveis=todas_vars,
    )
