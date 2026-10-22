# Plano B — Guia Visual de Contingência da Apresentação

> **Finalidade:** Servir como backup visual completo da demonstração de 15 minutos caso ocorra falha de hardware, monitor ou projetor durante a banca examinadora do Hackathon UFJF 2026.  
> **Uso:** Este documento contém o espelho fiel de todas as telas, tabelas e explicações geradas pelo sistema em tempo real para os 2 perfis de fazenda e a simulação.

---

## 1. Tela Inicial e Base de Conhecimento (Bloco 2)

### Visão Geral da Interface:
- **Barra lateral:** Navegação entre `"Diagnóstico"` e `"Base de conhecimento"`, seletores de exemplos conhecidos (`01_lucro`, `02_medio_prazo`, `03_curto_prazo_alimentacao`, `04_prejuizo_preco_reproducao`, `05_benchmark_ibge`) e resumo de progresso.
- **Cabeçalho:** *Diagnóstico Econômico da Atividade Leiteira · Hackathon UFJF 2026*.

### Tabela da Base de Conhecimento v1.0:
| Camada | Regra | Premissas (SE) | Conclusão (ENTÃO) | CF | Fonte Técnica |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **indicador** | `R-IND-01` | `preco_leite_fazenda < $preco_leite_uf` | `preco_leite = abaixo_mercado` | 1,0 | CONAB, PrecosMensalUF |
| **indicador** | `R-IND-02` | `pct_vacas_lactacao < 70` | `lactacao_nivel = baixa` | 1,0 | Embrapa Gado de Leite (2021) |
| **indicador** | `R-IND-03` | `litros_vaca_dia < 10` | `produtividade_nivel = baixa` | 1,0 | Embrapa Gado de Leite (2021) / CEPEA |
| **indicador** | `R-IND-04` | `pct_concentrado_receita > 40` | `concentrado_receita_nivel = alto` | 1,0 | Embrapa Gado de Leite (2021) |
| **indicador** | `R-IND-05` | `pct_alimentacao_coe > 65` | `custo_alimentar_nivel = alto` | 1,0 | CEPEA/Esalq (2012) / Embrapa |
| **indicador** | `R-IND-06` | `pct_alimentacao_coe > 65` E `litros_vaca_dia > 25` | `custo_alimentar_nivel = adequado` | 0,8 | Embrapa Gado de Leite (2021) / CEPEA *(Exceção)* |
| **indicador** | `R-IND-10` | `litros_dia_homem < 150` | `mao_obra_nivel = baixa` | 1,0 | CEPEA/Esalq (2012) |
| **indicador** | `R-IND-11` | `litros_vaca_dia < $produtividade_regional_ibge` | `produtividade_regional_nivel = abaixo` | 1,0 | IBGE – PPM, tabelas 74 e 94 |
| **situacao** | `R-SIT-01` | `receita_total >= $ct` | `situacao_economica = lucro` | 1,0 | Matsunaga et al. (1976) |
| **situacao** | `R-SIT-02` | `receita_total >= $cot` E `receita_total < $ct` | `situacao_economica = medio_prazo` | 1,0 | Matsunaga et al. (1976) |
| **situacao** | `R-SIT-03` | `receita_total >= $coe` E `receita_total < $cot` | `situacao_economica = curto_prazo` | 1,0 | Matsunaga et al. (1976) |
| **situacao** | `R-SIT-04` | `receita_total < $coe` | `situacao_economica = prejuizo` | 1,0 | Matsunaga et al. (1976) |
| **causa** | `R-CAU-01` | sem lucro E `preco_leite == abaixo_mercado` | `causa = preco_desfavoravel` | 0,8 | Análise de mercado CONAB |
| **causa** | `R-CAU-04` | sem lucro E `lactacao_nivel == baixa` | `causa = falha_reprodutiva` | 0,8 | Manejo reprodutivo Embrapa |
| **causa** | `R-CAU-07` | sem lucro E `mao_obra_nivel == baixa` | `causa = escala_baixa` | 0,7 | CEPEA/Esalq (2012) |

---

## 2. Formulário Inteligente e Explicabilidade Prévia (Bloco 3)

