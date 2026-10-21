# AGENTS.md

Guia do repositório para os modelos e para a equipe. Vale para todo o projeto.

## Projeto
Sistema especialista de **diagnóstico econômico da atividade leiteira**: Hackathon UFJF 2026, tema **T3 Economia** ("análise econômica e financeira com dados zootécnicos e custos de insumos").

- **Usuário:** produtor de leite ou técnico de assistência técnica.
- **Entrada:** dados de 1 mês de 1 fazenda: rebanho, produção, preço do leite e custos.
- **Saída:** parecer explicável com indicadores (custo por litro, margens), situação econômica, causas prováveis e recomendações. Cada item traz confiança (CF) e explicação "como?" / "por quê?".
- **Referência de mercado:** preços mensais por UF da CONAB (leite ao produtor, milho, diesel), lidos do snapshot local em `dados/raw/`.
- **Fora do escopo:** login, banco de dados, histórico de vários meses, várias fazendas, formulação de dieta, deploy em nuvem.

### Regras do hackathon (não negociáveis)
- **A LLM não é o sistema especialista.** Nenhuma chamada a LLM ou API de IA no código da aplicação. Quem decide é a base de conhecimento + o motor de inferência (determinístico e auditável).
- Roda **100% em localhost**, sem internet durante a demo.
- Só ferramentas e bibliotecas **open source**.
- Entregáveis: código, documentação (processo de desenvolvimento, arquitetura, regras de produção) e apresentação. Envio até **qui 22/10 às 20h**; demo **sex 23/10 às 9h**.
- Os PDFs oficiais ficam em `info-hackaton/`, fora do git.

## Stack
- Python 3.11+ · Streamlit 1.66 (interface) · PyYAML 6.0 (base de conhecimento)
- Motor de inferência **próprio**, em Python puro
- pandas (vem com o Streamlit): usar só onde simplifica (leitura da CONAB, gráficos)
- Dev: pytest 9.1 · ruff 0.17

## Estrutura
```
app.py                 # entrada do Streamlit: Interface do usuário
interface/             # telas e componentes Streamlit
motor/                 # motor GENÉRICO: não conhece leite nem economia
  memoria.py           #   memória de trabalho: fato = valor + CF + origem
  regras.py            #   carrega e valida conhecimento/regras.yaml
  inferencia.py        #   encadeamento progressivo, resolução de conflito, CF
  explicacao.py        #   "como?" e "por quê?" a partir do traço
conhecimento/          # BASE DE CONHECIMENTO, explícita e versionada
  regras.yaml          #   regras de produção
  perguntas.yaml       #   perguntas, unidades, faixas válidas, texto de ajuda
dominio/               # código específico do T3
  indicadores.py       #   fórmulas: COE, COT, CT, custo/L, margens, % lactação...
  mercado.py           #   dados/raw → fatos externos (preços CONAB por UF)
  diagnostico.py       #   respostas → indicadores + mercado → motor → resultado
dados/
  raw/                 #   snapshots originais (CONAB/IBGE) + FONTES.md; não editar
  casos/               #   fazendas-exemplo: demo e testes de casos conhecidos
  baixar_dados.py      #   atualiza os snapshots (precisa de internet; nunca na demo)
tests/                 # pytest
docs/                  # arquitetura, catálogo de regras, processo com IA, apresentação
```

## Comandos
```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

streamlit run app.py               # http://localhost:8501
pytest -q                          # todos os testes
pytest tests/test_casos.py -q      # só os casos conhecidos
ruff check . && ruff format .      # lint e formatação
python dados/baixar_dados.py       # atualiza dados de mercado (com internet)
```

## Base de conhecimento (`conhecimento/regras.yaml`)
```yaml
versao: "0.1"
regras:
  - id: R-SIT-03
    descricao: Receita cobre o COE mas não o COT; sobrevive só no curto prazo
    camada: situacao        # indicador | situacao | causa | recomendacao
    prioridade: 50          # maior dispara antes (resolução de conflito)
    se:                     # todas verdadeiras (E); para OU, escreva outra regra
      - [receita_total, ">=", $coe]
      - [receita_total, "<", $cot]
    entao: {fato: situacao_economica, valor: curto_prazo}
    cf: 1.0                 # de 0 a 1
    fonte: "Matsunaga et al. (1976), metodologia de custo operacional"
```
- Operadores: `==  !=  <  <=  >  >=  in`. `$nome` referencia outro fato; o resto é literal.
- Um fato pode ter vários valores (ex.: várias causas). `==` é verdadeiro se algum valor bate.
- CF da conclusão = `cf da regra × menor CF das premissas`. Premissa com CF < 0,2 conta como falsa. Se duas regras chegam à mesma conclusão: `cf1 + cf2 × (1 − cf1)`.
- Conflito: maior `prioridade` → mais condições → ordem no arquivo. Cada regra dispara no máximo uma vez.
- Toda regra precisa de `id` único, `descricao`, `fonte` e de ao menos um caso de teste que a exercite.

## Convenções de código
- Português nos nomes do domínio, textos da interface, regras e docs. Identificadores em `snake_case`, sem acento: `custo_por_litro`, `vacas_lactacao`.
- Toda variável tem unidade declarada em `perguntas.yaml` ou no indicador. Dinheiro em R$, volume em litros, período de referência = 1 mês.
- `motor/` não importa `dominio/`, `interface/` nem Streamlit. `dominio/` não importa Streamlit.
- Funções pequenas e puras. Classe só quando simplifica (ex.: `Fato`, `Regra`). Type hints nas funções públicas.
- Campo opcional vazio **não vira zero**: o fato não entra na memória e as regras que dependem dele não disparam.
- Nenhum acesso à rede em tempo de execução. Só `dados/baixar_dados.py` usa internet.

## Git e commits
- `main` sempre roda. Uma branch por issue: `feat/12-regras-causas`, `fix/31-divisao-zero`.
- Conventional Commits em português: `feat(motor): combina CF de regras com mesma conclusão`. Tipos: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`.
- Commits pequenos e `pytest -q` passando antes do PR. PR pequeno, merge rápido.
- PR que altera `conhecimento/` precisa de revisão de outra pessoa (a base é versionada e revisada).
- Depois do congelamento (qua 21/10 às 23h59), só entram correções, docs e apresentação.

## Regras de trabalho para o Claude
1. **Nunca** coloque chamada a LLM ou API de IA no código da aplicação.
2. Faça mudanças pequenas, restritas à issue pedida. Nada de refatoração "de brinde".
3. Não adicione dependência sem perguntar. Hoje são: streamlit, PyYAML, pandas, pytest, ruff.
4. Pergunte antes de decisões grandes: formato da regra, API do motor, estrutura de pastas, lista de variáveis, troca de biblioteca.
5. Não invente conhecimento de domínio. Limiar sem fonte confiável recebe `fonte: "PENDENTE"` e deve ser apontado na resposta.
6. Criou ou alterou regra? Atualize o caso de teste correspondente e rode `pytest -q`.
7. Antes de dizer "pronto", rode os testes e o app. Se algo falhar, mostre a saída.
8. Todo disparo de regra vai para o traço (regra, premissas com valores, CF): é ele que alimenta a explicação.
9. Registre decisões e prompts relevantes em `docs/processo-ia.md`: a apresentação precisa mostrar como a IA foi usada.
10. Não versione `info-hackaton/`, `.env` nem `.venv/`.
