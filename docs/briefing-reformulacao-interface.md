# Briefing para reformulação da interface do EconoLeite

## 1. Onde está o código da interface

O ponto de entrada atual da aplicação Streamlit é:

- `app.py`

O diretório reservado para componentes reutilizáveis é:

- `interface/`

Atualmente, `interface/` contém apenas o arquivo inicial de pacote. A maior
parte da interface está concentrada em `app.py`, incluindo:

- carregamento da base de conhecimento;
- renderização das perguntas;
- agrupamento por seção;
- preenchimento da fazenda-exemplo;
- coleta das respostas;
- validação de campos obrigatórios;
- resultado mock.

Arquivos relacionados que não devem ser confundidos com a interface:

- `motor/regras.py`: carrega e valida a base de conhecimento;
- `motor/inferencia.py`: fornece `perguntas_pendentes`;
- `motor/memoria.py`: representa a memória de trabalho;
- `conhecimento/perguntas.yaml`: declara perguntas, seções, tipos, unidades,
  faixas e textos de ajuda;
- `conhecimento/variaveis.yaml`: declara variáveis calculadas, externas e
  conclusões;
- `conhecimento/regras.yaml`: base das regras de produção, atualmente vazia;
- `dominio/diagnostico.py`: futuro orquestrador do diagnóstico;
- `dominio/indicadores.py`: futuro cálculo dos indicadores;
- `dominio/mercado.py`: leitura dos dados locais da CONAB.

## 2. Contexto do produto

O EconoLeite é um sistema especialista para diagnóstico econômico mensal de uma
fazenda leiteira, desenvolvido para o Hackathon UFJF 2026, tema T3 Economia.

O usuário principal é:

1. o produtor de leite, que precisa entender se a atividade está pagando seus
   custos;
2. o técnico de assistência técnica, que precisa de um diagnóstico padronizado
   e explicável.

O sistema recebe dados de uma fazenda e de um mês e deverá apresentar:

- indicadores econômicos;
- custos por litro;
- margens;
- situação econômica;
- causas prováveis;
- recomendações;
- confiança de cada conclusão;
- explicação de “como?” e “por quê?”.

O sistema deve funcionar 100% em localhost, sem acesso à internet durante a
execução. A decisão final pertence à base de conhecimento e ao motor
determinístico, não a uma LLM.

## 3. Estado atual da interface

O arquivo `app.py` atualmente:

1. carrega a base usando `carregar_base()` de `motor/regras.py`;
2. obtém as perguntas por `perguntas_pendentes(base, Memoria())`;
3. renderiza as perguntas conforme seus tipos;
4. organiza as perguntas nas seis seções da base;
5. mostra unidade e ajuda;
6. permite carregar uma fazenda-exemplo;
7. transforma os valores preenchidos em um `dict`;
8. valida perguntas obrigatórias;
9. mostra um resultado mock.

O resultado mock é intencional e deve continuar identificado como provisório.
O diagnóstico real ainda depende da implementação de:

- `dominio/indicadores.py`;
- `dominio/diagnostico.py`;
- `motor/inferencia.py`;
- `motor/explicacao.py`;
- regras em `conhecimento/regras.yaml`.

Não se deve implementar uma classificação econômica real diretamente na
interface como atalho. Quando o motor estiver pronto, a interface deverá
chamar o orquestrador do domínio.

## 4. Contratos que precisam ser preservados

### Base de conhecimento

A interface não deve ler YAML diretamente. Deve consumir a base através de
`carregar_base()` e usar os objetos `Base`, `Secao` e `Pergunta`.

As perguntas disponíveis vêm de:

```python
perguntas = perguntas_pendentes(base, memoria)
```

A interface não deve duplicar a lista de perguntas, seções, unidades ou textos
de ajuda no código.

### Respostas

As respostas precisam virar um dicionário no formato:

```python
{
    "uf": "MG",
    "mes_referencia": "09/2026",
    "vacas_lactacao": 42,
    "producao_litros": 28000.0,
    "preco_leite_fazenda": 3.04,
}
```

Campos vazios não devem ser convertidos para zero. Campos opcionais ausentes
devem simplesmente não aparecer no dicionário.

### Tipos de pergunta

Os tipos previstos pela base são:

- `escolha`;
- `mes`;
- `inteiro`;
- `numero`.

Perguntas numéricas possuem unidade e faixa. Perguntas de escolha possuem
opções declaradas na base.

### Estado da sessão

O formulário pode usar `st.session_state`, mas o estado deve permanecer
previsível. O carregamento da fazenda-exemplo deve preencher os campos sem
apagar dados inesperadamente ou criar valores que não estão na base.

## 5. Perguntas disponíveis

As perguntas estão organizadas em:

1. **Identificação da Propriedade**
   - UF;
   - mês de referência.
2. **Rebanho e Produtividade**
   - vacas em lactação;
   - vacas secas.
3. **Faturamento e Receitas**
   - produção;
   - preço do leite;
   - outras receitas.
4. **Custos Operacionais Desembolsados (COE)**
   - concentrado;
   - quantidade de concentrado;
   - volumoso;
   - mineral;
   - mão de obra contratada;
   - sanidade e reprodução;
   - energia e combustível;
   - outros custos.
