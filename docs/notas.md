# Notas do projeto

## Objetivo e indicador

**Objetivo central:** entender onde o atendimento falha e o que está associado à resolução percebida.

**Indicador principal:** taxa de resolução percebida = reclamações avaliadas como "Resolvida" ÷ reclamações avaliadas.

## Escopo e limitações

- Período: out/2024 a set/2026 (24 meses fechados).
- Apenas reclamações avaliadas pelo consumidor: [X]% do total nos 24 meses (recalcular; o ~31% anterior era só de agosto/2026).
- Mede a resolução **percebida pelo consumidor**, não o desempenho objetivo da empresa.
- Difere do índice oficial da plataforma, que conta como resolvida a reclamação não avaliada. Por isso os números aqui não vão bater com os do Perfil do Fornecedor.
- A análise de tempo de resposta usa só reclamações respondidas (`respondida = 'S'`), porque o campo é nulo nas demais.

## Perguntas

| # | Pergunta | Status |
|---|----------|--------|
| 1 | Quais segmentos têm menor/maior taxa de resolução? | em andamento |
| 2 | Quando a empresa responde, a resolução é maior? | em andamento |
| 3 | O tempo de resposta se associa à resolução? | pendente |
| 4 | Ter procurado a empresa antes muda a chance de resolução? | pendente |
| 5 | Como a taxa evolui mês a mês? | pendente |

## Qualidade dos dados

### 2025/09: colunas extras

O arquivo de 2025/09 veio com 2 colunas a mais: `Interação com Judiciário` e `Último Complemento Consumidor`.
- **Decisão:** descartadas, por serem irrelevantes para as perguntas do projeto.
- **Conferência:** as demais colunas coincidem em nome e ordem com os outros meses.

### Tempo de resposta

- **Esperado:** 0 a 10 dias (prazo padrão), com 11 como limite inicialmente assumido.
- **Observado:** valores até 16 em 2025/09 e até 80 em 2024/10; 2 valores negativos (-16 e -4) em um mês de pico.
- **Padrão por mês:** a taxa de respostas acima de 10 dias fica perto de 0% na maior parte dos meses e sobe em blocos (2025-11 a 2026-01 e 2026-05 a 2026-07, com picos de ~25% em 2026-01 e 2026-06).
- **Distribuição em mês de pico:** os valores de 11 a 15 crescem de forma contínua e caem para 5 casos no dia 16, ou seja, há um teto nítido em 15.
- **Concentração:** nos meses de pico, as 5 maiores empresas respondem por 25-40% dos casos acima de 10 dias; o restante está espalhado por muitas empresas.
- **Hipótese:** prazo de resposta de 15 dias em vigor em alguns períodos (o prazo já foi ampliado de 10 para 15 dias em 2020). **Ainda não confirmada.**
- **Teste pendente:** query por dia de finalização, buscando um degrau abrupto na taxa. Resultado: [preencher].
- **Tratamento:** [definir: flag de período, filtro de ≤ 10 dias ou comparação por regime]. Valores negativos: [tratar como NULL].

### Não respondidas com avaliação

Entre as reclamações com `respondida = 'N'`: 19.734 não avaliadas, 3.569 "Não Resolvida" e 570 "Resolvida".

**Hipóteses:**
1. Resposta fora do prazo (perde força: o tempo de resposta é nulo em todos os casos).
2. Resolução por outro canal, sem registro de resposta (possível).
3. Consumidor avalia mesmo sem receber resposta (possível; explicaria as "Não Resolvida").
4. Significado do campo `Respondida`: [conferir no dicionário de dados e anotar].

**Evidências nas 570 "Resolvida":** 424 foram abertas pela internet; 535 (93,86%) já tinham procurado a empresa antes e 35 (6,14%) não.
**Cuidado:** o percentual de 94% só distingue algo se for comparado com o mesmo percentual na base geral. [Comparar e anotar.]

**Decisão:** [definir como tratar esses casos: manter, excluir da pergunta 2 ou analisar à parte].

## Decisões

| Data | Decisão | Motivo |
|------|---------|--------|
| [20/10/2026] | Descartar as colunas extras de 2025/09 | Irrelevantes para as perguntas |
| [21/10/2026] | Analisar só reclamações avaliadas | O indicador mede a resolução percebida |
| [26/10/2026] | Carregar os 24 meses antes de responder às perguntas | Evitar refazer a análise por mês |
| [29/10/2026] | [tratamento do tempo de resposta] | facilitar o manuseio |

## Perguntas em aberto

- Por que o tempo de resposta é maior nas resolvidas? Testar dentro de cada segmento **e dentro de cada mês**: se o prazo de resposta mudou ao longo do tempo e a taxa de resolução também, o período pode estar afetando as duas variáveis ao mesmo tempo.
- As empresas do topo do ranking de respostas acima de 10 dias continuam lá quando se excluem os meses de pico?

## Anexo: índices

Foram criados índices nas colunas mais usadas em filtros e agrupamentos: `uf`, `data_finalizacao`, `segmento_de_mercado` e `nome_fantasia`. Comandos em `sql/indices.sql`. Avaliar também `ano_mes` e `tempo_resposta`, usados com frequência nas queries.
