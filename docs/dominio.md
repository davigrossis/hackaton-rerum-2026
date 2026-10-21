# Contexto de Negócio e Domínio: Diagnóstico Econômico da Atividade Leiteira

Documento técnico do tema **T3 (Economia)** do Hackathon UFJF 2026. Fundamenta o contexto de negócio, a metodologia de custeio, os indicadores zootécnicos e as bases normativas que orientam a base de conhecimento e as regras do sistema especialista.

---

## 1. Quem usa e que decisão toma

### Usuários-alvo
1. **Produtor de leite** (agricultura familiar e médios produtores): busca saber se a atividade está pagando as contas do mês, mantendo seu patrimônio ou consumindo seu capital.
2. **Técnico de assistência técnica e extensão rural (ATER)**: utiliza o parecer como ferramenta de diagnóstico padronizada em visitas mensais, auxiliando na orientação de manejo e gestão econômica.

### Decisões tomadas
- **Curto prazo (mensal):** ajustar compra de concentrado, rever manejo alimentar, buscar bonificações junto ao laticínio ou renegociar preço da matéria-prima.
- **Médio prazo (semestral/anual):** readequar taxa de lotação, descartar vacas improdutivas, planejar silagem/estoques para a seca e programar cobertura/inseminação.
- **Longo prazo:** decidir pela continuidade, expansão, troca de sistema de produção (pasto vs. confinamento) ou desinvestimento na atividade.

---

## 2. As dores da atividade leiteira

A bovinocultura de leite no Brasil opera com margens estreitas e elevada vulnerabilidade a choques externos:
1. **Margem por litro comprimida:** a diferença entre o preço recebido por litro e o custo de produção frequentemente oscila próxima de zero ou negativa.
2. **Volatilidade de preços e sazonalidade climática:**
   - Na época das chuvas (safra / verão), a produção nacional cresce com a disponibilidade de pastagens e o preço pago pelo laticínio cai.
   - Na época da seca (entressafra / outono-inverno), a oferta recua, os custos com alimentação sobem e o preço do leite tende a subir.
   - *Exemplo real observado em Minas Gerais (CONAB, 10/2025 a 09/2026):* o leite ao produtor foi de **R$ 2,11/L em 01/2026** (mínima nas chuvas) para **R$ 3,04/L em 09/2026** (máxima na seca), uma oscilação de **+44,1%** no mesmo ano.
3. **Custo alimentar como principal componente do desembolso:**
   - A alimentação do rebanho (concentrado proteico/energético, volumoso suplementar e sal mineral) responde tipicamente por **40% a 70% do Custo Operacional Efetivo (COE)**.
   - O preço do milho e do farelo de soja oscila no mercado de commodities independentemente do preço do leite na porteira.
4. **Relação de troca leite:milho volátil:**
   - Mede quantos quilogramas de milho o produtor consegue adquirir com o valor de 1 litro de leite entregue.
   - Em MG (2025/2026), essa relação oscilou entre **1,97 kg/L (01/2026)** e **3,11 kg/L (08/2026)**, impactando brutalmente o poder de compra de insumos.
5. **Dificuldade na apuração de custos indiretos:**
   - Produtores frequentemente confundem fluxo de caixa (sobra de dinheiro no mês) com lucro econômico real, negligenciando a depreciação de maquinários/benfeitorias e o valor do próprio trabalho familiar (pró-labore).

---

## 3. Como o leite é pago: volume e qualidade (IN 76/2018 e IN 77/2018)

O faturamento da fazenda leiteira decorre do volume entregue somado a bonificações ou penalizações por qualidade e escala:

### Parâmetros normativos oficiais (MAPA - Instruções Normativas 76 e 77 de 2018)
O leite cru refrigerado deve atender a critérios higiênico-sanitários obrigatórios:
- **Contagem de Células Somáticas (CCS):** limite máximo de **500.000 CS/mL** (média geométrica trimestral). É o principal indicador de saúde da glândula mamária do rebanho (mastite).
- **Contagem Padrão em Placas (CPP):** limite máximo de **300.000 UFC/mL** (média geométrica trimestral). Reflete a higiene de ordenha, limpeza do tanque de resfriamento e conservação térmica.
- **Teores mínimos de sólidos:** Gordura mínima de 3,0 g/100g e Proteína total mínima de 2,9 g/100g.
- **Ausência de resíduos:** proibição rigorosa de inibidores e antibióticos.

### Impacto financeiro no preço
- **Bonificações:** laticínios pagam adicionais por CCS reduzida (ex.: < 250 mil CS/mL), sólidos elevados e grandes volumes diários (escala de coleta).
- **Penalizações / Descontos:** leite com CCS ou CPP fora do padrão legal sofre descontos diretos por litro ou recusa de carregamento.

---

## 4. Metodologia de Custo de Produção (Matsunaga et al., 1976 / Embrapa / CEPEA)

