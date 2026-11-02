# Registro de decisões

| ID | Decisão | Status |
|----|---------|--------|
| D-001 | Explorar o CSV antes de modelar | aceita |
| D-002 | Analisar só reclamações avaliadas | aceita |
| D-003 | Carregar os 24 meses antes de responder às perguntas | aceita |
| D-004 | Descartar as 2 colunas extras de 2025/09 | aceita |
| D-005 | Criar Índices para facilitar a busca | aceita |
| D-006 | Marcar o período de prazo estendido com flag, sem excluir | aceita |
| D-007 | Tratar os dados negativos em tempo_resposta como NULL | aceita | 

---

## D-001 · Explorar o CSV antes de modelar
- **Data:** 19/10/2026
- **Contexto:** não conhecia a estrutura nem a qualidade dos dados.
- **Decisão:** escrever um script que perfila o arquivo (colunas, tipos, nulos, valores distintos) antes de criar tabelas.
- **Alternativas:** carregar direto no PostgreSQL e descobrir os problemas depois.
- **Impacto:** o esquema da tabela e as regras de validação partiram do que o perfil mostrou.


## D-002 · Analisar só reclamações avaliadas
- **Data:** 21/10/2026
- **Contexto:** Do número total de reclamações, apenas 32% foram avaliadas.
- **Decisão:** Avaliar somente as reclamações avaliadas.
- **Alternativas:** Avaliar todas as reclamações
- **Impacto:** Apenas 32% dos dados serão avaliados (cerca de 1.897.768 reclamações)


## D-003 · Carregar os 24 meses antes de responder às perguntas
- **Data:** 23/10/2026
- **Contexto:** Inicialmente estava sendo utilizado apenas 1 mês para o entendimento dos dados, poderia ter se iniciado a busca pelas respostas
neste estágio, porém se poderia carregar logo 2 cliclos para a comparação.
- **Decisão:** Carregar 2 ciclos completos de 2 anos de reclamções, para depois responder as perguntas.
- **Alternativas:** Começar a responder as perguntas apenas utilizado o mês de teste.
- **Impacto:** Início da resolução das perguntas adiado; Observação sobre os valores totais; Comparação entre os mesmos meses em ciclos diferentes.


## D-004 · Descartar as 2 colunas extras de 2025/09
- **Data:** 27/10/2026
- **Contexto:** o arquivo de 2025/09 veio com `Interação com Judiciário` e `Último Complemento Consumidor`; as demais colunas coincidem em nome e ordem.
- **Decisão:** descartar as duas, por não serem usadas nas perguntas.
- **Alternativas:** adicionar as colunas a todos os meses com NULL.
- **Impacto:** nenhuma pergunta depende delas. Se virarem relevantes, é preciso reprocessar o CSV original de 2025/09.


## D-005 · Criar Índices para facilitar a busca
- **Data:** 31/10/2026
- **Contexto:** As análises estavam demorando bastante devido ao volume de dados.
- **Decisão:** Criar índices para acelerar esse processo.
- **Alternativas:** Continuar sem índices.
- **Impacto:** As buscas ficaram mais rápidas, mas a inserção provavelmente ficou mais lenta.


## D-006 · Flag para o período de prazo estendido
- **Data:** 02/11/2026
- **Contexto:** duas janelas de ~60 dias têm respostas de até 15 dias; causa não identificada (ver `notas.md`, "Tempo de resposta").
- **Decisão:** criar a view `ocorrencias_analise` com `periodo_prazo_estendido` , `tempo_atipico` (> 15)
  e `tempo_resposta_valido` e rodar a pergunta 3 com e sem esses meses.
- **Alternativas:** excluir os meses; cortar os valores acima de 10.
- **Impacto:** nenhum dado é perdido; as datas das janelas são aproximadas.


## D-007 · Tratamento dos valores negativos
- **Data:** 02/11/2026
- **Contexto:** dois valores negativos no tempo_resposta.
- **Decisão:** definir ambos como NULL na VIEW criada, deixando os valores originais intactos.
- **Alternativas:** não alterar eles; excluir linhas; usar o valor absoluto.
- **Impacto:** interferência de dois valores impossíveis, com tão pouco casos não muda o resultado referente.



## D-00 · ---
- **Data:**
- **Contexto:**
- **Decisão:** 
- **Alternativas:**
- **Impacto:**