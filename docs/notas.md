# Notas do projeto

## Objetivo e indicador

**Objetivo central:** Descobrir onde o atendimento ao consumidor falha e o que está associado a uma reclamação ser considerada resolvida, usando 24 meses de dados do Consumidor.gov.br (out/2024 a set/2026) 

**Indicador principal:** taxa de resolução percebida = reclamações avaliadas como "Resolvida" ÷ reclamações avaliadas.

## Escopo e limitações

- Período: out/2024 a set/2026 (24 meses fechados, 5.930.527 dados totais).
- Apenas reclamações avaliadas pelo consumidor: 32% do total nos 24 meses (1.897.927 dados).
- Mede a resolução **percebida pelo consumidor**, não o desempenho objetivo da empresa.
- Difere do índice oficial da plataforma, que conta como resolvida a reclamação não avaliada. Por isso os números aqui não vão bater com os do Perfil do Fornecedor.
- A análise de tempo de resposta usa só reclamações respondidas (`respondida = 'S'`, 5.679.864 dados totais), porque o campo é nulo nas demais.

## Perguntas

| # | Pergunta | Status |
|---|----------|--------|
| 1 | Quais segmentos têm menor/maior taxa de resolução? | concluida |
| 2 | Quando a empresa responde, a resolução é maior? | pendente |
| 3 | O tempo de resposta se associa à resolução? | pendente |
| 4 | Ter procurado a empresa antes muda a chance de resolução? | pendente |
| 5 | Como a taxa evolui mês a mês? | em andamento |

## Resultados

### Pergunta 1: segmentos com maior e menor taxa de resolução (concluída)
- **Método:** taxa = resolvidas ÷ avaliadas por segmento (24 meses, 1.897.927 avaliadas), com intervalo
  de 95% de Wilson. Melhores ordenados pelo limite inferior e piores pelo superior [ver D-010](decisoes.md).
- **Gráfico:** `outputs/segmentos_ic_wilson.png`. **Tabela completa:** `outputs/segmentos_wilson.csv`.

**Maiores taxas**
| segmento_de_mercado                                                     |   avaliadas |   resolvidas |   taxa_pct |   ic_inf_pct |   ic_sup_pct |   largura_pp |
|:------------------------------------------------------------------------|------------:|-------------:|-----------:|-------------:|-------------:|-------------:|
| Operadoras de Telecomunicações (Telefonia, Internet, TV por assinatura) |      208.706 |       148.491 |       71.1% |         71% |         71.3% |          0.3 |
| Transporte Aéreo                                                        |      115.391 |        74.616 |       64.7% |         64.4% |         64.9% |          0.5 |
| Programas de Fidelidade                                                 |       37.140 |        23.405 |       63%   |         62.5% |         63.5% |          1   |
| Supermercados                                                           |        3.746 |         2.353 |       62.8% |         61.3% |         64.3% |          3   |
| Fabricantes - Móveis, Colchões e Acessórios                             |         339 |          219 |       64.6% |         59.4% |         69.5% |         10.1 |

**Menores taxas**
5 piores (ordenados pelo limite superior do intervalo):
| segmento_de_mercado                                                   |   avaliadas |   resolvidas |   taxa_pct |   ic_inf_pct |   ic_sup_pct |   largura_pp |
|:----------------------------------------------------------------------|------------:|-------------:|-----------:|-------------:|-------------:|-------------:|
| Provedores de Conteúdo e Outros Serviços na Internet                  |       83.608 |        11.677 |       14%   |         13.7% |         14.2% |          0.5 |
| Entidades Sem Fins Lucrativos                                         |         718 |          120 |       16.7% |         14.2% |         19.6% |          5.4 |
| Fabricantes - Eletroeletrônicos,  Produtos de Telefonia e Informática |       37.308 |         7.434 |       19.9% |         19.5% |         20.3% |          0.8 |
| Montadoras, Concessionárias e Prestadores de Serviços Automotivos     |        7.037 |         1.600 |       22.7% |         21.8% |         23.7% |          1.9 |
| Empresas de Recuperação de Crédito                                    |       65.976 |        16.035 |       24.3% |         24%   |         24.6% |          0.6 |

- Telecomunicações (71,1%) e Transporte Aéreo (64,7%) lideram sem sobreposição de intervalos.
  Programas de Fidelidade, Supermercados e Móveis/Colchões ficam tecnicamente empatados do 3º ao 5º lugar.
