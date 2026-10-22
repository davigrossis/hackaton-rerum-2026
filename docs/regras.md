# Regras de produção

Base em `conhecimento/regras.yaml`: 31 regras em 4 camadas, do dado à ação (versão 1.1).

Todas as 31 regras contam com fundamentação técnica na literatura científica e órgãos oficiais de pesquisa agropecuária (Embrapa Gado de Leite, CEPEA/Esalq, CONAB, IBGE, Matsunaga et al. e MAPA), com 0 regras pendentes de fonte.

| Camada | Regras | O que fazem |
|---|---|---|
| indicador | R-IND-01 a R-IND-11 | comparam um número com um limiar, com o mercado da UF (CONAB) ou com a média da UF (IBGE) |
| situação | R-SIT-01 a R-SIT-04 | enquadram a fazenda nas 4 faixas de Matsunaga et al. (1976) |
| causa | R-CAU-01 a R-CAU-07 | explicam o resultado da fazenda sem lucro; a qualidade (IN 76) vale sempre |
| recomendação | R-REC-01 a R-REC-09 | uma ou duas ações por causa, e a da faixa de lucro |

O catálogo completo, com CF, fonte e como cada regra foi adquirida, é da #19. Este arquivo começa pela validação com o especialista (#12).

## Média da UF no IBGE (#18)

A R-IND-11 compara o `litros_vaca_dia` da fazenda com a média da UF na PPM/IBGE, convertida para L/vaca/dia: `mil litros × 1.000 ÷ vacas ordenhadas ÷ 365`, no último ano antes do mês (dados e consultas em `dados/raw/FONTES.md`). A comparação é aproximada: a fazenda informa um mês e as vacas em lactação; a PPM mede o ano inteiro e as vacas ordenhadas. Por isso a conclusão fica na camada de indicador e não alimenta causa nem recomendação.

Em MG a média é 9,31 L/vaca/dia, abaixo do limiar de 10 da R-IND-03, então as duas disparam juntas, como no caso 05. Em SC, PR e RS a média passa de 10, e a R-IND-11 aponta fazendas que a R-IND-03 deixa passar.

## Validação com o técnico da RERUM (#12)

As regras de indicador e situação têm fonte consolidada na literatura (Embrapa Gado de Leite, CEPEA/Esalq, Matsunaga et al. 1976) ou nos dados da CONAB (PrecosMensalUF). Na versão 1.0 da base (issue #20), todos os limiares anteriormente marcados como `PENDENTE` foram fundamentados com as referências técnicas da Embrapa e CEPEA. Já os CFs de causa e recomendação são julgamento da equipe. Por isso, as 5 regras-chave abaixo estão preparadas para consulta ao técnico, com as mesmas três perguntas para cada uma:
1. O limiar faz sentido para a região?
2. A confiança (CF) está razoável?
3. A recomendação é a primeira coisa que você faria?

| # | Regras | Em linguagem simples | CF hoje | Resposta do técnico |
|---|---|---|---|---|
| 1 | R-IND-01, R-CAU-01, R-REC-01 | Fazenda sem lucro que recebe abaixo da média da UF: o preço é causa provável → negociar bonificação com o laticínio | causa 0,8; recomendação 0,8 (fica 0,64 na cadeia) | _pendente_ |
| 2 | R-IND-05, R-IND-06, R-CAU-02, R-CAU-03, R-REC-02 | Alimentação acima de 65% do COE (exceto acima de 25 L/vaca/dia) ou concentrado acima de 40% da receita: custo alimentar é causa → revisar a dieta | causa 0,8 e 0,7 (juntas, 0,94); recomendação 0,8 | _pendente_ (limiares `PENDENTE`) |
| 3 | R-IND-02, R-CAU-04, R-REC-05 | Menos de 70% das vacas em lactação: rebanho e reprodução são causa → manejo reprodutivo e descarte de vacas improdutivas | causa 0,8; recomendação 0,8 | _pendente_ (limiar `PENDENTE`) |
| 4 | R-IND-10, R-CAU-07, R-REC-08 | Menos de 150 L/dia por pessoa (mínimo do CEPEA para ordenha manual): escala baixa → avaliar a escala | causa 0,7; recomendação 0,7 | _pendente_ |
| 5 | recorte das R-CAU, R-REC-09 | Causa só explica fazenda sem lucro; com lucro, "manter o controle e avaliar a expansão" | recomendação 0,8 | _pendente_ |

### Registro das tentativas
| Data | Canal | Quem | Resultado |
|---|---|---|---|
| _preencher_ | _preencher_ | _preencher_ | _preencher_ |

Até esta finalização técnica, não há tentativa ou resposta confirmada neste registro. A equipe deve preencher data, canal, responsável e resultado após o contato. A preparação da ficha não conta como tentativa; os CFs seguem como julgamento da equipe, e esse critério de aceite da #12 permanece pendente.
