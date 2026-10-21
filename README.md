# hackaton-rerun-2026

Sistema especialista de diagnóstico econômico da atividade leiteira: Hackathon UFJF 2026, tema T3 (Economia).
A decisão vem de uma base de conhecimento explícita e de um motor de inferência próprio; nenhuma LLM roda no app.

## Como rodar
Requer Python 3.11 ou mais novo. Tudo roda em localhost, sem internet.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

streamlit run app.py               # abra http://localhost:8501
pytest -q                          # todos os testes; o que cada arquivo testa: tests/README.md
ruff check . && ruff format .      # lint e formatação
```

## Estrutura
| Pasta | Papel no modelo conceitual |
|---|---|
| `app.py`, `interface/` | Interface do usuário |
| `motor/` | Motor de inferência, memória de trabalho e módulo de explicação |
| `conhecimento/` | Base de conhecimento: regras, perguntas e catálogo de produtos da CONAB em YAML |
| `dominio/` | Indicadores econômicos, dados de mercado e diagnóstico |
| `dados/` | Fontes de dados externas (snapshots) e casos de teste |
| `tests/` | Testes (pytest); o que cada arquivo testa: `tests/README.md` |
| `docs/` | Guia do sistema especialista (`docs/sistema-especialista.md`), processo com IA, arquitetura e regras |

Convenções e regras de trabalho, para a equipe e para os agentes de IA: `AGENTS.md` (o `CLAUDE.md` só importa esse arquivo). Detalhes da base de preços: `base.md`.

## Fonte dos dados
Preços agropecuários mensais por UF: CONAB (detalhes e licença em `base.md`).
