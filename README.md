# hackaton-rerun-2026

Sistema especialista de diagnóstico econômico da atividade leiteira: Hackathon UFJF 2026, tema T3 (Economia).
A decisão vem de uma base de conhecimento explícita e de um motor de inferência próprio; nenhuma LLM roda no app.

## Como rodar
Requer Python 3.11 ou mais novo. Tudo roda em localhost, sem internet.

### Instalação padrão
```bash
# 1. Clone o repositório
git clone https://github.com/davigrossis/hackaton-rerun-2026.git
cd hackaton-rerun-2026

# 2. Crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .venv\Scripts\Activate.ps1
                                   # Windows (CMD):        .venv\Scripts\activate.bat

# 3. Instale as dependências
pip install -r requirements-dev.txt

# 4. Inicie o sistema especialista
streamlit run app.py               # abra http://localhost:8501
pytest -q                          # suíte de testes; detalhes em tests/README.md
ruff check . && ruff format .      # auditoria de código e formatação
```

### Como testar offline (sem Wi-Fi)
A aplicação roda 100% offline em localhost, cumprindo a regra fundamental do hackathon:
1. Desconecte o Wi-Fi ou desative os adaptadores de rede da máquina.
2. Execute a suíte de testes e o aplicativo:
   ```bash
   pytest -q                      # roda todos os testes sem acesso externo à internet
   pytest tests/test_offline.py -v # validação formal com bloqueio de sockets externos
   streamlit run app.py           # sobe a interface web no navegador localmente
   ```

### Instalação em máquina totalmente desconectada (sem internet prévia)
Caso a máquina de apresentação não possua conexão com a internet durante o setup:
1. Em uma máquina conectada, baixe os pacotes para um diretório local:
   ```bash
   pip download -r requirements-dev.txt -d wheels/
   ```
2. Transfira a pasta `wheels/` (ex.: pendrive) para a máquina offline e instale:
   ```bash
   pip install --no-index --find-links wheels/ -r requirements-dev.txt
   ```

### Tempo de inicialização do zero (#21)
O projeto foi auditado e cronometrado a partir de um clone limpo, subindo do zero em **1,90 minutos** (critério de aceite do hackathon: < 10 minutos):
- Criação do `.venv`: 11,2 s
- Instalação das dependências (pip): 76,3 s
- Execução de toda a suíte de testes (278 testes): 21,7 s
- Inicialização do app Streamlit: 2,5 s

Na barra lateral, selecione **Base de conhecimento** para consultar a versão,
as condições, conclusões, confiança e fontes de todas as regras usadas pelo motor.

Na barra lateral, o seletor **Fazenda-exemplo** carrega três perfis para explorar
cenários diferentes: uma fazenda excelente, mas sensível a queda de preço e
produção; uma fazenda média, que pode atingir resultado bom com melhora de preço
e produção; e uma fazenda ruim, dependente de preço, produção e custo do
concentrado. A escolha preenche o formulário e reinicia a análise desde a
primeira etapa.

## Estrutura
| Pasta | Papel no modelo conceitual |
|---|---|
| `app.py`, `interface/` | Interface do usuário |
| `motor/` | Motor de inferência, memória de trabalho e módulo de explicação |
| `conhecimento/` | Base de conhecimento: regras, perguntas e catálogo de produtos da CONAB em YAML |
| `dominio/` | Indicadores econômicos, dados de mercado (CONAB), média regional (IBGE) e diagnóstico |
| `dados/` | Fontes de dados externas (snapshots) e casos de teste |
| `tests/` | Testes (pytest); o que cada arquivo testa: `tests/README.md` |
| `docs/` | Guia do sistema especialista (`docs/sistema-especialista.md`), processo com IA, arquitetura e regras |

Convenções e regras de trabalho, para a equipe e para os agentes de IA: `AGENTS.md` (o `CLAUDE.md` só importa esse arquivo). Detalhes da base de preços: `base.md`.

## Fonte dos dados
Preços agropecuários mensais por UF: CONAB (detalhes e licença em `base.md`).
Produção de leite e vacas ordenhadas por UF: IBGE – PPM, tabelas 74 e 94 (detalhes e licença em `dados/raw/FONTES.md`).