### Detalhe do Popover "Por que a pergunta?":
```text
┌────────────────────────────────────────────────────────────────────────┐
│ [?] Por que pergunto sobre 'custo_concentrado'?                       │
│ ---------------------------------------------------------------------- │
│ Esta informação é necessária para:                                    │
│ • Calcular o 'custo_alimentar' e o 'coe' (Custo Operacional Efetivo)   │
│ • Avaliar a proporção de concentrado na receita bruta                  │
│ • Acionar a regra R-IND-04 (concentrado consome mais de 40% da receita)│
│ • Acionar a regra R-IND-05 (alimentação consome mais de 65% do COE)   │
└────────────────────────────────────────────────────────────────────────┘
```

### Funcionalidade de "Valor estimado":
- **Checkbox:** `[x] Valor estimado (reduz CF para 70%)`
- **Comportamento matemático:** A memória marca o fato com `Origem(tipo='usuario', detalhe='estimado', cf=0.7)`. Variáveis calculadas que dependem deste fato herdam `cf=0.7` (regra D7), sinalizando na tela `(estimado · CF 70%)`.

---

## 3. Fazenda 1: Saudável — Caso 01 (Bloco 4)

### Resumo das Entradas:
- **UF / Mês:** MG, 09/2026 | **Área:** 40 ha | **Mão de obra:** 2 pessoas
- **Rebanho:** 40 vacas em lactação, 8 secas (83,3% em lactação)
- **Produção:** 30.000 L/mês (28,0 L/vaca/dia) | **Preço recebido:** R$ 3,10/L
- **Desembolsos (COE):** R$ 57.000 (Concentrado R$ 25.000; Volumoso R$ 13.300; Outros R$ 18.700)
- **COT:** R$ 72.000 (Depreciação R$ 5.000; Pró-labore R$ 10.000)
- **CT:** R$ 77.000 (Capital R$ 1.000.000 com taxa de juros de 6% a.a. = R$ 5.000)
- **Receita Total:** R$ 93.000 (Leite R$ 93.000 + Outras R$ 0)

### Cartão de Situação Econômica (Verde):
```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ SITUAÇÃO ECONÔMICA: LUCRO SUPERAVITÁRIO (CF 100%)                             │
│ A receita cobre todos os custos operacionais e a remuneração do capital.      │
│                                                                               │
│ • Receita Total: R$ 93.000,00         • COE: R$ 57.000,00 (R$ 1,90/L)        │
│ • Margem Bruta:  +R$ 36.000,00        • COT: R$ 72.000,00 (R$ 2,40/L)        │
│ • Margem Líquida: +R$ 21.000,00       • CT:  R$ 77.000,00 (R$ 2,57/L)        │
│ • Lucro Econômico: +R$ 16.000,00                                              │
└───────────────────────────────────────────────────────────────────────────────┘
```

### O Conflito Resolvido — "Como cheguei aqui?":
```text
▼ Como cheguei aqui? (R-IND-06 — Exceção de alta produtividade)
  • Regra disparada: R-IND-06
  • Descrição: Exceção da R-IND-05; acima de 25 L/vaca/dia, a alta produção dilui o custo alimentar
  • Fonte: Embrapa Gado de Leite (2021) / CEPEA
  • Premissas satisfeitas:
    - pct_alimentacao_coe (67.19%) > 65% [VERDADEIRO]
    - litros_vaca_dia (28.00 L/vaca/dia) > 25 [VERDADEIRO]
  • Conclusão gerada: custo_alimentar_nivel = adequado (CF 80%)
  • Conflitos e regras bloqueadas:
    - R-IND-05 (regra geral que concluiria custo_alimentar_nivel = alto) BLOQUEADA POR ESPECIFICIDADE
```

### Cards CONAB e Benchmark IBGE:
- **Preço Fazenda × CONAB:** R$ 3,10/L vs R$ 3,04/L (+2,0% em relação à média estadual de MG).
- **Produtividade Fazenda × IBGE:** 28,00 L/vaca/dia vs 9,31 L/vaca/dia (+200,7% acima da média estadual de MG na PPM 2025).

---

## 4. O Diálogo Interativo do Motor (Bloco 5)

