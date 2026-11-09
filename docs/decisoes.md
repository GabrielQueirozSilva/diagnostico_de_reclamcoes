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
| D-010 | Recorte de 3 meses de cada lado da série (início e fim) | aceita |
| D-011 | Decomposição entre efeito dentro dos segmentos e composição | aceita |
| D-012 | Tratar entrada e saída de entidades em vez de descartá-las | aceita |

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


## D-010 · Recorte de 3 meses de cada lado da série
- **Data:** 07/11/2026
- **Contexto:** Para explicar a queda da taxa geral é preciso comparar o começo e o fim da série, com volume suficiente por segmento.
- **Decisão:** Comparar out-dez/2024 (início) com jul-set/2026 (fim), definidos em INICIO_ATE e FIM_A_PARTIR.
- **Alternativas:** 1 mês de cada lado (menos volume por segmento, mais ruído); metades da série (mistura meses muito diferentes); só o gráfico mês a mês (não permite decompor a queda).
- **Impacto:** Volume suficiente na maioria dos segmentos. O início coincide com o começo da série, onde as notas já registram tempo de resposta atípico. A variação total depende do recorte (de −8,3 a −16,1 pp nos 6 recortes testados com --sensibilidade), então o −13,7 pp é um valor do recorte padrão, e não da trajetória toda; a parcela dentro dos segmentos, ao contrário, é estável (62% a 76%).


## D-011 · Decomposição entre efeito dentro dos segmentos e composição
- **Data:** 07/11/2026
- **Contexto:** A taxa geral é uma média ponderada. Ela pode cair porque as taxas caíram dentro dos segmentos ou porque o peso migrou para segmentos com taxa menor.
- **Decisão:** Por segmento, dentro = s0·(r1−r0) e mix = (s1−s0)·(r1−R1) (s = peso, r = taxa do segmento, R1 = taxa geral do fim). As colunas somam a variação total. Como a divisão depende do peso de referência (início ou fim), reportar a faixa obtida com os dois.
- **Alternativas:** Só a variação por segmento (não separa composição); um único peso de referência (o resultado dependeria da escolha).
- **Impacto:** O efeito dentro dos segmentos é de −8,8 a −9,8 pp conforme o peso de referência, isto é, 64% a 71% da queda de −13,7 pp no recorte padrão, e de 62% a 76% nos 6 recortes testados. Os termos descrevem onde a queda aconteceu, não provam a causa.


## D-012 · Tratar entrada e saída de entidades em vez de descartá-las
- **Data:**
- **Contexto:** O script original usava dropna() e descartava segmentos ausentes em um dos períodos. Entre empresas isso é comum (nos bancos, 106 entraram e 10 saíram entre os períodos).
- **Decisão:** Classificar cada entidade como estável, entrou ou saiu, com entrada e saída como termos próprios da decomposição (função decompor em decomposicao.py, usada por segmentos e empresas). Wilson e Newcombe só para estáveis com pelo menos 30 avaliadas nos dois períodos (MIN_AVAL).
- **Alternativas:** dropna() (a taxa geral passa a considerar só quem existe nos dois períodos); restringir a análise às empresas estáveis.
- **Impacto:** As contribuições fecham com a variação observada (há um assert no código). Limite: empresa com volume minúsculo no início (ex.: 6 avaliadas) conta como estável, embora na prática seja entrante.




## D-00 · ---
- **Data:**
- **Contexto:**
- **Decisão:** 
- **Alternativas:**
- **Impacto:**