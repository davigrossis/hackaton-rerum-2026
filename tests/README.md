# Testes

Rode na raiz do repositório, com o ambiente ativado (passo a passo no `README.md` da raiz):

```bash
pytest -q                                  # todos os testes
pytest tests/test_mercado.py -q            # só os fatos de mercado
pytest tests/test_catalogo_mercado.py -v   # catálogo da CONAB, com um caso por produto
```

## O que cada arquivo testa
| Arquivo | O que testa | Pergunta que responde |
|---|---|---|
| `test_esqueleto.py` | o projeto de pé: a base de conhecimento carrega, o app abre e o `CLAUDE.md` só importa o `AGENTS.md` | "O projeto roda?" |
| `test_mercado.py` | **a saída**: o que `fatos_mercado` devolve | "O sistema calcula os fatos certos?" |
| `test_catalogo_mercado.py` | **a entrada**: o catálogo `conhecimento/mercado.yaml` e o script de rascunho | "O sistema está lendo os produtos certos da base?" |

Os dois arquivos de mercado se completam; nenhum substitui o outro:
- **id trocado no catálogo** (4744, soja, no lugar de 4742, milho): só o `test_catalogo_mercado.py` pega;
- **erro de cálculo** (janela de 12 meses, troca leite:milho, último preço do insumo): o catálogo continua certo, e só o `test_mercado.py` pega.

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

## Ainda não existe
- `test_casos.py`: casos conhecidos de fazendas, que chegam com a issue #11 (`fase-2-casos-conhecidos`).
