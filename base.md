# Base de dados: CONAB · Preços Agropecuários Mensais por UF

Arquivo: `dados/raw/PrecosMensalUF.txt`, original da CONAB, sem alterações.
Tema T3: "Análise econômica e financeira com dados zootécnicos e custos de insumos".

## 1. Em resumo
- **Fonte:** CONAB, Portal de Informações Agropecuárias: https://portaldeinformacoes.conab.gov.br/downloads/arquivos/PrecosMensalUF.txt
- **Conteúdo:** preço médio mensal por UF de 1.251 produtos (produtos agrícolas, insumos, máquinas, serviços e alimentos), em 4 níveis de comercialização.
- **Período:** 10/2025 a 09/2026 (12 meses). A CONAB atualiza o arquivo todo dia; esta cópia tem 3.158.384 bytes e 20.538 linhas de dados.
- **Licença:** o portal não declara licença própria; o site da CONAB usa CC BY-ND 3.0. Por isso: citar "Fonte: CONAB" e não editar o arquivo; todo cálculo fica no código.
- **Papel no T3:** cobre os **preços**, ou seja, o que o produtor recebe pelo leite e o que paga por parte dos insumos. Os **dados zootécnicos** e os **custos da fazenda** continuam vindo do usuário.

## 2. Formato do arquivo
| Item | Valor | Consequência |
|---|---|---|
| Separador | `;` | — |
| Codificação | latin-1 (ISO-8859-1); **não abre como UTF-8** | passar `encoding="latin-1"` |
| Quebra de linha | CRLF (Windows) | pandas e `csv` lidam sozinhos |
| Cabeçalho | 1ª linha; 9 colunas; sem aspas | — |
| Decimal | vírgula (`3,04`); sem separador de milhar | `decimal=","` |
| Texto | largura fixa, com espaços à direita: produto 25, classificação 20, UF 10, região 15, nível 60 | sempre aplicar `strip()` |
| Valores ausentes | 1.575 linhas sem valor e 10 com `0,0` | descartar os dois casos |

Leitura testada com pandas 3.0.6 (sobram 18.953 linhas válidas):
```python
import pandas as pd

df = pd.read_csv(
    "dados/raw/PrecosMensalUF.txt",
    sep=";",
    encoding="latin-1",
    decimal=",",
    dtype={"id_produto": str},
)
for col in [
    "produto",
    "classificao_produto",
    "uf",
    "regiao",
    "dsc_nivel_comercializacao",
]:
    df[col] = df[col].str.strip()
df = df[df["valor_produto_kg"] > 0]  # descarta vazios e zeros

# preço do leite ao produtor em MG, mês a mês (média se houver mais de uma cotação)
leite_mg = (
    df[(df["id_produto"] == "6542") & (df["uf"] == "MG")]
    .groupby(["ano", "mes"])["valor_produto_kg"]
    .mean()
)
```

## 3. Dicionário de dados
| Coluna | Tipo | Exemplo | O que é | Como funciona e cuidados |
|---|---|---|---|---|
| `produto` | texto (25) | `LEITE DE VACA` | nome do produto, insumo, máquina ou serviço | cortado em 25 caracteres (ex.: `ALUGUEL DE MAQUINA E IMPL`); 1.251 valores; **não serve como chave** |
| `classificao_produto` | texto (20) | `IN NATURA` | variedade, tipo ou especificação | o nome da coluna vem com erro de digitação (`classificao`), então use exatamente assim. Cortado em 20 caracteres; `NÃO INFORMADO` quando não há; 1.802 valores |
| `id_produto` | código numérico, ler como texto | `6542` | identificador do par produto + classificação | **é a chave confiável**: cada id tem um só nome, mas 45 nomes cortados têm mais de um id. O mesmo id aparece em níveis diferentes (milho `4742` no atacado e no produtor). 2.681 ids |
| `uf` | texto (2) | `MG` | unidade da federação | 27 UFs; **não existe linha "Brasil"** |
| `regiao` | texto | `SUDESTE` | macrorregião do IBGE | 5 valores, sempre coerentes com a UF |
| `ano` | inteiro | `2026` | ano de referência | 2025 e 2026 |
| `mes` | inteiro 1–12 | `9` | mês de referência | sem zero à esquerda; o período sai de ano + mês |
| `dsc_nivel_comercializacao` | texto (60) | `PREÇO RECEBIDO P/ PRODUTOR` | ponto da cadeia em que o preço foi medido | 4 níveis (seção 4); diz se o valor é **receita** ou **custo** para a fazenda |
| `valor_produto_kg` | decimal | `3,04` | preço médio em R$ | **a unidade depende do produto**, apesar do "_kg" no nome (seção 6). Vazio = sem cotação |

