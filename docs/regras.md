# Regras de produção

Base em `conhecimento/regras.yaml`: 30 regras em 4 camadas, do dado à ação.

| Camada | Regras | O que fazem |
|---|---|---|
| indicador | R-IND-01 a R-IND-10 | comparam um número com um limiar ou com o mercado da UF (CONAB) |
| situação | R-SIT-01 a R-SIT-04 | enquadram a fazenda nas 4 faixas de Matsunaga et al. (1976) |
| causa | R-CAU-01 a R-CAU-07 | explicam o resultado da fazenda sem lucro; a qualidade (IN 76) vale sempre |
| recomendação | R-REC-01 a R-REC-09 | uma ou duas ações por causa, e a da faixa de lucro |

O catálogo abaixo é a transcrição completa de `conhecimento/regras.yaml`.
Cada linha preserva o CF e a fonte declarados na base.

## Catálogo completo

| ID | Camada | SE | ENTÃO | CF | Fonte |
|---|---|---|---|---:|---|
| R-IND-01 | indicador | `preco_leite_fazenda < $preco_leite_uf` | `preco_leite = abaixo_mercado` | 1,00 | CONAB, PrecosMensalUF: preço médio do leite ao produtor na UF |
| R-IND-02 | indicador | `pct_vacas_lactacao < 70` | `lactacao_nivel = baixa` | 1,00 | PENDENTE |
| R-IND-03 | indicador | `litros_vaca_dia < 10` | `produtividade_nivel = baixa` | 1,00 | PENDENTE |
| R-IND-04 | indicador | `pct_concentrado_receita > 40` | `concentrado_receita_nivel = alto` | 1,00 | PENDENTE |
| R-IND-05 | indicador | `pct_alimentacao_coe > 65` | `custo_alimentar_nivel = alto` | 1,00 | PENDENTE |
| R-IND-06 | indicador | `pct_alimentacao_coe > 65` e `litros_vaca_dia > 25` | `custo_alimentar_nivel = adequado` | 0,80 | PENDENTE |
| R-IND-07 | indicador | `troca_leite_milho_uf < $troca_leite_milho_uf_media_12m` | `troca_leite_milho_nivel = desfavoravel` | 1,00 | CONAB, PrecosMensalUF: relação de troca do mês contra a média de 12 meses |
| R-IND-08 | indicador | `ccs > 500` | `qualidade_leite = fora_in76` | 1,00 | MAPA, IN 76/2018: CCS máxima de 500 mil CS/mL |
| R-IND-09 | indicador | `cpp > 300` | `qualidade_leite = fora_in76` | 1,00 | MAPA, IN 76/2018: CPP máxima de 300 mil UFC/mL |
| R-IND-10 | indicador | `litros_dia_homem < 150` | `mao_obra_nivel = baixa` | 1,00 | CEPEA/Esalq (2012): mínimo de 150 L/homem/dia na ordenha manual |
| R-SIT-01 | situacao | `receita_total >= $ct` | `situacao_economica = lucro` | 1,00 | Matsunaga et al. (1976), metodologia de custo operacional |
| R-SIT-02 | situacao | `receita_total >= $cot` e `receita_total < $ct` | `situacao_economica = medio_prazo` | 1,00 | Matsunaga et al. (1976), metodologia de custo operacional |
| R-SIT-03 | situacao | `receita_total >= $coe` e `receita_total < $cot` | `situacao_economica = curto_prazo` | 1,00 | Matsunaga et al. (1976), metodologia de custo operacional |
| R-SIT-04 | situacao | `receita_total < $coe` | `situacao_economica = prejuizo` | 1,00 | Matsunaga et al. (1976), metodologia de custo operacional |
| R-CAU-01 | causa | `preco_leite == abaixo_mercado` e situação sem lucro | `causa = preco_recebido_baixo` | 0,80 | CONAB e `docs/dominio.md`, seções 3 e 7 |
| R-CAU-02 | causa | `custo_alimentar_nivel == alto` e situação sem lucro | `causa = custo_alimentar_alto` | 0,80 | CEPEA/Esalq (2012) e `docs/dominio.md`, seção 2 |
| R-CAU-03 | causa | `concentrado_receita_nivel == alto` e situação sem lucro | `causa = custo_alimentar_alto` | 0,70 | `docs/dominio.md`, seção 6.4 |
| R-CAU-04 | causa | `lactacao_nivel == baixa` e situação sem lucro | `causa = rebanho_reproducao` | 0,80 | CEPEA/Esalq (2012) e `docs/dominio.md`, seção 6.1 |
| R-CAU-05 | causa | `produtividade_nivel == baixa` e situação sem lucro | `causa = produtividade_baixa` | 0,60 | CEPEA/Esalq (2012) e `docs/dominio.md`, seção 6.2 |
| R-CAU-06 | causa | `qualidade_leite == fora_in76` | `causa = qualidade_leite` | 0,70 | MAPA, IN 76/2018 e `docs/dominio.md`, seção 3 |
| R-CAU-07 | causa | `mao_obra_nivel == baixa` e situação sem lucro | `causa = escala_baixa` | 0,70 | CNA/Cepea, Campo Futuro (03/2020) |
| R-REC-01 | recomendacao | `causa == preco_recebido_baixo` | `recomendacao = negociar_com_laticinio` | 0,80 | `docs/dominio.md`, seções 1, 3 e 7 |
| R-REC-02 | recomendacao | `causa == custo_alimentar_alto` | `recomendacao = revisar_dieta_com_nutricionista` | 0,80 | `docs/dominio.md`, seção 7 |
| R-REC-03 | recomendacao | custo alimentar alto e troca desfavorável | `recomendacao = planejar_compra_de_insumos` | 0,70 | CONAB e `docs/dominio.md`, seção 7 |
| R-REC-04 | recomendacao | `causa == produtividade_baixa` | `recomendacao = revisar_dieta_com_nutricionista` | 0,70 | CEPEA/Esalq (2012) e `docs/dominio.md`, seção 6.2 |
| R-REC-05 | recomendacao | `causa == rebanho_reproducao` | `recomendacao = manejo_reprodutivo` | 0,80 | `docs/dominio.md`, seções 1 e 7 |
| R-REC-06 | recomendacao | `causa == qualidade_leite` | `recomendacao = melhorar_higiene_ordenha` | 0,80 | MAPA, IN 77/2018 e `docs/dominio.md`, seção 3 |
| R-REC-07 | recomendacao | qualidade do leite e `ccs > 500` | `recomendacao = controlar_mastite` | 0,80 | MAPA, IN 76/2018 e `docs/dominio.md`, seção 3 |
| R-REC-08 | recomendacao | `causa == escala_baixa` | `recomendacao = avaliar_escala` | 0,70 | CEPEA/Esalq (2012) |
| R-REC-09 | recomendacao | `situacao_economica == lucro` | `recomendacao = manter_controle_e_avaliar_expansao` | 0,80 | Matsunaga et al. (1976) e `docs/dominio.md`, seção 5 |