O sistema adota a metodologia de Custo Operacional consagrada pelo Instituto de Economia Agrícola (IEA/SP) por Matsunaga et al. (1976), amplamente aplicada pela Embrapa Gado de Leite e pelo CEPEA/Esalq:

```
Custos Desembolsados (Insumos, Mão de Obra Contratada, Serviços, Energia)
    │
    ▼
[ Custo Operacional Efetivo - COE ]
    │
    │ + Depreciação de máquinas, benfeitorias e forragens
    │ + Remuneração da Mão de Obra Familiar (Pró-labore)
    ▼
[ Custo Operacional Total - COT ]
    │
    │ + Remuneração do Capital Investido (taxa de juros de oportunidade)
    │ + Custo de Oportunidade da Terra
    ▼
[ Custo Total - CT ]
```

### Componentes de Custo
1. **COE (Custo Operacional Efetivo):** todos os gastos que implicam desembolso financeiro direto no mês:
   - Alimentação: concentrado (ração comercial, milho, farelo de soja), volumoso conservado (silagem, feno), pastagem anual e sal mineral.
   - Mão de obra contratada (salários + encargos).
   - Sanidade e reprodução (vacinas, medicamentos, sêmen, nitrogênio, exames).
   - Energia elétrica e combustíveis (óleo diesel de tratores/geradores).
   - Frete, manutenção de equipamentos e despesas administrativas diversas.
2. **COT (Custo Operacional Total):**
   - $\text{COT} = \text{COE} + \text{Depreciação} + \text{Pró-labore}$
   - *Depreciação:* reserva contábil para reposição do desgaste de máquinas, tratores, ordenhadeira, tanque e benfeitorias ao final de sua vida útil.
   - *Pró-labore:* remuneração estimada pelo tempo de trabalho dedicado pelo produtor e sua família à lida diária.
3. **CT (Custo Total):**
   - $\text{CT} = \text{COT} + \text{Remuneração do Capital}$
   - *Remuneração do Capital:* custo de oportunidade do capital empatado em animais, máquinas e instalações, calculado com base em uma taxa de juros de oportunidade (ex.: taxa de poupança ou taxa real de 6% a.a., equivalente a 0,5% a.m.).

### Indicadores Financeiros Derivados
- **Receita Total:** faturamento com venda de leite ($\text{Produção (L)} \times \text{Preço Recebido (R\$/L)}$) somado a outras receitas do mês (venda de animais descartados, esterco, etc.).
- **Margem Bruta (R\$):** $\text{Receita Total} - \text{COE}$
- **Margem Líquida (R\$):** $\text{Receita Total} - \text{COT}$
- **Lucro Econômico (R\$):** $\text{Receita Total} - \text{CT}$
- **Custo por Litro:**
  - $\text{COE/litro} = \text{COE} / \text{Produção de Leite}$
  - $\text{COT/litro} = \text{COT} / \text{Produção de Leite}$
  - $\text{CT/litro} = \text{CT} / \text{Produção de Leite}$

---

## 5. As 4 Situações Econômicas da Fazenda

Com base na comparação entre a Receita Total e as três camadas de custo (COE, COT, CT), a fazenda é classificada em uma das quatro situações econômicas:

| Situação | Critério Matemático | Diagnóstico e Sustentabilidade |
|---|---|---|
| **Lucro** (Viável a Longo Prazo) | $\text{Receita} \ge \text{CT}$ | A atividade paga todos os custos operacionais, remunera o trabalho da família e remunera o capital investido com sobras. Há lucro econômico real; a propriedade é sustentável e tem capacidade de expansão e reinvestimento. |
| **Médio Prazo** (Estável no Médio Prazo) | $\text{COT} \le \text{Receita} < \text{CT}$ | A receita cobre os desembolsos imediatos e a reposição do patrimônio (depreciação e pró-labore), mas a remuneração do capital investido é inferior ao mercado. O produtor se mantém na atividade, mas seu capital rende menos que uma aplicação segura. |
| **Curto Prazo** (Alerta de Descapitalização) | $\text{COE} \le \text{Receita} < \text{COT}$ | A fazenda cobre o caixa mensal do dia a dia, mas **não cobre a depreciação nem remunera adequadamente a família**. A propriedade está se descapitalizando: quando máquinas ou matrizes quebrarem, não haverá reserva para reposição. |
| **Prejuízo** (Inviabilidade Imediata) | $\text{Receita} < \text{COE}$ | A receita não cobre sequer os desembolsos diretos de insumos e mão de obra. A cada litro produzido, a propriedade queima caixa ou acumula dívidas bancárias e com fornecedores. Situação crítica que exige intervenção imediata. |

---

## 6. Indicadores Zootécnicos e de Eficiência Produtiva

Fórmulas e referências técnicas recomendadas pela literatura especializada (Embrapa Gado de Leite / CEPEA):

