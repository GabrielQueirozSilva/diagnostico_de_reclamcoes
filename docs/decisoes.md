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
| D-013 | Comparar respondidas e não respondidas dentro de estratos | aceita |
| D-014 | Reportar a pergunta 3 por faixa e por segmento, com efeito fixo de mês | aceita |

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
- **Data:** 07/11/2026
- **Contexto:** O script original usava dropna() e descartava segmentos ausentes em um dos períodos. Entre empresas isso é comum (nos bancos, 106 entraram e 10 saíram entre os períodos).
- **Decisão:** Classificar cada entidade como estável, entrou ou saiu, com entrada e saída como termos próprios da decomposição (função decompor em decomposicao.py, usada por segmentos e empresas). Wilson e Newcombe só para estáveis com pelo menos 30 avaliadas nos dois períodos (MIN_AVAL).
- **Alternativas:** dropna() (a taxa geral passa a considerar só quem existe nos dois períodos); restringir a análise às empresas estáveis.
- **Impacto:** As contribuições fecham com a variação observada (há um assert no código). Limite: empresa com volume minúsculo no início (ex.: 6 avaliadas) conta como estável, embora na prática seja entrante.

## D-013 · Comparar respondidas e não respondidas dentro de estratos
- **Data:** 11/11/2026
- **Contexto:** Os casos N (3,2% das avaliadas) se concentram em segmentos e empresas com resolução mais baixa, então a diferença bruta (+24,0 pp) mistura efeito da resposta com composição. Também era preciso saber se a queda da taxa geral vem do aumento dos casos N.
- **Decisão:** Reportar a diferença bruta (Wilson e Newcombe) e comparar dentro de estratos (segmento, mês, segmento × mês, empresa), com odds ratio de Mantel-Haenszel e diferença padronizada pelos pesos dos casos N. Entram só estratos com pelo menos 30 avaliadas em cada grupo (MIN_POR_GRUPO), o que cobre 87% dos casos N no nível empresa. Para a queda, reaproveitar decompor da P5 com a entidade sendo respondida = S ou N, nos mesmos recortes da D-010.
- **Alternativas:** apenas a diferença bruta; regressão logística com efeitos fixos.
- **Impacto:** A diferença cai de 24,0 para 18,5 pp (empresa) e o odds ratio fica entre 2,75 e 3,24. Na queda de −13,7 pp, o peso de N explica só 4% (1,5% a 4,4% nos 6 recortes); ~95% vem de dentro dos casos respondidos. A conclusão é uma associação, não causal, e a heterogeneidade entre estratos é grande (de ~9 a ~52 pp por segmento).

## D-014 · Reportar a pergunta 3 por faixa e por segmento, com efeito fixo de mês 
- **Data:** 12/11/2026
- **Contexto:** O OR bruto por dia de espera (1,018) inverte para 0,9885 ao controlar por segmento, e a taxa por faixa tem forma de U invertido no agregado. Em modelos sequenciais, só o segmento (e não o mês nem o prazo estendido) provoca a inversão, e o formato da curva e o sinal diferem entre segmentos.
- **Decisão:** Reportar (1) a taxa por faixa de tempo, com Wilson, e o OR por faixa ajustado por segmento e mês; (2) o OR por dia dentro de cada segmento, ajustado por mês, com heterogeneidade (interação por razão de verossimilhança, Q, I², tau e intervalo de predição); (3) sensibilidade ao prazo estendido (D-006) em cada cenário; (4) nos três maiores segmentos (Bancos, Telecom, Aéreo), OR por dia dentro da empresa (efeito fixo de empresa) com IC robusto a agrupamento por empresa. Só entram segmentos com pelo menos 500 avaliadas (MIN_AVALIADAS_SEG) e o tempo tem teto de 15 dias no termo linear (TETO_DIAS).
- **Alternativas:** um único OR por dia (esconde a mudança de sinal entre segmentos); curva suave por spline (mais flexível, mas difícil de explicar no relatório); controlar por empresa em vez de segmento (mais fiel, mas muito mais lento e com mais estratos pequenos; feito só nos três maiores segmentos).
- **Impacto:** A conclusão deixa de ser um número e passa a ser "o efeito depende do segmento": 17 a 20 dos 38 a 39 segmentos com queda clara (36% a 41% das avaliadas), 7 a 8 com alta (47% a 50%, puxado por Bancos), o resto inconclusivo, com e sem os dias de prazo estendido; intervalo de predição do OR por dia de 0,84 a 1,13. A contagem muda um pouco entre os cenários (segmentos de efeito perto de zero), os maiores mantêm o sinal. No teste por empresa, ~80% do sinal positivo de Bancos vem de composição entre empresas, e a queda em Telecom e Aéreo se mantém dentro da empresa. Limites: associação, não causal; ICs sem correção para agrupamento por empresa; faixa 11-15 confundida com o prazo estendido.


## D-00 · ---
- **Data:**
- **Contexto:**
- **Decisão:** 
- **Alternativas:**
- **Impacto:**