- Provedores de Conteúdo (14,0%) é o pior com folga; Entidades Sem Fins Lucrativos (16,7%, n=718) vem
  em seguida, com intervalo mais largo.
- Segmentos com poucas avaliações (ex.: Bares, 2 avaliações) ficam sem conclusão.
- **Limitações:** período agregado (a taxa geral caiu ao longo do tempo, ver pergunta 5); só reclamações
  avaliadas; os intervalos não consideram que reclamações da mesma empresa são parecidas entre si.

### Pergunta 5: evolução da taxa (em andamento)
- Taxa geral: 51,9% (out-dez/2024) → 38,2% (jul-set/2026), queda de 13,7 pp.
- ~63% da queda ocorre dentro dos segmentos e ~37% por mudança de composição.
- Dez segmentos explicam quase toda a queda (Bancos/Financeiras e Telecomunicações à frente).
- Pendente: olhar as empresas dentro dos segmentos e o gráfico mês a mês.

## Qualidade dos dados

### 2025/09: colunas extras [Ver D-004](decisoes.md)

O arquivo de 2025/09 veio com 2 colunas a mais: `Interação com Judiciário` e `Último Complemento Consumidor`.

### Tempo de resposta (investigação concluída) [Ver D-006 e D-007](decisoes.md)
- Fora de duas janelas, quase nenhuma resposta passa de 10 dias (máximo 10-11).
- Nas janelas (27/11/2025 a 26/01/2026 e 12/05/2026 a 09/07/2026, ~60 dias cada), dezenas de
  milhares passam de 10 dias, mas praticamente nenhuma de 15 (2026-05 e 2026-07: zero acima de 15).
  Compatível com dois regimes de prazo (10 e 15 dias).
- Critério das janelas: primeiro e último dia de finalização com mais de 5% das respostas acima
  de 10 dias. Datas aproximadas, pois a finalização vem depois da resposta.
- Não é erro de ingestão (as janelas começam e terminam no meio do mês) nem efeito de volume.
- Causa específica não identificada (ocorrencia de aumento para 15 dias encontrado, mas não confirma o caso
  como um todo). Hipótese de prazo de 15 dias não confirmada.
- Fim de 2024 (2024-10 a 12): cauda longa distinta (até 80 dias), que some em 2025-01.
- Impacto: o tempo médio sobe ~1 dia nos meses de pico; a taxa de resolução não muda de forma
  consistente com as janelas.

### Não respondidas com avaliação - Decidido. [Ver D-008](decisoes.md)

Entre as reclamações com `respondida = 'N'`:  190.732 não avaliadas,  49.310 "Não Resolvida" e  10.621 "Resolvida".

**Hipóteses:** 
1. Resposta fora do prazo (perde força: o tempo de resposta é nulo em todos os casos).
2. Resolução por outro canal, sem registro de resposta (possível).
3. Consumidor avalia mesmo sem receber resposta (possível; explicaria as "Não Resolvida").
4. Significado do campo `Respondida`: [dicionário não especifíca sobre].

**Evidências nas 570 "Resolvida":** 424 foram abertas pela internet; 535 (93,86%) já tinham procurado a empresa antes e 35 (6,14%) não. [ATUALIZAR ISSO]
**Cuidado nisso:** o percentual de 94% só distingue algo se for comparado com o mesmo percentual na base geral. [Lembrar de comparar e anotar.]


## Perguntas em aberto

- Por que o tempo de resposta é maior nas resolvidas? Testar dentro de cada segmento **e dentro de cada mês**: se o prazo de resposta mudou ao longo do tempo e a taxa de resolução também, o período pode estar afetando as duas variáveis ao mesmo tempo.
- As empresas do topo do ranking de respostas acima de 10 dias continuam lá quando se excluem os meses de pico?
- Por que a taxa de resolução cai de ~55% para ~38% ao longo dos 24 meses? Testar composição por segmento.
- Conferir o volume menor em 2025-11.

## Anexo: índices

Foram criados índices nas colunas mais usadas em filtros e agrupamentos: `uf`, `data_finalizacao`, `segmento_de_mercado` e `nome_fantasia`. Comandos em `sql/indices.sql`. Avaliar também `ano_mes` e `tempo_resposta`, usados com frequência nas queries.
