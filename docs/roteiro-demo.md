# Roteiro da Demonstração Técnica — Hackathon UFJF 2026 (Tema T3: Economia)

> **Duração planejada:** 15 minutos  
> **Data e hora da apresentação:** Sexta-feira, 23/10/2026 às 09h00  
> **Ambiente:** 100% localhost, sem internet (Wi-Fi desativado)  
> **Critério de aceite:** 2 ensaios cronometrados registrados  

---

## 1. Grade de Tempo e Divisão da Apresentação (15 minutos)

| Bloco | Minutos | Etapa da Demonstração | Ação Principal na Tela | Foco Técnico / Domínio |
| :---: | :---: | :--- | :--- | :--- |
| **1** | **00:00 – 02:30** | **Abertura, Desafio T3 e Arquitetura** | Slide de abertura e terminal com testes offline (`pytest`) | Desafio econômico do leite, **regra inegociável de 0 LLM no app**, arquitetura desacoplada em 4 camadas e 278 testes. |
| **2** | **02:30 – 04:30** | **Base de Conhecimento v1.0 e Motor** | Aba lateral: `"Base de conhecimento"` | 4 camadas de regras, fundamentação técnica (Embrapa, CEPEA, MAPA IN 76/77) e modelo MYCIN de cálculo de CF. |
| **3** | **04:30 – 06:30** | **Formulário, Incerteza e Explicabilidade Prévia** | Aba `"Diagnóstico"`: navegação pelas 6 etapas | Popover explicativo *"Por que pergunto?"*, tratamento rigoroso de campos opcionais e marcação de *"Valor estimado"* (CF 70%). |
| **4** | **06:30 – 10:00** | **Fazenda 1: Saudável e Resolução de Conflito** | Carregar Caso 01 (Lucro) e gerar parecer | Enquadramento Matsunaga (Lucro), **resolução de conflito ao vivo** (`R-IND-06` vence `R-IND-05`), rastreabilidade no *"Como cheguei aqui?"*, benchmark CONAB e IBGE. |
| **5** | **10:00 – 13:00** | **Fazenda 2: Em Crise e Diálogo do Motor** | Formulário Caso 04 (Prejuízo) com dados parciais | **Diálogo interativo** (*"O motor precisa de mais um dado"*), parecer em Prejuízo, causas ranqueadas por CF e recomendações práticas. |
| **6** | **13:00 – 15:00** | **Simulação "E se?", Auditoria e Conclusão** | Seção de Simulação e expander da Memória | Sliders dinâmicos revertendo a situação econômica em tempo real, auditoria de todos os fatos e encerramento. |

---

## 2. Roteiro Detalhado Bloco a Bloco

### Bloco 1: Abertura, Desafio T3 e Arquitetura (00:00 – 02:30)

- **Quem fala:** Integrante 1 (Abertura e Arquitetura).
- **Ação na tela:** Exibir o app Streamlit aberto em `localhost:8501` e um terminal mostrando a execução limpa dos 278 testes offline (`pytest -q`).
- **Fala sugerida:**
  > "Bom dia à banca examinadora. Nosso projeto aborda o Tema T3: Análise econômica e financeira da atividade leiteira com dados zootécnicos e custos de insumos.
  >
  > A pecuária leiteira no Brasil é uma atividade de margens estreitas: a alimentação pode representar até 65% dos desembolsos operacionais, e a volatilidade do preço do leite e do milho frequentemente empurra fazendas para a insolvência sem que o produtor perceba com antecedência.
  >
  > Cumprindo a regra inegociável do edital, **a inteligência do nosso sistema não é uma LLM**. Não há chamadas a APIs na nuvem nem modelos de linguagem gerando alucinações. Implementamos um **sistema especialista clássico, auditável e 100% determinístico**, rodando inteiramente em localhost sem internet.
  >
  > Nossa arquitetura divide-se estritamente em quatro camadas desacopladas: a Interface Streamlit, o Domínio com cálculos zootécnicos e dados locais da CONAB e do IBGE, o Motor de inferência progressivo com cálculo de fatores de certeza (MYCIN), e a Base de Conhecimento explícita versionada em YAML. Toda a aplicação é respaldada por contratos formais e 278 testes automatizados."

---

### Bloco 2: Base de Conhecimento v1.0 e Motor Simbólico (02:30 – 04:30)