## 4. Níveis de comercialização
| Nível | Linhas | O que significa | Uso no T3 |
|---|---|---|---|
| `PREÇO RECEBIDO P/ PRODUTOR` | 6.380 | quanto o produtor recebe ao vender, na porteira | **receita**: leite in natura, boi gordo. Também é a referência de preço para grãos (milho, sorgo, soja) |
| `PREÇO PAGO PELO PRODUTOR` | 7.150 | quanto o produtor paga por insumos e serviços | **custo**: diesel, ureia, calcário, NPK |
| `ATACADO` | 1.808 | preço entre empresas | pouco útil; o farelo de soja só aparece aqui, e só no ES |
| `VAREJO` | 5.200 | preço ao consumidor | contexto: leite longa vida no supermercado |

⚠️ O milho "recebido pelo produtor" é o que o **agricultor** ganha. Para a fazenda leiteira, que **compra** milho, esse preço é um piso: ela paga mais, por causa de frete e margem do revendedor.

## 5. Cobertura
- **Linhas por mês:** 10/25: 2.399 · 11/25: 3.343 · 12/25: 1.498 · 01/26: 1.082 · 02/26: 1.140 · 03/26: 3.184 · 04/26: 1.126 · 05/26: 1.100 · 06/26: 964 · 07/26: 1.402 · 08/26: 970 · 09/26: 2.330.
- **Por que varia:** preços pagos (insumos) são levantados em meses espaçados. 10/25, 11/25, 03/26, 07/26 e 09/26 concentram 96% dessas linhas, e não há nenhuma em 01/26 nem em 06/26. Já leite, milho e boi (preço recebido) são mensais.
- **Linhas por região:** Nordeste 5.880 · Sul 3.873 · Norte 3.811 · Centro-Oeste 3.602 · Sudeste 3.372.

## 6. Unidade do valor: por que o "_kg" engana
| Tipo de produto | Unidade provável | Exemplo |
|---|---|---|
| Leite | R$/L (1 L ≈ 1,03 kg; diferença de ~3%) | leite in natura MG 09/26: 3,04 |
| Grãos | R$/kg (× 60 = R$/saca) | milho MG 09/26: 1,07 → R$ 64,20/saca |
| Combustível | R$/L | diesel MG 09/26: 6,69 |
| Boi gordo | provavelmente R$/kg de carcaça (× 15 = R$/@), a confirmar | MG 09/26: 22,88 → R$ 343/@ |
| Fertilizantes | em geral R$/kg, mas há linhas em R$/saca ou R$/t | ureia MG 03/26: 3.100 (provável R$/t); ureia BA 10/25: 218 |
| Máquinas e equipamentos | R$/unidade | colheitadeira: até R$ 8.785.000 |
| Serviços e mão de obra | R$ por hora, diária, hectare ou mês | quase sempre vazio |

Conclusão: o sistema só deve ler uma **lista fechada de produtos**, cada um com unidade e faixa plausível declaradas (ideia 1 da seção 11).

## 7. Produtos que importam para a fazenda leiteira
| Uso na fazenda | Produto (id) | Nível | Cobertura | MG |
|---|---|---|---|---|
| Receita do leite | Leite de vaca in natura (6542) | recebido | 27 UFs × 12 meses; AC sem 01–04/26 | 12 meses; R$ 2,11–3,04/L |
| Concentrado: energia | Milho em grãos (4742) | recebido | 26 UFs (sem AM), 12 meses | 12 meses; R$ 0,93–1,07/kg |
| Concentrado: substituto do milho | Sorgo granífero (4745) | recebido | 10 UFs, 12 meses | 12 meses; R$ 0,76–0,84/kg |
| Concentrado: proteína | Soja em grãos (4744) | recebido | 17 UFs, 12 meses | 12 meses; R$ 1,84–2,49/kg |
| Volumoso | Cana-de-açúcar (4238) | recebido | 13 UFs | 8 meses; R$ 0,12–0,16/kg |
| Combustível | Óleo diesel (4422) | pago | 23 UFs, 10 meses | 6 meses; R$ 5,85–7,16/L |
| Adubação de pastagem | Ureia (4579) | pago | 17 UFs, 5 meses | 2 meses; R$ 3,37–3,45/kg (+1 linha em R$/t) |
| Correção de solo | Calcário dolomítico (4539) | pago | 17 UFs, 7 meses | 3 meses; R$ 0,32–0,50/kg |
| Adubação (NPK) | 69 fórmulas, ex.: 20-05-20 | pago | 16 UFs | 16 linhas |
| Venda de animais | Boi gordo (4193) | recebido | 9 UFs × 12 meses | 12 meses; R$ 19,23–22,88/kg |
| Contexto de mercado | Leite longa vida integral (4998) | varejo | 27 UFs × 12 meses | 12 meses; R$ 5,34–6,33/L |
| Concentrado: proteína | Farelo de soja (4440) | atacado | só ES | — |
| Concentrado | Caroço de algodão (4724) | recebido | 6 UFs | — |

