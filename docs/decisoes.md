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
| D-008 | Analisar todas as avaliadas, respondidas ou não | aceita |
| D-009 | Utilizar o intervalo de Wilson em vez da taxa bruta para a pergunta 1 | aceita |
| D-010 | Recorte de 3 meses de cada lado dos dados, referenciando o inicio e o fim | aceita |
| D-011 | Decomposição entre efeito dentro dos segmentos e composição | aceita |

---

## D-001 · Explorar o CSV antes de modelar
- **Data:** 19/10/2026
- **Contexto:** Não conhecia a estrutura nem a qualidade dos dados.
- **Decisão:** Escrever um script que perfila o arquivo (colunas, tipos, nulos, valores distintos) antes de criar tabelas.
- **Alternativas:** Carregar direto no PostgreSQL e descobrir os problemas depois.
- **Impacto:** O esquema da tabela e as regras de validação partiram do que o perfil mostrou.


## D-002 · Analisar só reclamações avaliadas
- **Data:** 21/10/2026
- **Contexto:** Do número total de reclamações, apenas 32% foram avaliadas.
- **Decisão:** Analisar somente as reclamações avaliadas.
- **Alternativas:** Contar as não avaliadas como resolvidas
- **Impacto:** Apenas 32% dos dados serão avaliados (cerca de 1.897.927 reclamações)


## D-003 · Carregar os 24 meses antes de responder às perguntas
- **Data:** 23/10/2026
- **Contexto:** Inicialmente estava sendo utilizado apenas 1 mês para o entendimento dos dados, poderia ter se iniciado a busca pelas respostas
  neste estágio, porém se poderia carregar logo 24 meses (2 ciclos) para a comparação.
- **Decisão:** Carregar 2 ciclos completos de 12 meses de reclamações, para depois responder as perguntas.
- **Alternativas:** Começar a responder as perguntas apenas utilizado o mês de teste.
- **Impacto:** Início da resolução das perguntas adiado; Observação sobre os valores totais; Comparação entre os mesmos meses em ciclos diferentes.


## D-004 · Descartar as 2 colunas extras de 2025/09
- **Data:** 27/10/2026
- **Contexto:** O arquivo de 2025/09 veio com `Interação com Judiciário` e `Último Complemento Consumidor`; as demais colunas coincidem em nome e ordem.
- **Decisão:** Descartar as duas, por não serem usadas nas perguntas.
- **Alternativas:** Adicionar as colunas a todos os meses com NULL.
- **Impacto:** Nenhuma pergunta depende delas. Se virarem relevantes, é preciso reprocessar o CSV original de 2025/09.


## D-005 · Criar Índices para facilitar a busca
- **Data:** 31/10/2026
- **Contexto:** As análises estavam demorando bastante devido ao volume de dados.
- **Decisão:** Criar índices para acelerar esse processo.
- **Alternativas:** Continuar sem índices.
- **Impacto:** As buscas ficaram mais rápidas, mas a inserção provavelmente ficou mais lenta.


## D-006 · Flag para o período de prazo estendido
- **Data:** 02/11/2026
- **Contexto:** Duas janelas de ~60 dias (aprox. 2025/11 A 2026/01 e 2026/05 a 2026/07 ) têm respostas de até 15 dias; causa não identificada  (ver `notas.md`, "Tempo de resposta").
- **Decisão:** Criar a view `ocorrencias_analise` com `periodo_prazo_estendido`, `tempo_atipico` (> 15)
  e `tempo_resposta_valido` e rodar a pergunta 3 com e sem esses meses, devido ao fato de não ter datas referentes a abertura não foi possível fazer uma análise de possíveis causas.
- **Alternativas:** Excluir os meses; cortar os valores acima de 10.
- **Impacto:** Nenhum dado é perdido; as datas das janelas são aproximadas.


## D-007 · Tratamento dos valores negativos
- **Data:** 02/11/2026
- **Contexto:** Dois valores negativos no tempo_resposta.
- **Decisão:** Definir ambos como NULL na VIEW criada, deixando os valores originais intactos.
- **Alternativas:** Não alterar eles; excluir linhas; usar o valor absoluto.
- **Impacto:** Interferência de dois valores impossíveis, com tão poucos casos não muda o resultado referente.


## D-008 · Analisar todas as avaliadas, respondidas ou não
- **Data:** 04/11/2026
- **Contexto:** Em certo momento durante a análise se foi feito o questionamento se as análises seriam feitas apenas sobre as reclamações 
  que foram respondidas.
- **Decisão:** Foi decidido utilizar ambos, os respondida = 'S' e 'N', pois o indicador mede a percepção do consumidor, e descartar essas  avaliações seria jogar fora opiniões legítimas.
- **Alternativas:** Utilizar o apenas as reclamações respondidas.
- **Impacto:** Adição de mais dados e menor necessidade de filtros na pesquisa.


## D-009 · Utilizar o intervalo de Wilson em vez da taxa bruta para a pergunta 1
- **Data:** 04/11/2026
- **Contexto:** Durante o inicio do projeto se foi cogitado fazer a análise utiliziando apenas a divisão bruta de percebida = reclamações  avaliadas como "Resolvida" ÷ reclamações avaliadas, porém foi percebido a oportunidade de se usar o intervalo de Wilson.
- **Decisão:** O intervalo de Wilson foi adotado para fazer a análise dos dados.
- **Alternativas:** Fazer a divisão bruta.
- **Impacto:** O ranking passa a ser pelo limite inferior (melhores) e superior (piores), e segmentos com poucas avaliações, como Bares com 0 em  2, deixam de aparecer como extremos.


## D-010 · ---
- **Data:**
- **Contexto:**
- **Decisão:** 
- **Alternativas:**
- **Impacto:**


## D-11 · ---
- **Data:**
- **Contexto:**
- **Decisão:** 
- **Alternativas:**
- **Impacto:**



## D-00 · ---
- **Data:**
- **Contexto:**
- **Decisão:** 
- **Alternativas:**
- **Impacto:**