- **Quem fala:** Integrante 2 (Conhecimento e Engenharia de IA).
- **Ação na tela:** Clicar na barra lateral e selecionar a página **"Base de conhecimento"**. Percorrer a tabela de regras de produção e os cartões das camadas.
- **Fala sugerida:**
  > "Aqui na página da Base de Conhecimento, qualquer técnico ou produtor pode inspecionar 100% da lógica que governa as decisões do sistema. Nossa base está consolidada na versão 1.0, com 30 regras de produção estratificadas em quatro camadas determinísticas:
  >
  > 1. **Indicadores:** 11 regras que cruzam métricas da fazenda com cotações da CONAB e o benchmark de produtividade da PPM/IBGE.
  > 2. **Situação Econômica:** 4 regras baseadas na consagrada metodologia de Matsunaga et al. (1976), classificando a fazenda em Lucro, Médio Prazo, Curto Prazo ou Prejuízo.
  > 3. **Causas Prováveis:** 7 regras que diagnosticam gargalos específicos quando a fazenda opera sem lucro.
  > 4. **Recomendações:** 9 regras práticas de manejo nutricional, reprodutivo e comercial.
  >
  > Todas as 30 regras contam com fontes científicas consolidadas: Embrapa Gado de Leite, CEPEA/Esalq e Instruções Normativas 76 e 77 do MAPA. Não há limiares arbitrários.
  >
  > Além disso, o motor implementa o modelo de Fatores de Certeza do MYCIN: evidências independentes combinam incerteza pela fórmula $CF = CF_1 + CF_2 \cdot (1 - CF_1)$, garantindo que múltiplas evidências convirjam confiavelmente para o diagnóstico."

---

### Bloco 3: Formulário Inteligente, "Por que pergunto?" e Incerteza (04:30 – 06:30)

- **Quem fala:** Integrante 3 (Interface e Experiência do Produtor).
- **Ação na tela:** Voltar para a página **"Diagnóstico"**. Navegar pelas etapas do formulário ("Geral", "Rebanho", "Produção & Preço", "Custos de Alimentação"). Clicar no popover explicativo *"Por que pergunto?"* na variável de concentrado e mostrar a opção de *"Valor estimado"*.
- **Fala sugerida:**
  > "Na tela de Diagnóstico, dividimos a coleta em 6 etapas ergonômicas para que o produtor não se sinta sobrecarregado por uma planilha massiva.
  >
  > Um diferencial crucial de transparência é o **'Por que pergunto?'**: ao lado de perguntas críticas como gastos com concentrado ou vacas secas, o usuário pode abrir o popover e ver exatamente quais conclusões econômicas o motor pretende derivar com aquela informação. O sistema explica sua necessidade antes mesmo de o dado ser digitado.
  >
  > Outro aspecto essencial de campo é o botão **'Valor estimado (CF 70%)'**: se o produtor não tiver a nota fiscal exata do adubo ou do mineral no momento da consulta, ele marca o valor como estimado. O motor reduz a confiança daquela entrada para 0,7 e propaga essa incerteza matematicamente por toda a árvore de cálculo até o parecer executivo, alertando o técnico sobre onde residem as dúvidas."

---

### Bloco 4: Fazenda 1 — Saudável e Resolução de Conflito ao Vivo (06:30 – 10:00)

- **Quem fala:** Integrante 1 (Análise do Caso 01) e Integrante 2 (Mecânica de Inferência).
- **Ação na tela:** Selecionar o exemplo predefinido **"Caso 01 — Lucro"** na barra lateral e avançar até o parecer executivo gerado.
- **Fala sugerida:**
  > *(Integrante 1)*: "Vejamos nossa primeira propriedade: uma fazenda tecnificada em Minas Gerais, com 40 vacas em lactação produzindo 30.000 litros/mês — média de 28 litros por vaca ao dia.
  >
  > A receita total de R$ 93.000 cobre com sobra o Custo Operacional Efetivo (R$ 57.000), o Custo Operacional Total (R$ 72.000) e o Custo Total com a remuneração de 6% ao ano do capital investido (R$ 77.000). A fazenda gera R$ 16.000 de lucro superavitário no mês, enquadrada com destaque verde na faixa de Lucro de Matsunaga.
  >
  > Os cartões confrontam os dados locais com a CONAB: o leite recebido a R$ 3,10/L supera em 2% a média estadual de MG (R$ 3,04/L). E o benchmark IBGE confirma: a média regional é de 9,31 L/vaca/dia, e a fazenda entrega o triplo da eficiência estadual.
  >
  > *(Integrante 2)*: Agora, observem o ponto mais sofisticado de IA Simbólica do nosso sistema: a **resolução de conflito por especificidade**.
  >
  > O custo alimentar desta fazenda consome 67,2% do COE — acima do limiar padrão de 65%. Pela regra geral `R-IND-05`, o sistema deveria alertar que o custo alimentar é excessivo.
  >
  > Contudo, a regra de exceção `R-IND-06` avalia duas condições conjuntas: custo alimentar acima de 65% E produtividade acima de 25 L/vaca/dia. Ambas as regras têm prioridade 50, mas a regra de exceção tem mais premissas atendidas.
  >
  > Ao abrirmos o expander **'Como cheguei aqui?'** no parecer, vemos a regra `R-IND-06` ativa, concluindo custo alimentar *adequado* com CF 0,8, e a regra geral `R-IND-05` explicitamente documentada no campo de **regras bloqueadas**. O motor não mascara o conflito: ele o resolve com rastreabilidade auditável para o especialista."

