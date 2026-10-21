# Contratos do Sistema Especialista: Base de Conhecimento e Motor

Este documento estabelece os contratos de dados, formatos YAML e assinaturas de API entre as três frentes do projeto:
- **Base de Conhecimento** (`conhecimento/*.yaml`)
- **Motor de Inferência** (`motor/*.py`)
- **Interface e Domínio** (`app.py`, `interface/`, `dominio/*.py`)

É este contrato que permite o desenvolvimento independente e em paralelo das frentes na Fase 1 (#5, #6, #7). Qualquer alteração neste contrato **só pode ser feita via Pull Request aprovado pela equipe**.

---

## 1. Mapeamento das 6 Ligações do Modelo Conceitual (Slide 14)

| Ligação | Papel no Projeto | Como fica no código |
|---|---|---|
| **Interface ↔ Motor** | Perguntas e respostas | A interface consulta `perguntas_pendentes(base, memoria)` e alimenta a memória com `origem='usuario'`. Na fase 3 (#26), o motor solicita o que falta para destravar regras em diálogo progressivo. |
| **Base → Motor** | Carga e validação de regras | `motor/regras.py::carregar_base()` valida toda a base: sintaxe, unicidade de identificadores, variáveis declaradas, compatibilidade de camadas e faixas de CF entre 0 e 1. |
| **Motor ↔ Memória** | Leitura e conclusão de fatos | O motor consulta fatos para casar premissas e grava conclusões com CF calculado e origem identificada. |
| **Motor → Explicação** | Registro de traço | Cada ciclo de inferência produz um registro detalhado (`Ciclo`): conflito, regra escolhida, premissas avaliadas, CF e bloqueios de fatos únicos. |
| **Aquisição → Base** | Gestão de conhecimento | Toda regra, pergunta ou produto novo é adicionado via YAML versionado no git em `conhecimento/`, sujeito a revisão por PR. |
| **Fontes externas → Memória** | Alimentação contextual | `dominio/mercado.py` extrai fatos de mercado (`origem='externo'`) com fonte e período (ex.: CONAB, MG, 09/2026) e os insere na memória antes da inferência. |

Os indicadores econômicos (`dominio/indicadores.py`) entram na memória antes do encadeamento com `origem='calculado'`; suas fórmulas constam em `variaveis.yaml` e são exibidas na explicação ("como?").

---

## 2. Decisões Arquiteturais Aprovadas (D1–D9)

- **D1 (Declaração de variáveis):** Arquivo centralizado `conhecimento/variaveis.yaml` dividido em 3 grupos (`calculadas`, `externas`, `conclusoes`). Perguntas do formulário são declaradas exclusivamente em `conhecimento/perguntas.yaml` (o `id` da pergunta é o identificador do fato).
- **D2 (Validação prévia):** `motor/regras.py::carregar_base()` valida a integridade referencial completa na inicialização. Erros geram `ValueError` com contexto e arquivo claros.
- **D3 (Estratificação por camadas):** A resolução de conflito avalia camada a camada (`indicador` → `situacao` → `causa` → `recomendacao`). Regras de camadas posteriores só entram no conjunto de conflito após o esgotamento das candidatas da camada anterior, garantindo que o CF de fatos intermediários esteja consolidado.
- **D4 (Conclusões restritas à camada):** Toda variável em `conclusoes` declara sua `camada`. Uma regra só conclui para variáveis de sua própria camada. Premissas nunca podem ler fatos concluídos na mesma camada ou em camadas posteriores.
- **D5 (Referências dinâmicas `$nome`):** Só podem referenciar variáveis com `unico: true`. O CF da premissa que compara dois fatos é o menor entre os dois (`min(cf_fato, cf_alvo)`).
- **D6 (Semântica dos operadores):** Fato não informado na memória torna a premissa **falsa** (inclusive para `!=`). Comparações `<, <=, >, >=` exigem variáveis numéricas. Para fatos multivalorados, `==` e `in` são verdadeiros se qualquer valor satisfizer; `!=` exige que nenhum valor seja igual.
- **D7 (Cálculo e herança de CF):** Respostas do usuário têm CF 1.0 (ou 0.7 quando marcadas como estimadas na #16). Fatos calculados recebem o menor CF de suas entradas. Fatos externos têm CF 1.0 (fonte oficial). Conclusão = `cf_regra × menor(CF_premissas)`. Premissas com CF < 0.2 contam como falsas. Conclusões coincidentes combinam CF: `CF1 + CF2 × (1 − CF1)`.
- **D8 (Imutabilidade de entradas):** O campo `entao.fato` de uma regra só pode concluir variáveis de `conclusoes`. Uma regra jamais sobrescreve respostas de usuário, fatos externos ou indicadores calculados.
- **D9 (Estruturas de explicação):** `como()` e `por_que()` retornam dataclasses puras (`NoComo`, `MotivoPergunta`), permitindo renderização desacoplada na interface.

---

## 3. Formato dos Arquivos YAML da Base de Conhecimento

### 3.1 `conhecimento/perguntas.yaml`
```yaml
versao: "0.1"

secoes:
  - id: identificacao
    titulo: Identificação da Propriedade
  - id: producao
    titulo: Rebanho e Produção

perguntas:
  - id: uf
    secao: identificacao
    texto: Em que UF fica a fazenda?
    ajuda: Estado onde a propriedade está localizada para consulta dos preços CONAB.
    tipo: escolha           # numero | inteiro | escolha | mes
    opcoes: [MG, SP, PR, ...]
    obrigatoria: true

  - id: preco_leite_fazenda
    secao: producao
    texto: Qual o preço médio recebido por litro de leite?
    ajuda: Valor líquido recebido pelo produtor no mês de referência.
    tipo: numero
    unidade: R$/L
    faixa: [0.5, 20.0]
    fonte_faixa: "Observado na CONAB"
    obrigatoria: true
```

### 3.2 `conhecimento/variaveis.yaml`
```yaml
versao: "0.1"

calculadas:
  - nome: receita_total
    descricao: Faturamento total com a venda de leite
    tipo: numero
    unidade: R$
    formula: producao_litros * preco_leite_fazenda
    entradas: [producao_litros, preco_leite_fazenda]
    fonte: "Fórmula de receita"

externas:
  - nome: preco_leite_uf
    descricao: Preço médio do leite recebido na UF no mês
    tipo: numero
    unidade: R$/L
    fonte: "CONAB, Preços Agropecuários Mensais por UF"

conclusoes:
  - nome: situacao_economica
    descricao: Classificação da viabilidade segundo Matsunaga et al. (1976)
    camada: situacao
    tipo: categoria
    unico: true             # Apenas uma conclusão prevalece; a segunda é bloqueada
    valores: [lucro, medio_prazo, curto_prazo, prejuizo]

  - nome: causa
    descricao: Causas prováveis do desempenho econômico
    camada: causa
    tipo: categoria
    unico: false            # Admite múltiplas causas concorrentes
    valores: [preco_recebido_baixo, custo_alimentar_alto]
```

### 3.3 `conhecimento/regras.yaml`
```yaml
versao: "0.1"

regras:
  - id: R-SIT-03
    descricao: Receita cobre o COE mas não o COT; sobrevive só no curto prazo
    camada: situacao
    prioridade: 50
    se:
      - [receita_total, ">=", $coe]
      - [receita_total, "<", $cot]
    entao:
      fato: situacao_economica
      valor: curto_prazo
    cf: 1.0
    fonte: "Matsunaga et al. (1976), metodologia de custo operacional"
```

---

## 4. API do Motor e Tipos de Dados

### 4.1 Memória de Trabalho (`motor/memoria.py`)
```python
class Memoria:
    def adicionar(
        self,
        nome: str,
        valor: Any,
        cf: float = 1.0,
        origem: str = "usuario",
        detalhe: str = "",
    ) -> Fato: ...
    def valores(self, nome: str) -> list[Fato]: ...
    def valor(self, nome: str) -> Fato | None: ...
    def tem(self, nome: str) -> bool: ...
    def fatos(self) -> list[Fato]: ...
    def copia(self) -> Memoria: ...
```

### 4.2 Carga de Regras (`motor/regras.py`)
```python
def carregar_base(pasta: Path = PASTA_CONHECIMENTO) -> Base: ...
```

### 4.3 Ciclo de Inferência (`motor/inferencia.py`)
```python
def inferir(base: Base, memoria: Memoria) -> Resultado: ...
def avaliar_premissas(regra: Regra, memoria: Memoria) -> list[PremissaAvaliada]: ...
def perguntas_pendentes(
    base: Base, memoria: Memoria, resultado: Resultado | None = None
) -> list[Pergunta]: ...
```

#### Semântica do motor (#5)
**Premissas** (`avaliar_premissas`): todas são avaliadas, sem parar na primeira falsa, para o traço e o diálogo (#26) enxergarem cada uma.
- Valor com CF < 0,2 conta como ausente. Fato ausente torna a premissa falsa, inclusive com `!=` (D6).
- `$nome`: o alvo é o valor do outro fato, e o CF da premissa é o menor dos dois (D5). Referência ausente torna a premissa falsa.
- Fato com vários valores: `==`, `in` e as comparações valem se algum valor satisfizer, com o maior CF entre os que satisfazem; `!=` exige que nenhum valor seja igual, com o menor CF entre os valores.
- `PremissaAvaliada.valor_fato` traz o valor, uma tupla quando há vários, ou `None` quando o fato falta. Premissa falsa tem CF 0.

**Ciclo** (`inferir`):
- Memória de entrada que já traga conclusão gera `ValueError`: só as regras concluem (D8). O motor trabalha numa cópia, e a memória recebida não muda.
- Camada por camada (D3), repete casar → resolver o conflito (maior `prioridade` → mais condições → ordem no arquivo) → disparar, até o conjunto de conflito ficar vazio. Cada regra dispara no máximo uma vez.
- A conclusão entra com CF = `cf_regra × menor CF das premissas`, `origem="regra"` e o id da regra. Se outra regra concluir o mesmo valor, a memória combina os CFs.
- Fato `unico`: a regra vencedora bloqueia as do conjunto que concluiriam outro valor. Elas saem da disputa e ficam em `Ciclo.bloqueadas`, no ciclo da vencedora.
- Uma passada por camada chega ao ponto fixo porque nenhuma premissa lê conclusão da própria camada ou de camada posterior, nem pelo `$nome` (D4, checada em `carregar_base`).

### 4.4 Módulo de Explicação (`motor/explicacao.py`)
```python
def como(resultado: Resultado, fato: str, valor: Any = None) -> list[NoComo]: ...
def por_que(
    base: Base, variavel: str, resultado: Resultado | None = None
) -> list[MotivoPergunta]: ...
```

### 4.5 Integração de Domínio (`dominio/`)
```python
# dominio/indicadores.py (#6)
def calcular_indicadores(
    entradas: dict[str, float], externos: dict[str, float]
) -> dict[str, dict]: ...


# dominio/diagnostico.py (#10)
def diagnosticar(
    respostas: dict, estimados: frozenset[str] = frozenset(), base: Base | None = None
) -> Resultado: ...
```