### Como as regras foram adquiridas

1. **Extração assistida por IA:** a equipe usou IA para ler os materiais do
   hackathon, organizar o modelo do slide 14 e localizar candidatos de
   literatura. A IA não é chamada pelo sistema em execução.
2. **Especificação humana:** os candidatos foram convertidos em premissas,
   conclusões, camadas e CFs no YAML. A equipe decidiu o escopo, a semântica
   das camadas e os casos conhecidos.
3. **Revisão da base:** `carregar_base()` valida estrutura, referências,
   operadores, camadas, CF e unicidade. Alterações em `conhecimento/` devem
   passar por revisão de PR.
4. **Validação executável:** cada regra tem caso em
   [`tests/test_regras.py`](../tests/test_regras.py) ou nos casos integrados,
   e [`tests/test_casos.py`](../tests/test_casos.py) verifica as conclusões
   esperadas das fazendas de referência.

Os limiares marcados como `PENDENTE` e os CFs de causas/recomendações continuam
explicitamente aguardando validação técnica; não foram apresentados como fatos
confirmados.

## Validação com o técnico da RERUM (#12)

As regras de indicador e situação têm fonte na literatura ou nos dados da CONAB, com exceção dos limiares `PENDENTE` (R-IND-02 a R-IND-06). Já os CFs de causa e recomendação são julgamento da equipe. Por isso, as 5 regras-chave abaixo estão preparadas para consulta ao técnico, com as mesmas três perguntas para cada uma:
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