Quando o usuário submete o formulário com dados opcionais ausentes que poderiam completar regras quase satisfeitas:

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ ⚠ O motor precisa de mais um dado                                            │
│ Essas informações são opcionais, mas podem completar uma regra que já está    │
│ quase satisfeita na base de conhecimento.                                     │
│                                                                               │
│ ┌─ Contagem de Células Somáticas (CCS em mil CS/mL) ────────────────────────┐ │
│ │ ℹ Porque a regra R-IND-08 pode concluir que a qualidade do leite está     │ │
│ │   fora do padrão da IN 76/77 do Ministério da Agricultura (limite 500).   │ │
│ │ [ Digite o valor de CCS...                              ]                 │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│ [ Continuar diagnóstico ]                                                     │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Fazenda 2: Em Crise — Caso 04 (Bloco 5)

### Resumo das Entradas:
- **UF / Mês:** MG, 09/2026 | **Área:** 45 ha | **Mão de obra:** 3 pessoas
- **Rebanho:** 30 vacas em lactação, 20 secas (60,0% em lactação — alerta grave)
- **Produção:** 9.000 L/mês (10,0 L/vaca/dia) | **Preço recebido:** R$ 2,50/L
- **Desembolsos (COE):** R$ 30.000,00 | **Receita Total:** R$ 22.500,00
- **Margem Bruta:** -R$ 7.500,00 | **Margem Líquida:** -R$ 16.500,00 | **Lucro:** -R$ 20.500,00

### Cartão de Situação Econômica (Vermelho):
```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ SITUAÇÃO ECONÔMICA: PREJUÍZO (CF 100%)                                       │
│ A receita bruta não cobre sequer os desembolsos diretos do mês (COE).         │
│ A fazenda opera em sangria de caixa operacional imediata.                     │
│                                                                               │
│ • Receita Total: R$ 22.500,00         • COE: R$ 30.000,00 (R$ 3,33/L)        │
│ • Margem Bruta:  -R$ 7.500,00         • COT: R$ 39.000,00 (R$ 4,33/L)        │
│ • Margem Líquida: -R$ 16.500,00       • CT:  R$ 43.000,00 (R$ 4,78/L)        │
│ • Lucro Econômico: -R$ 20.500,00                                              │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Causas e Recomendações Diagnosticadas pelo Motor:
1. **Preço recebido desfavorável (CF 80%):** R$ 2,50/L recebido na fazenda está 17,8% abaixo da média de R$ 3,04 da CONAB para MG.
   - *Recomendação:* Negociar bonificação com o laticínio por volume, teor de sólidos ou pesquisar compradores alternativos na região.
2. **Falha reprodutiva do rebanho (CF 80%):** Apenas 60% do rebanho está em lactação (ideal: 80% a 85%). Há 20 vacas secas consumindo insumos sem produzir leite.
   - *Recomendação:* Revisar protocolo reprodutivo, intervalo entre partos e descartar matrizes cronicamente inférteis ou improdutivas.
3. **Escala baixa de mão de obra (CF 70%):** Produtividade de 100 L/dia por trabalhador, abaixo do limiar de 150 L/dia fixado pelo CEPEA/Esalq (2012).
   - *Recomendação:* Avaliar adequação do quadro de pessoal e rotinas de ordenha.

---

## 6. Simulação "E se?" ao Vivo (Bloco 6)

### Controles Interativos:
```text
[ Preço do leite:  +15% ]        [ Custo concentrado: -10% ]        [ Produção: 0% ]
```

### Resultado Recalculado pelo Motor em Tempo Real:
```text
┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
│ Situação original                    │  │ Situação simulada                    │
│ PREJUÍZO                             │  │ CURTO PRAZO                          │
└──────────────────────────────────────┘  └──────────────────────────────────────┘
✓ A variação cruzou um limiar e mudou a situação econômica da fazenda.
```
- **Explicação ao Produtor:** Ao negociar o preço em +15% (R$ 2,87/L) e otimizar o concentrado em 10% (economia de R$ 630), a receita sobe para R$ 25.875 e o COE cai para R$ 29.370, permitindo vislumbrar o ponto de equilíbrio para sair da insolvência.