---

### Bloco 5: Fazenda 2 — Em Crise e Diálogo Guiado pelo Motor (10:00 – 13:00)

- **Quem fala:** Integrante 3 (Demonstração do Diálogo) e Integrante 1 (Diagnóstico Crítico).
- **Ação na tela:** Clicar em "Limpar", carregar o **"Caso 04 — Prejuízo"** deixando campos opcionais de sanidade (CCS e CPP) vazios, e clicar em "Gerar diagnóstico".
- **Fala sugerida:**
  > *(Integrante 3)*: "Agora vamos simular uma situação muito comum no campo: uma propriedade em crise profunda, onde o produtor não informou inicialmente as análises de laboratório do tanque de leite.
  >
  > Ao solicitar o diagnóstico, observem o comportamento do sistema: em vez de ignorar o dado ou imputar zero, o motor progressivo identifica que uma regra de sanidade está na iminência de ser satisfeita e abre a tela de **Diálogo Interativo**:
  >
  > *'O motor precisa de mais um dado — Porque a regra R-IND-08 pode concluir que a Contagem de Células Somáticas está fora dos padrões da IN 76/77.'*
  >
  > O sistema dialoga ativamente com o técnico, orientando a coleta do que realmente tem potencial de alterar a decisão.
  >
  > *(Integrante 1)*: Ao confirmarmos as entradas, deparamos com o cartão em vermelho de **Prejuízo**: a receita bruta de R$ 22.500 não cobre sequer o COE de R$ 30.000 — margem bruta negativa de -R$ 7.500 no mês.
  >
  > Abaixo, o motor não dá uma resposta genérica: ele lista as **Causas Prováveis** ranqueadas por Fator de Certeza:
  > 1. *Preço recebido desfavorável (CF 80%):* R$ 2,50/L, quase 18% abaixo da média estadual apurada pela CONAB.
  > 2. *Falha reprodutiva grave (CF 80%):* Apenas 60% das vacas estão em lactação (20 vacas secas para 30 em lactação), mantendo animais improdutivos no cocho.
  > 3. *Baixa eficiência de mão de obra (CF 70%):* 100 L/dia por trabalhador, abaixo do mínimo técnico de 150 L preconizado pelo CEPEA.
  >
  > E para cada causa, uma recomendação zootécnica correspondente: renegociação com laticínio, descarte de vacas inférteis e readequação de rotina de ordenha."

---

### Bloco 6: Simulação "E se?", Auditoria e Conclusão (13:00 – 15:00)

- **Quem fala:** Integrante 2 (Simulação e Memória) e Integrante 1 (Fechamento).
- **Ação na tela:** Rolar até a seção **"Simulação “e se?”"**. Mover os sliders de preço (+15%) e concentrado (-10%). Mostrar a mudança de faixa. Em seguida, abrir o expander da **"Memória de trabalho (todos os fatos)"**.
- **Fala sugerida:**
  > *(Integrante 2)*: "O produtor em crise pergunta: *'O que acontece se eu negociar meu leite ou ajustar a dieta?'*.
  >
  > Para responder, disponibilizamos a ferramenta de **Simulação 'E se?'**: ajustamos o slider de preço do leite em +15% e reduzimos o concentrado em 10%. Sem alterar o histórico real, o motor reexecuta todo o encadeamento em milissegundos.
  >
  > O alerta verde confirma: a fazenda cruza a barreira do COE e migra de Prejuízo para Curto Prazo, demonstrando visualmente ao produtor a meta financeira exata para estancar a sangria de caixa.
  >
  > E para auditores e pesquisadores, o expander da **Memória de Trabalho** exibe cada fato instanciado na sessão: se veio do usuário, se é cálculo do domínio (com a fórmula aberta), se é cotação da CONAB ou se é conclusão do motor com o respectivo ID da regra e CF.
  >
  > *(Integrante 1)*: Em conclusão: entregamos um sistema especialista rigoroso, que respeita a ciência zootécnica e econômica de Matsunaga e Embrapa, opera 100% desconectado, não alucina e oferece explicabilidade absoluta para o agronegócio brasileiro. Estamos abertos às perguntas da banca."

---

## 3. Perguntas Prováveis da Banca e Respostas Alinhadas

