# Fontes dos dados

Os arquivos desta pasta são cópias **originais**, sem edição. Todo cálculo derivado é feito em tempo de execução (`dominio/mercado.py` e `dominio/benchmark.py`). Para atualizar: baixar o arquivo pelo link, substituir o de `dados/raw/`, trocar a data do download aqui e, se for a CONAB, gerar de novo o `dados/PrecosMensalUF.xlsx`.

## PrecosMensalUF.txt
- **O que é:** preços agropecuários mensais por UF (leite ao produtor, milho, diesel e outros 1.248 produtos). Análise da base em `base.md`.
- **Fonte:** CONAB, Portal de Informações Agropecuárias
- **Link:** https://portaldeinformacoes.conab.gov.br/downloads/arquivos/PrecosMensalUF.txt
- **Data do download:** 20/10/2026
- **Período coberto:** 10/2025 a 09/2026
- **Licença:** o portal não declara licença própria; o site da CONAB usa CC BY-ND 3.0 (https://creativecommons.org/licenses/by-nd/3.0/br/). Citar "Fonte: CONAB" e não editar o arquivo.

## Cópia para visualização: `dados/PrecosMensalUF.xlsx`
- Planilha gerada a partir do `PrecosMensalUF.txt`, só para abrir no Excel. O sistema não lê esse arquivo.
- Fica fora desta pasta porque não é o original. Ao trocar a base, gere a planilha de novo para ela não ficar diferente do `.txt`.

## ibge_ppm_74.json e ibge_ppm_94.json
- **O que é:** Pesquisa da Pecuária Municipal (PPM) por UF: produção de leite (tabela 74, variável 106, em mil litros) e vacas ordenhadas (tabela 94, variável 107, em cabeças). Com elas, `dominio/benchmark.py` calcula a produtividade média da UF em L/vaca/dia.
- **Fonte:** IBGE, SIDRA (https://sidra.ibge.gov.br/tabela/74 e https://sidra.ibge.gov.br/tabela/94)
- **Links:** https://apisidra.ibge.gov.br/values/t/74/n3/all/v/106/p/2024-2025/c80/2682 e https://apisidra.ibge.gov.br/values/t/94/n3/all/v/107/p/2024-2025 (para um ano novo, trocar o `p/2024-2025` nos dois)
- **Data do download:** 22/10/2026
- **Período coberto:** 2024 e 2025, 27 UFs
- **Licença:** sem licença formal publicada. Citar "Fonte: IBGE – PPM" e não editar os arquivos.
