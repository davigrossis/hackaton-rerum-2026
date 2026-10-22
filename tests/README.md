# Testes

Rode na raiz do repositório, com o ambiente ativado (passo a passo no `README.md` da raiz):

```bash
pytest -q                                  # todos os testes
pytest tests/test_mercado.py -q            # só os fatos de mercado
pytest tests/test_catalogo_mercado.py -v   # catálogo da CONAB, com um caso por produto
pytest tests/test_benchmark.py -v          # média da UF no IBGE e a R-IND-11, sem rede
pytest tests/test_inferencia.py -v         # só o motor de inferência
pytest tests/test_casos.py -v              # os 5 casos conhecidos de fazendas
pytest tests/test_regras.py -v             # as regras da base real, uma a uma
pytest tests/test_diagnostico.py -v        # a ponta a ponta: diagnóstico e tela
pytest tests/test_validacao.py -v          # validação de entradas
pytest tests/test_rodada_bugs.py -v        # rodada de bugs: 2 fazendas inventadas, formulário e fazendas aleatórias
```

## O que cada arquivo testa
| Arquivo | O que testa | Pergunta que responde |
|---|---|---|
| `test_esqueleto.py` | o projeto de pé: a base de conhecimento carrega, o app abre e o `CLAUDE.md` só importa o `AGENTS.md` | "O projeto roda?" |
| `test_contratos.py` | contratos da base de conhecimento, validações de carga, memória de trabalho e APIs do motor | "Os contratos e regras estão consistentes?" |
| `test_indicadores.py` | 21 indicadores econômicos e zootécnicos calculados à mão, opcionais, divisores zero e paridade YAML | "Os cálculos econômicos e zootécnicos estão corretos e protegidos?" |
| `test_casos.py` | os 5 casos conhecidos de fazendas (lucro, médio prazo, curto prazo por alimentação, prejuízo por preço + reprodução, produtividade abaixo da média da UF no IBGE) com contas à mão | "O sistema se comporta como esperado nos casos de referência?" |
| `test_regras.py` | as regras de `conhecimento/regras.yaml`, uma a uma, com os fatos postos direto na memória | "Cada regra conclui o que deve, e só quando deve?" |
| `test_diagnostico.py` | a ponta a ponta (#10, #13, #16): o `diagnosticar` monta a memória e os 4 casos conhecidos viram parecer executivo real na tela | "As respostas viram um parecer de verdade, na tela?" |
| `test_validacao.py` | validação e normalização de respostas (#14), rejeição de entradas inválidas e preservação de zero explícito | "O formulário e a API barram dados inconsistentes antes de rodar o motor?" |
| `test_explicacao.py` | as explicações "como?" e "por quê?" derivadas do traço de inferência | "O motor explica como chegou a cada conclusão e por que pergunta cada dado?" |
| `test_inferencia.py` | o motor de inferência: premissas, ciclo por camada, resolução de conflito, bloqueio de fato único e CF, com a fazenda de exemplo do guia | "O motor raciocina como o guia descreve?" |
| `test_mercado.py` | **a saída**: o que `fatos_mercado` devolve | "O sistema calcula os fatos certos?" |
| `test_catalogo_mercado.py` | **a entrada**: o catálogo `conhecimento/mercado.yaml` e o script de rascunho | "O sistema está lendo os produtos certos da base?" |
| `test_rodada_bugs.py` | a rodada de bugs cruzada (#22): 2 fazendas inventadas com contas à mão, cobertura de todas as regras, o formulário digitado campo a campo e fazendas aleatórias | "Uma fazenda que ninguém do time escreveu passa sem exceção e com o parecer certo?" |
| `test_benchmark.py` | o snapshot da PPM/IBGE, a média da UF (`fatos_benchmark`) e a R-IND-11 no caso 05, com a rede bloqueada | "A comparação com o IBGE funciona offline e dispara quando deve?" |

Os dois arquivos de mercado se completam; nenhum substitui o outro:
- **id trocado no catálogo** (4744, soja, no lugar de 4742, milho): só o `test_catalogo_mercado.py` pega;
- **erro de cálculo** (janela de 12 meses, troca leite:milho, último preço do insumo): o catálogo continua certo, e só o `test_mercado.py` pega.

### `test_contratos.py`
- Valida o carregamento da base real e da base fixture de exemplo (`tests/fixtures/base_exemplo/`);
- Confere se as variáveis externas batem com o que `fatos_mercado` e `fatos_benchmark` devolvem em nomes e unidades;
- Testa 27 casos de preenchimento incorreto de regras, perguntas e variáveis (incluindo ciclo, conclusões e duplicatas em opcionais, e camada no `$nome`), garantindo mensagens de erro claras;
- Testa operações da memória de trabalho (adição, combinação de CF, valor único vs multivalorado, cópia independente);
- Testa `perguntas_pendentes` v0 e integridade do motor (não importa domínio, interface ou Streamlit);
- Garante que a interface só usa a API: `app.py` e `interface/` não importam `dominio.indicadores`, `dominio.mercado`, `dominio.benchmark` nem `yaml` (critério da #10).

### `test_indicadores.py`
- Valida os 21 indicadores econômicos e zootécnicos contra uma fazenda de referência conferida à mão em 2 casas decimais;
- Testa comportamento de opcionais ausentes e valores `None` nas somas de `receita_total`, `custo_alimentar` e `coe`;
- Testa proteção de divisores zero e negativos em todos os denominadores (produção, rebanho, área, trabalhadores, COE e preço UF);
- Garante imutabilidade dos dicionários de entrada e externos;
- Garante paridade 1:1 entre a tupla `INDICADORES` em código e o grupo `calculadas` de `conhecimento/variaveis.yaml`.

### `test_casos.py`
- Valida os 5 casos conhecidos de referência em `dados/casos/` (`01_lucro.yaml`, `02_medio_prazo.yaml`, `03_curto_prazo_alimentacao.yaml`, `04_prejuizo_preco_reproducao.yaml` e `05_benchmark_ibge.yaml`);
- Garante conformidade de todas as variáveis de entrada com `conhecimento/perguntas.yaml` (sem erros no formulário e dentro dos limites zootécnicos);
- Confere os preços oficiais da CONAB (`fatos_mercado`) e a média da UF no IBGE (`fatos_benchmark`) para a UF e mês de referência de cada caso;
- Confere todos os 21 indicadores econômicos e zootécnicos (`calcular_indicadores`) contra as contas feitas à mão em 2 casas decimais;
- Valida o enquadramento de Matsunaga et al. (1976) e os sinais de domínio característicos de cada perfil;
- Atua como contrato executável para as regras de produção (`inferir`) e ponta a ponta: o `diagnosticar` chega ao mesmo traço da montagem manual;
- causas e recomendações batem com o esperado como **conjunto exato** (#12): regra que dispara a mais ou a menos derruba o caso.

### `test_diagnostico.py`
- Cada fato entra com a sua origem: resposta (`usuario`), CONAB (`externo`, com UF e mês no detalhe), indicador (`calculado`, com a fórmula e os valores) e conclusão (`regra`, com o id);
- resposta estimada entra com CF 0,7 e derruba a cadeia que depende dela (receita, situação), sem mexer no que não depende (COE);
- opcional vazio (ausente ou `None`) não vira fato: sem capital investido não há CT, e a fazenda que cobre o COT fica sem situação;
- sem mês de referência não há fatos de mercado, e a situação sai mesmo assim;
- chave que não é pergunta da base gera `ValueError`;
- **na tela (#10, #13, #16):** com `AppTest`, testa a fazenda-exemplo e os 4 casos conhecidos de referência. O parecer renderiza a situação destacada, cards fazenda × CONAB, gráfico do COE, causas e recomendações por CF, explicações "como cheguei aqui?" e "por que pergunto?" no formulário, expander com toda a memória de trabalho e rodapé com versão e data do snapshot.

### `test_validacao.py` (#14)
- Valida os extremos e valores fora das faixas declaradas, obrigatórios, opcionais, inteiros, números não finitos, UF e mês;
- Confere normalização sem mutação, ausência sem fato, zero explícito, diagnóstico parcial e rejeição antes da consulta ao mercado;
- Executa o app vazio até a revisão e bloqueia zero vacas injetado fora dos limites do widget; verifica correção e preservação de CF estimado;
- Verifica revalidação no callback e descarte de resultado anterior. As proteções matemáticas de divisores zero continuam cobertas por `test_indicadores.py`.

### `test_explicacao.py`
- Valida as explicações "como?" e "por quê?" derivadas do traço de inferência;
- Testa derivação da cadeia indicador -> situação com premissas avaliadas e fatos antecedentes;
- Testa visualização de fórmulas de calculados e regras mais gerais bloqueadas por conflito;
- Testa marcação de perguntas que destravam regras no formulário e com dados ausentes.

### `test_regras.py`
- Testa só a base: os fatos entram direto na memória, sem calcular indicadores. A ponta a ponta fica no `test_casos.py`;
- tabela `CASOS`: um caso por regra, com a regra que dispara e a conclusão. Causa e recomendação partem dos números (a memória de entrada não aceita conclusões) e, como têm vários valores, basta o esperado estar entre eles. **Regra nova precisa de uma linha nela**, e o `test_toda_regra_da_base_tem_caso` falha e aponta a regra que ficou sem caso;
- limiar: as comparações são estritas, e exatamente no limiar nada é concluído;
- situação: cada receita cai numa faixa só, e na marca (COE, COT ou CT) vale a faixa de cima. Sem capital investido não há CT: lucro e médio prazo não disparam, e abaixo do COT a situação sai normalmente;
- par geral × exceção: a R-IND-06 vence a R-IND-05 por ter mais condições, e a R-IND-05 fica em `bloqueadas`; a exceção não esconde o concentrado na receita, que tem conclusão própria;
- OU: CCS e CPP fora da IN 76 concluem o mesmo fato, com as duas origens;
- causas (#12): só explicam fazenda sem lucro, e sem situação (sem CT) não sai causa; a qualidade fora da IN 76 vale mesmo com lucro, e só a CCS alta recomenda controlar mastite;
- OU com CF combinado: duas evidências de custo alimentar chegam a 0,94, e a recomendação já lê esse CF (0,752); duas causas levam à mesma recomendação (0,7912); a troca leite:milho desfavorável só pesa com custo alimentar alto;
- a lista exata das regras com `fonte: "PENDENTE"`. Achou a fonte? Atualize a regra e a lista.

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

### `test_benchmark.py` (#18)
- O snapshot da PPM tem a variável, a unidade e o produto certos e as 27 UFs, e a tabela `CODIGO_UF` cobre as UFs do formulário;
- a média de MG bate com a conta à mão (`10.070.127 × 1.000 ÷ 2.963.271 ÷ 365`), em L/vaca/dia, do último ano antes do mês; UF sem dado, símbolo do SIDRA (`...`, `-`) e vacas zeradas não geram fato;
- critérios de aceite da #18: com a rede bloqueada, o caso 05 dispara a R-IND-11 (7,78 < 9,3105 L/vaca/dia) com CF 1,0.

### `test_rodada_bugs.py` (#22)
- Duas fazendas inventadas em `tests/fixtures/rodada_bugs/`, no formato de `dados/casos/`, com as contas à mão nos comentários: **A** (PR, alta produção, médio prazo, CCS acima da IN 76) e **B** (GO, familiar, prejuízo, troca leite:milho desfavorável, CPP acima da IN 76, opcionais vazios e zero explícito);
- confere mercado, indicadores (e os que não existem por falta de opcional), situação, conclusões de indicador com CF, regra bloqueada e causas e recomendações como conjunto exato com CF;
- cobertura: toda regra da base dispara ponta a ponta em algum dos 5 casos conhecidos ou das 2 fazendas. **Regra nova precisa disparar em algum caso**;
- na tela: os 7 casos são digitados no formulário, etapa por etapa, até o parecer; o motor recebe exatamente as respostas da fazenda;
- 100 fazendas aleatórias (sementes fixas) com extremos de faixa, opcionais vazios, meses fora do snapshot e valores estimados: nenhuma exceção no diagnóstico, no "como?", no "por quê?" e na simulação, e a situação bate com as faixas de Matsunaga.

## Quando um teste falhar
- **Depois de trocar a base da CONAB:** o `test_catalogo_mercado.py` aponta id que mudou de nome e valor fora da faixa, com UF, mês e valor. Se o preço for real, alargue a faixa no `mercado.yaml`.
- **Depois de trocar os snapshots do IBGE:** o `test_benchmark.py` aponta variável, unidade ou UF errada.
- **Depois de mexer no `dominio/mercado.py`:** o `test_mercado.py` mostra qual fato mudou.
- **Depois de mexer nos cálculos de fazendas ou regras:** o `test_casos.py` mostra qual caso divergiu.
- **Depois de criar ou alterar uma regra:** o `test_regras.py` mostra qual regra deixou de concluir o esperado ou ficou sem caso.
- **Depois de criar uma regra que nenhum caso dispara:** o `test_casos_e_fazendas_disparam_toda_regra_da_base` aponta a regra; ajuste um caso ou uma fazenda inventada para dispará-la.
- **Depois de mexer no `diagnosticar` ou na tela de parecer:** o `test_diagnostico.py` mostra se a memória perdeu origem ou CF, ou se a fazenda-exemplo deixou de chegar ao parecer.