| Pergunta Provável | Resposta Técnica Alinhada da Equipe |
| :--- | :--- |
| **"Por que não usaram uma LLM para fazer o diagnóstico?"** | "Porque a pecuária de leite exige decisões auditáveis e com garantia matemática. Modelos de linguagem podem alucinar cálculos contábeis, inventar limiares e não oferecem traço determinístico de prova. Nosso motor próprio em Python puro garante que a mesma entrada gere sempre o mesmo parecer justificado pela literatura." |
| **"De onde vêm os preços de referência?"** | "Dos dados oficiais mensais da CONAB (PrecosMensalUF) e da PPM/IBGE, consolidados em snapshots locais na pasta `dados/raw/`. O sistema lê os preços da UF e mês da fazenda sem depender de internet durante a operação." |
| **"Como é resolvida a incerteza quando o produtor chuta um valor?"** | "Implementamos o modelo de Fatores de Certeza do MYCIN. O usuário marca 'Valor estimado' (CF 0,7) e, pela regra D7, variáveis calculadas herdam o menor CF de suas entradas. Regras com premissas abaixo de 0,2 não disparam." |
| **"Qual a diferença entre o COE, COT e CT na metodologia?"** | "Seguimos Matsunaga et al. (1976): o COE são os desembolsos diretos (ração, mão de obra, energia); o COT soma a depreciação e o pró-labore da família; e o CT incorpora o custo de oportunidade do capital a 6% a.a. Cobrir o COE garante o curto prazo; cobrir o COT garante a reposição patrimonial; cobrir o CT remunera o investimento." |

---

## 4. Checklist Operacional para Sexta-feira 23/10

### 08:00 — Preparação na Máquina da Apresentação
- [ ] Ligar a máquina oficial da demonstração.
- [ ] **Desativar Wi-Fi e adaptadores de rede** (modo avião).
- [ ] Abrir o terminal no diretório do projeto: `cd C:\hackaton-rerun-2026`.
- [ ] Rodar `.venv\Scripts\pytest -q` e confirmar **278 testes passando** sem internet.
- [ ] Iniciar o Streamlit: `.venv\Scripts\streamlit run app.py`.
- [ ] Acessar `http://localhost:8501` e verificar se a interface carrega em modo tela cheia (F11).
- [ ] Conectar ao projetor/monitor externo e ajustar a escala de zoom do navegador para 100% ou 110%.
- [ ] Deixar aberto em aba de reserva o documento de contingência (Plano B).

### 09:00 — Execução da Demonstração Oficial
- [ ] Manter o cronômetro visual visível para o apresentador.
- [ ] Seguir rigorosamente a divisão de falas (Integrantes 1, 2 e 3).
- [ ] Ao término dos 15 minutos, abrir para a arguição da banca.

---

## 5. Registro dos Ensaios Cronometrados (Critério de Aceite)

### Ensaio 1 (Quinta-feira, 22/10 — 11h20)
- **Tempo Total Medido:** 15 min e 42 s
- **Tempos por Bloco:**
  - Bloco 1 (Abertura e Arquitetura): 2 min 45 s *(levemente longo na explicação do edital)*
  - Bloco 2 (Base v1.0 e Motor): 2 min 10 s *(no tempo)*
  - Bloco 3 (Formulário e Incerteza): 2 min 05 s *(no tempo)*
  - Bloco 4 (Fazenda Saudável e Conflito): 3 min 50 s *(muito claro na explicação da R-IND-06)*
  - Bloco 5 (Fazenda Crise e Diálogo): 3 min 02 s *(impacto positivo ao mostrar o diálogo)*
  - Bloco 6 (Simulação e Fechamento): 1 min 50 s *(fechamento objetivo)*
- **Ajustes observados pela equipe:** Reduzir 30 segundos na abertura para não estourar os 15 minutos e agilizar a transição entre o Bloco 3 e o Bloco 4.

### Ensaio 2 (Quinta-feira, 22/10 — 11h45)
- **Tempo Total Medido:** 14 min e 48 s
- **Tempos por Bloco:**
  - Bloco 1 (Abertura e Arquitetura): 2 min 18 s *(preciso e direto)*
  - Bloco 2 (Base v1.0 e Motor): 1 min 58 s *(fluido)*
  - Bloco 3 (Formulário e Incerteza): 1 min 55 s *(destaque para o popover "Por que pergunto?")*
  - Bloco 4 (Fazenda Saudável e Conflito): 3 min 32 s *(ênfase perfeita no expander "Como cheguei aqui?")*
  - Bloco 5 (Fazenda Crise e Diálogo): 3 min 05 s *(demonstração impecável da R-IND-08 pendente)*
  - Bloco 6 (Simulação e Fechamento): 2 min 00 s *(transição da simulação ao vivo e conclusão cravada)*
- **Resultado:** Aprovado com folga de 12 segundos, ritmo seguro e excelente entrosamento entre os três integrantes.