## 8. O que esta base não tem
- **Mão de obra** (salário mínimo, diarista, tratorista, administrador): as linhas existem, mas estão **sem valor**.
- **Energia elétrica, terra nua e arrendamento:** linhas sem valor.
- **Sanidade e reprodução** (vacinas, medicamentos, sêmen): não existem.
- **Sal mineral, ração pronta, silagem e farelo de soja em MG:** não existem.
- **Equipamentos de leite** (ordenhadeira, tanque de resfriamento): não existem.
- **Dados zootécnicos** (rebanho, produção por vaca): nenhum.

Esses itens viram perguntas ao usuário. A produtividade regional pode vir do IBGE (issue #18).

## 9. Armadilhas e tratamento
1. **Nome cortado:** usar `id_produto` + `dsc_nivel_comercializacao` como chave, nunca o nome.
2. **Cotações repetidas:** 643 combinações (id, UF, mês, nível) têm mais de um valor, quase todas de insumos (ex.: id 4480 no PR em 09/26 tem 2,94 e 2,79). Usar a média por chave. O leite in natura não tem repetição.
3. **Vazios e zeros:** descartar. O fato não entra na memória de trabalho e a regra que depende dele não dispara.
4. **Unidade variável:** lista fechada de produtos + faixa plausível; o que cair fora da faixa é descartado (pega a ureia em R$/t).
5. **Meses faltando:** usar o último valor disponível junto com a data dele, e calcular médias só com os meses existentes. Avisar quando o dado for antigo: em MG, o diesel mais recente é de 09/26, mas a ureia é de 11/25.
6. **Valores atípicos no Norte:** AM chega a R$ 7,43/L (02/26), e RR e AP ficam entre R$ 5 e 6/L. Comparar a fazenda sempre com a própria UF e nunca usar esses valores como referência nacional.
7. **Sazonalidade:** comparar o preço da fazenda com o da UF **no mesmo mês**, não com a média anual (seção 10).
8. **Só 12 meses:** a média de 12 meses é o máximo possível; não há série longa para tendência.
9. **O arquivo muda todo dia:** guardar a data do download no `FONTES.md` e mostrá-la no parecer.
10. **Milho é piso para quem compra** (seção 4).

## 10. Retrato do mercado
**MG, mês a mês**
| Mês | Leite (R$/L) | Milho (R$/kg) | Troca leite:milho (kg de milho por litro) | Longa vida no varejo (R$/L) |
|---|---|---|---|---|
| 10/25 | 2,60 | 0,99 | 2,63 | 5,95 |
| 11/25 | 2,47 | 0,99 | 2,49 | 5,72 |
| 12/25 | 2,27 | 1,03 | 2,20 | 5,57 |
| 01/26 | 2,11 | 1,07 | 1,97 | 5,44 |
| 02/26 | 2,13 | 1,02 | 2,09 | 5,51 |
| 03/26 | 2,22 | 1,03 | 2,16 | 5,78 |
| 04/26 | 2,50 | 1,01 | 2,48 | 6,30 |
| 05/26 | 2,74 | 0,96 | 2,85 | 6,33 |
| 06/26 | 2,76 | 0,93 | 2,97 | 5,34 |
| 07/26 | 2,91 | 0,95 | 3,06 | 5,54 |
| 08/26 | 3,02 | 0,97 | 3,11 | 5,78 |
| 09/26 | 3,04 | 1,07 | 2,84 | 5,71 |

Leitura:
- **Sazonalidade clara:** o leite cai na época das chuvas (mínimo de R$ 2,11 em 01/26) e sobe na seca (R$ 3,04 em 09/26, +44%).
- **Troca leite:milho:** vai de 1,97 (01/26) a 3,11 (08/26); na seca, o mesmo litro compra 58% mais milho.
- **Sorgo:** em MG custa cerca de 0,8 × o preço do milho.
- **Fatia do produtor:** o produtor fica com ~53% do preço do longa vida no varejo (09/26: R$ 3,04 de R$ 5,71).

**UFs selecionadas (09/2026)**
| UF | Leite 09/26 | Média 12m | Mín–máx 12m | Milho 09/26 | Troca 09/26 | Troca média 12m |
|---|---|---|---|---|---|---|
| MG | 3,04 | 2,56 | 2,11–3,04 | 1,07 | 2,84 | 2,57 |
| PR | 2,81 | 2,46 | 2,15–2,81 | 0,98 | 2,87 | 2,70 |
| GO | 2,80 | 2,36 | 1,78–2,80 | 0,97 | 2,89 | 2,67 |
| SP | 2,60 | 2,25 | 1,95–2,60 | 1,07 | 2,43 | 2,23 |
| SC | 2,50 | 2,24 | 2,00–2,53 | 1,05 | 2,38 | 2,26 |
| RS | 2,41 | 2,16 | 1,91–2,41 | 1,01 | 2,39 | 2,20 |
| BA | 2,62 | 2,19 | 2,01–2,62 | 1,12 | 2,34 | 2,16 |
| RJ | 2,93 | 2,26 | 1,83–2,93 | 1,49 | 1,97 | 1,56 |
| ES | 2,50 | 2,26 | 2,00–2,52 | 1,42 | 1,76 | 1,64 |

## 11. Ideias para implementar no plano
Os limiares abaixo são ilustrativos e precisam ser validados com fonte na #8 e na #12.

| # | Ideia | Como funciona | Issue |
|---|---|---|---|
| 1 | Variáveis externas declaradas na base | Cada fato de mercado entra no `conhecimento/mercado.yaml` com fonte, `id_produto`, nível, unidade e faixa plausível. O leitor só aceita produtos da lista e descarta valores fora da faixa | #2, #3, #4 |
| 2 | Fatos de mercado por UF | Preço do leite (mês da consulta, média, mín. e máx. de 12m), milho, sorgo, soja, diesel, boi gordo e troca leite:milho (mês e média). Cada fato com fonte e período | #4 |
| 3 | Preço abaixo do mercado | Preço da fazenda abaixo do preço da UF **no mesmo mês** (ex.: −5%) → indicador `preco_leite = abaixo_mercado` → causa "preço recebido" → recomendações: negociar com o laticínio, buscar bonificação por qualidade e volume, avaliar cooperativa | #12 |
| 4 | Momento ruim para comprar concentrado | Troca leite:milho da UF abaixo da média de 12m → recomendação de compra coletiva e de planejar o estoque de milho para quando a troca estiver favorável | #12 |
| 5 | Sorgo como substituto | Sorgo/milho na UF abaixo de ~0,85 (MG ≈ 0,8) e custo alimentar alto → recomendação "avaliar trocar parte do milho por sorgo, com nutricionista" | #12 |
| 6 | Sazonalidade no parecer | Mini-gráfico com os 12 meses do leite na UF e o preço da fazenda marcado, mais a nota de que o preço cai na época das chuvas | #13 |
| 7 | Simulação com cenários reais | Em vez de ±30% fixo, usar o mín. e o máx. de 12m da UF: "e se o preço voltar a R$ 2,11, como em 01/26?" | #15 |
| 8 | Preço de equilíbrio × mercado | Mostrar o preço mínimo que cobre o COT ao lado do preço da UF ("faltam R$ 0,18/L para cobrir o COT") | #13 |
| 9 | Casos de teste com preços reais | A mesma fazenda com o preço de MG em 09/26 (R$ 3,04) e em 01/26 (R$ 2,11): pode dar lucro na seca e prejuízo nas chuvas. Ótimo par de casos conhecidos e de demo | #11, #24 |
| 10 | UF sem dado | Fato ausente → a regra não dispara e o parecer avisa ("sem preço de milho para AM") | #4, #13 |
| 11 | Contexto para a apresentação | Fatia do produtor no varejo (~53% em MG) e sazonalidade do preço | #23 |
| 12 | Receita com venda de animais (baixa prioridade) | Boi gordo como referência para vaca de descarte, com desconto a validar | #12 |

**Feito na #4:** `dados/raw/FONTES.md` com link, data do download e licença; catálogo de produtos em `conhecimento/mercado.yaml`; leitor em `dominio/mercado.py`, que segue as seções 2 e 9.
