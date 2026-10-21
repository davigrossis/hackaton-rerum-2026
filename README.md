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
pytest -q                          # testes
ruff check . && ruff format .      # lint e formatação
```

## Estrutura
| Pasta | Papel no modelo conceitual |
|---|---|
| `app.py`, `interface/` | Interface do usuário |
| `motor/` | Motor de inferência, memória de trabalho e módulo de explicação |
| `conhecimento/` | Base de conhecimento: regras e perguntas em YAML |
| `dominio/` | Indicadores econômicos, dados de mercado e diagnóstico |
| `dados/` | Fontes de dados externas (snapshots) e casos de teste |
| `tests/` | Testes (pytest) |
| `docs/` | Processo com IA, arquitetura e regras |

Convenções e regras de trabalho: `CLAUDE.md`. Detalhes da base de preços: `base.md`.

## Fonte dos dados
Preços agropecuários mensais por UF: CONAB (detalhes e licença em `base.md`).
