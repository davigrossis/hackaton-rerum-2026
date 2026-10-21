# Testes

Rode na raiz do repositório, com o ambiente ativado (passo a passo no `README.md` da raiz):

```bash
pytest -q                                  # todos os testes
pytest tests/test_mercado.py -q            # só os fatos de mercado
pytest tests/test_catalogo_mercado.py -v   # catálogo da CONAB, com um caso por produto
pytest tests/test_inferencia.py -v         # só o motor de inferência
```

## O que cada arquivo testa
| Arquivo | O que testa | Pergunta que responde |
|---|---|---|
| `test_esqueleto.py` | o projeto de pé: a base de conhecimento carrega, o app abre e o `CLAUDE.md` só importa o `AGENTS.md` | "O projeto roda?" |
| `test_contratos.py` | contratos da base de conhecimento, validações de carga, memória de trabalho e APIs do motor | "Os contratos e regras estão consistentes?" |
| `test_indicadores.py` | 21 indicadores econômicos e zootécnicos calculados à mão, opcionais, divisores zero e paridade YAML | "Os cálculos econômicos e zootécnicos estão corretos e protegidos?" |
| `test_inferencia.py` | o motor de inferência: premissas, ciclo por camada, resolução de conflito, bloqueio de fato único e CF, com a fazenda de exemplo do guia | "O motor raciocina como o guia descreve?" |
| `test_mercado.py` | **a saída**: o que `fatos_mercado` devolve | "O sistema calcula os fatos certos?" |
| `test_catalogo_mercado.py` | **a entrada**: o catálogo `conhecimento/mercado.yaml` e o script de rascunho | "O sistema está lendo os produtos certos da base?" |

Os dois arquivos de mercado se completam; nenhum substitui o outro:
- **id trocado no catálogo** (4744, soja, no lugar de 4742, milho): só o `test_catalogo_mercado.py` pega;
- **erro de cálculo** (janela de 12 meses, troca leite:milho, último preço do insumo): o catálogo continua certo, e só o `test_mercado.py` pega.

### `test_contratos.py`
- Valida o carregamento da base real e da base fixture de exemplo (`tests/fixtures/base_exemplo/`);
- Confere se as variáveis externas batem com o que `fatos_mercado` devolve em nomes e unidades;
- Testa 27 casos de preenchimento incorreto de regras, perguntas e variáveis (incluindo ciclo, conclusões e duplicatas em opcionais, e camada no `$nome`), garantindo mensagens de erro claras;
- Testa operações da memória de trabalho (adição, combinação de CF, valor único vs multivalorado, cópia independente);
- Testa `perguntas_pendentes` v0 e integridade do motor (não importa domínio, interface ou Streamlit).

### `test_indicadores.py`
- Valida os 21 indicadores econômicos e zootécnicos contra uma fazenda de referência conferida à mão em 2 casas decimais;
- Testa comportamento de opcionais ausentes e valores `None` nas somas de `receita_total`, `custo_alimentar` e `coe`;
- Testa proteção de divisores zero e negativos em todos os denominadores (produção, rebanho, área, trabalhadores, COE e preço UF);
- Garante imutabilidade dos dicionários de entrada e externos;
- Garante paridade 1:1 entre a tupla `INDICADORES` em código e o grupo `calculadas` de `conhecimento/variaveis.yaml`.

### `test_inferencia.py`
- `avaliar_premissas`: fato ausente torna a premissa falsa (inclusive com `!=`), `$nome` usa o menor CF dos dois fatos, valor com CF abaixo de 0,2 conta como ausente, fato com vários valores;
- `inferir` com a fazenda do guia (`docs/sistema-especialista.md`, seção 8): a cadeia R-IND-01 → R-SIT-03 → R-CAU-01 → R-REC-01 com CFs 1,0 → 1,0 → 0,7 → 0,56; sem o preço da fazenda, só a cadeia dele para; com o preço a CF 0,25, a recomendação não sai;
- resolução de conflito (prioridade → condições → ordem no arquivo), mesma entrada dando o mesmo traço e a memória de entrada intacta;
- fato único: a exceção mais específica vence, e a regra geral fica em `bloqueadas` no ciclo da vencedora;
- CF combinado: duas causas iguais (0,7 e 0,5) chegam a 0,85 antes de a recomendação disparar (0,68). Sem a ordem por camada (D3), este teste falha.

### `test_mercado.py`
- `fatos_mercado("MG")` funciona sem internet, e cada fato traz fonte e período (critérios de aceite da issue #4);
- os valores de MG batem com o `base.md`, que foi calculado com pandas: uma referência independente do código;
- a média de 12 meses diz quantos meses entraram (o AC tem 8);
- insumo sem preço no mês usa o último disponível, com a data dele;
- UF sem dado fica sem o fato, em vez de receber zero;
- valor fora da faixa do catálogo é descartado.

### `test_catalogo_mercado.py`
- **Gerados a partir do catálogo:** para cada produto do `mercado.yaml`, o id existe na base com o nome declarado e os valores ficam dentro da faixa. Produto novo no YAML ganha esses testes sem ninguém escrever código. Com `-v`, eles aparecem como `[leite]`, `[milho]` e `[diesel]`.
- O carregador recusa catálogo mal preenchido: campo `PREENCHER`, id sem aspas, `sem_preco_no_mes` inválido, faixa invertida e produto repetido.
- O rascunho de `python -m dados.rascunho_catalogo` traz os dados da base e só entra no catálogo depois de preenchido.

## Quando um teste falhar
- **Depois de trocar a base da CONAB:** o `test_catalogo_mercado.py` aponta id que mudou de nome e valor fora da faixa, com UF, mês e valor. Se o preço for real, alargue a faixa no `mercado.yaml`.
- **Depois de mexer no `dominio/mercado.py`:** o `test_mercado.py` mostra qual fato mudou.
- **Depois de mexer no `motor/`:** o `test_inferencia.py` mostra qual regra ou CF mudou no traço.

## Ainda não existe
- `test_casos.py`: casos conhecidos de fazendas, que chegam com a issue #11 (`fase-2-casos-conhecidos`).