5. **Custos Não Desembolsados e Capital**
   - depreciação;
   - pró-labore;
   - capital investido.
6. **Informações Complementares e Qualidade**
   - área;
   - pessoas;
   - CCS;
   - CPP.

## 6. Objetivo da reformulação

Reformular a interface para que ela seja mais assertiva, clara e adequada ao
usuário produtor/técnico, sem alterar os contratos do motor.

A reformulação deve priorizar:

- redução da sensação de formulário longo;
- orientação clara sobre o que precisa ser informado;
- destaque para unidades e exemplos;
- distinção visual entre perguntas obrigatórias e opcionais;
- progressão natural entre as seções;
- prevenção de erros de preenchimento;
- resumo das respostas antes do envio;
- feedback claro depois do envio;
- visualização adequada em notebook e monitor comum;
- linguagem simples em português;
- indicação explícita de que o resultado atual é mock, enquanto o motor real
  não estiver integrado.

## 7. Direção visual sugerida

Manter uma interface limpa e profissional, com foco em tomada de decisão:

- título curto e subtítulo explicativo;
- bloco inicial com objetivo do diagnóstico;
- indicador de progresso por seção;
- cards ou colunas para os principais dados;
- campos de identificação destacados no começo;
- custos agrupados de forma visual;
- dicas contextuais próximas do campo;
- botão de exemplo em posição secundária;
- botão principal de diagnóstico destacado;
- resultado em card com situação, observações e próximos passos;
- uso moderado de cores: verde para situação favorável, amarelo para atenção
  e vermelho para situação desfavorável, quando houver diagnóstico real.

Não adicionar dependências sem aprovação. Usar os recursos já disponíveis do
Streamlit e componentes simples do projeto.

## 8. Restrições importantes

- Não adicionar LLM, API de IA ou acesso à rede.
- Não mover regras de negócio para a interface.
- Não duplicar a base de perguntas no Python.
- Não transformar campos ausentes em zero.
- Não inventar conclusões reais enquanto o motor estiver incompleto.
- Não criar login, banco de dados, histórico ou cadastro de várias fazendas.
- Não modificar o contrato YAML sem necessidade.
- Não alterar o comportamento do motor para resolver um problema visual.
- Preservar o funcionamento do botão de fazenda-exemplo.
- Manter a execução em localhost.

## 9. Critérios de aceite para a nova interface

### Funcionais

- O app inicia com `streamlit run app.py`.
- A aplicação responde em localhost.
- As perguntas são obtidas por `perguntas_pendentes`.
- A interface não acessa os arquivos YAML diretamente.
- As respostas são armazenadas em um `dict`.
- O UF é escolhido a partir das opções da pergunta.
- Unidades e textos de ajuda aparecem para perguntas que os possuem.
- Perguntas obrigatórias são identificadas e validadas.
- Campos opcionais vazios não aparecem no dicionário.
- O botão de fazenda-exemplo preenche um conjunto coerente de respostas.
- O resultado mock permanece explicitamente identificado como mock.

### Técnicos

- `pytest -q` continua passando.
- `ruff check .` continua passando.
- Não há chamadas externas de rede.
- A interface continua dependendo do motor para obter as perguntas.
- O código permanece legível e dividido em funções pequenas.

## 10. Arquivos que o agente deve ler antes de editar

- `app.py`;
- `motor/inferencia.py`;
- `motor/memoria.py`;
- `motor/regras.py`;
- `conhecimento/perguntas.yaml`;
- `docs/contratos.md`;
- `AGENTS.md`;
- `tests/test_esqueleto.py`.

## 11. Prompt pronto para outro agente de IA

> Você está trabalhando no projeto EconoLeite, em Python 3.11+ com Streamlit.
> Leia `AGENTS.md`, `app.py`, `motor/inferencia.py`, `motor/memoria.py`,
> `motor/regras.py`, `conhecimento/perguntas.yaml`, `docs/contratos.md` e
> `tests/test_esqueleto.py` antes de editar.
>
> Reformule a interface Streamlit para deixá-la mais clara, assertiva e
> adequada a produtor de leite e técnico de assistência técnica. Preserve o
> contrato atual: a interface deve carregar a base com `carregar_base()`, obter
> as perguntas via `perguntas_pendentes(base, memoria)`, renderizar as seis
> seções declaradas na base, mostrar unidade e ajuda, coletar as respostas em
> um `dict`, manter o botão de carregar fazenda-exemplo e exibir resultado
> mock explicitamente identificado como provisório.
>
> Não leia YAML diretamente na interface, não duplique perguntas ou textos,
> não coloque regras de negócio no Streamlit, não adicione dependências, não
> use LLM/API de IA e não acesse a internet. Campos opcionais vazios não
> podem virar zero. Preserve a execução em localhost.
>
> Melhore principalmente a hierarquia visual, o agrupamento dos campos, a
> orientação do usuário, a indicação de obrigatoriedade, a validação, o
> resumo antes do envio e a clareza do resultado. Se criar componentes,
> prefira colocá-los em `interface/`, mantendo `app.py` como ponto de entrada.
>
> Depois da implementação, rode `pytest -q`, `ruff check .` e faça um smoke
> test do Streamlit em localhost. Relate os arquivos alterados, os testes
> executados e qualquer limitação que permaneça.

