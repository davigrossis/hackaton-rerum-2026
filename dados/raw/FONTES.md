# Fontes dos dados

Os arquivos desta pasta são cópias **originais**, sem edição. Todo cálculo derivado é feito em tempo de execução (`dominio/mercado.py`). Para atualizar: baixar o arquivo pelo link, substituir o de `dados/raw/`, trocar a data do download aqui e gerar de novo o `dados/PrecosMensalUF.xlsx`.

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