1. **Porcentagem de vacas em lactação:**
   - $\text{\% Lactação} = \frac{\text{Vacas em Lactação}}{\text{Vacas em Lactação} + \text{Vacas Secas}} \times 100$
   - *Referência zootécnica:* ideal entre **80% e 85%** (Embrapa).
   - *Alerta:* abaixo de 70% aponta falhas reprodutivas graves (intervalo entre partos excessivo, atraso na inseminação ou retenção de vacas improdutivas).
2. **Produtividade média por vaca em lactação:**
   - $\text{Litros/vaca/dia} = \frac{\text{Produção Mensal (L)}}{\text{Vacas em Lactação} \times 30}$
   - *Referência:* varia com o sistema (animais a pasto vs confinamento), mas produções abaixo de 10 a 12 L/vaca/dia com concentrado comercial indicam conversão alimentar ineficiente.
3. **Participação da alimentação no COE:**
   - $\text{\% Alimentação no COE} = \frac{\text{Custo de Concentrado} + \text{Volumoso} + \text{Mineral}}{\text{COE}} \times 100$
   - *Referência:* faixa saudável entre **40% e 65%**. Acima de 68% a 70% indica sobrecusto alimentar ou desperdício de ração (exceto rebanhos de altíssima produtividade onde a escala compensa).
4. **Participação do concentrado na receita:**
   - $\text{\% Concentrado na Receita} = \frac{\text{Custo de Concentrado}}{\text{Receita Total}} \times 100$
   - *Referência:* ideal abaixo de **30% a 35%**. Quando o concentrado consome mais de 40% da receita bruta, a margem para cobrir mão de obra e outros custos fica seriamente comprometida.
5. **Produtividade da terra e da mão de obra:**
   - $\text{Litros/ha} = \text{Produção Mensal} / \text{Área (ha)}$
   - $\text{Litros/dia-homem} = \text{Produção Diária} / \text{Trabalhadores}$

---

## 7. As 3 Perguntas que o Sistema Responde

A estrutura de regras em camadas espelha diretamente as três indagações do produtor:

1. **"Tenho lucro?"**
   - Respondida pela camada `situacao`: compara a Receita com COE, COT e CT e enquadra em uma das 4 faixas com CF 1.0.
2. **"Por quê?"**
   - Respondida pelas camadas `indicador` e `causa`:
     - *Preço:* a fazenda recebe abaixo da média estadual no mesmo mês (`preco_leite = abaixo_mercado`)?
     - *Alimentação:* o concentrado está pesado demais para a produtividade obtida?
     - *Reprodução:* o percentual de vacas secas no rebanho está excessivo?
     - *Qualidade:* há penalização por contagem bacteriana ou celular fora da IN 76?
3. **"O que faço?"**
   - Respondida pela camada `recomendacao`: ações práticas sugeridas (negociar com o laticínio bonificações por qualidade/volume, readequar a formulação da ração com nutricionista, descartar vacas com longo período de serviço, planejar estoque de milho em momento favorável de troca).

---

## 8. Glossário

- **COE:** Custo Operacional Efetivo. Gastos desembolsados diretamente em dinheiro no mês.
- **COT:** Custo Operacional Total. COE acrescido das cotas de depreciação de bens duráveis e da remuneração familiar (pró-labore).
- **CT:** Custo Total. COT acrescido da remuneração do capital empatado e da terra.
- **Margem Bruta:** Receita menos COE. Se negativa, a fazenda fecha no vermelho imediato.
- **Margem Líquida:** Receita menos COT. Se positiva, a fazenda remunera a reposição de suas máquinas e a família.
- **CCS:** Contagem de Células Somáticas por mililitro (células de defesa e descamação).
- **CPP:** Contagem Padrão em Placas por mililitro (bactérias viáveis).
- **Relação de Troca Leite:Milho:** quilogramas de grão de milho que podem ser comprados com a venda de um litro de leite na fazenda ou no mercado estadual.

---

## 9. Referências Bibliográficas

1. **Matsunaga, M. et al.** (1976). *Metodologia de custo de produção utilizado pelo IEA.* Agricultura em São Paulo, v. 23, n. 1, p. 123-139.
2. **Embrapa Gado de Leite.** (2021). *Gestão Econômica da Propriedade Leiteira: Conceitos e Metodologia.* Coleção Sistema de Produção, Juiz de Fora: Embrapa Gado de Leite.
3. **Ministério da Agricultura, Pecuária e Abastecimento (MAPA).** (2018). *Instrução Normativa nº 76, de 26 de novembro de 2018* (Regulamento técnico de fixação de identidade e qualidade do leite cru refrigerado).
4. **Ministério da Agricultura, Pecuária e Abastecimento (MAPA).** (2018). *Instrução Normativa nº 77, de 26 de novembro de 2018* (Critérios de controle de qualidade e boas práticas na produção de leite).
5. **CEPEA / Esalq-USP.** *Metodologia de Custos de Produção da Pecuária de Leite no Brasil.* Piracicaba: CEPEA.
6. **CONAB - Companhia Nacional de Abastecimento.** *Série Histórica de Preços Agropecuários Mensais por UF.* Portal de Informações Agropecuárias.
