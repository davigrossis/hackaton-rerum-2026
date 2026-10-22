# Apresentação Oficial — Hackathon UFJF 2026 (Tema T3)

Slides oficiais preparados para a banca examinadora do Hackathon UFJF 2026, cobrindo o problema, o tema T3, arquitetura em 4 camadas, regras de produção, motor determinístico (0 LLM), explicabilidade, simulação e o processo com IA (as 8 diretrizes do slide 12).

## Arquivos Disponíveis

- **`apresentacao.pdf`**: Apresentação pronta em PDF widescreen (16:9), formatada para exibição no projetor ou leitura pelos jurados.
- **`index.html`**: Apresentação interativa em HTML/CSS moderno. Pode ser aberta em qualquer navegador (pressione `F11` para tela cheia e use as setas ou scroll).
- **`gerar_pdf.py`**: Script automatizado para regenerar o PDF nativamente via Microsoft Edge ou Chrome headless, sem dependências adicionais:
  ```bash
  python docs/apresentacao/gerar_pdf.py
  ```

## Estrutura dos 15 Slides

| # | Slide | Destaques |
|---|---|---|
| 1 | **Capa** | Identificação do projeto, tema T3, equipe e parâmetros de engenharia. |
| 2 | **O Desafio Econômico** | Custos de alimentação (40–65% do COE), volatilidade de preços e falta de clareza causal. |
| 3 | **O Tema T3 e o Propósito** | Entradas mensais, processamento local e parecer executivo acionável. |
| 4 | **Diretriz: Por que Sistema Especialista?** | Zero LLM em runtime, determinismo contábil, ausência de alucinações e 100% offline. |
| 5 | **Arquitetura em 4 Camadas** | Interface (Streamlit) → Domínio → Motor genérico → Conhecimento (YAML). |
| 6 | **Fontes Oficiais: CONAB e IBGE** | Cotações de leite, milho e diesel (PrecosMensalUF) e produtividade regional (PPM). |
| 7 | **Base de Conhecimento v1.0** | 30 regras em 4 camadas, 0 pendências, embasamento Embrapa, CEPEA e MAPA IN 76/77. |
| 8 | **Motor de Inferência e MYCIN** | Estratificação por camadas (D3), resolução de conflitos e cálculo de CF. |
| 9 | **Explicabilidade: "Como?" e "Por quê?"** | Transparência prévia no formulário e rastreabilidade genealógica no parecer. |
| 10 | **Demonstração Prática (15 min)** | Fazenda Saudável (Lucro e conflito R-IND-06 x R-IND-05) vs Fazenda em Crise (Prejuízo). |
| 11 | **Simulação Interativa "E se?"** | Ajuste dinâmico de sliders de preço e insumos revertendo a solvência em tempo real. |
| 12 | **Qualidade e Confiabilidade** | 278 testes automatizados, máquina limpa em 1,90 min e blindagem offline. |
| 13 | **Processo com IA (Slide do Processo)** | Tabela detalhada mapeando as 8 diretrizes do slide 12 com suas evidências no repo. |
| 14 | **Gestão e Versionamento** | 28 issues em 6 fases no GitHub, Conventional Commits e diário contínuo. |
| 15 | **Conclusão e Agradecimentos** | Síntese do valor e prontidão tecnológica para a pecuária leiteira nacional. |
