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
| 5 | Como a taxa evolui mês a mês? | concluida | |

## Resultados

### Pergunta 1: segmentos com maior e menor taxa de resolução (concluída)
- **Método:** taxa = resolvidas ÷ avaliadas por segmento (24 meses, 1.897.927 avaliadas), com intervalo
  de 95% de Wilson. Melhores ordenados pelo limite inferior e piores pelo superior [ver D-009](decisoes.md).
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

### Pergunta 5: evolução da taxa (concluído)
- **Método:** recortes de 3 meses (out-dez/2024 e jul-set/2026), decomposição em dentro, mix, entrada e saída (ver D-010, D-011 e D-012). 
- **Scripts:** pergunta_05_evolucao.py (segmentos), pergunta_05_empresas.py (empresas dentro dos segmentos) e pergunta_05_mensal.py (mês a mês).
- **Taxa geral:** 51,9% (out-dez/2024) → 38,2% (jul-set/2026), queda de 13,7 pp.
- **Segmentos:** o efeito dentro dos segmentos é de −8,8 pp (peso do início) a −9,8 pp (peso do fim), ou seja, 64% a 71% da queda de −13,7 pp; o restante (29% a 36%) é composição. Os 10 primeiros segmentos explicam 99% da variação. 42 segmentos existem nos dois períodos, 2 só no fim e 1 só no início, sem efeito material (entrada e saída ≈ 0).

- No nível geral, Telecom pesa mais por composição (mix −1,95 pp) do que por queda própria (dentro −1,09 pp): é um segmento de taxa alta (70,6%) que perdeu peso no total. Bancos é o contrário (dentro −3,16 pp, mix −0,71 pp).

**Dentro dos 3 segmentos que mais pesam** (outputs/empresas_*.csv, outputs/empresas_resumo.csv)


| Segmento | Variação | Dentro | Mix | Entrada + saída | Concentração |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Bancos, Financeiras e Adm. Cartão** | 39,2% → 27,5% (−11,7 pp) | −10,0 | −1,4 | −0,3 | 10 de 279 empresas ≈ 63% |
| **Operadoras de Telecomunicações** | 77,7% → 70,6% (−7,1 pp) | −8,9 | +1,9 | ~0 | Vivo + Tim ≈ 80% |
| **Transporte Aéreo** | 71,7% → 58,9% (−12,9 pp) | −10,3 | −2,5 | ~0 | Gol ≈ 48%; Gol + Latam ≈ 71% |


* Nos três, a queda vem sobretudo de empresas que já existiam e perderam taxa; a entrada de empresas pesa quase nada.
* Bancos: queda ampla entre os grandes (Santander 34,2% → 16,5%, Caixa 51,5% → 35,7%, BB 42,8% → 29,4%, Nubank 30,6% → 19,7%, Bradesco 31,7% → 22,8%, Itaú 35,5% → 24,6%). Hipótese a testar: algo comum a vários bancos.
* Telecom: Vivo (83,6% → 71,6%) e Tim (76,3% → 65,0%) concentram a queda; Claro quase estável. A Oi Fixo caiu (72,9% → 45,1%), mas o volume dela encolheu e o mix compensou +1,8 pp.
* Aéreo: Gol de 80,4% → 49,1%.
* **Mês a mês: (outputs/mensal_*.png):** a taxa geral cai de 54,9% (out/2024) para um piso de 35,6% (abr/2026), com recuperação parcial para cerca de 38% em jul-set/2026. Não há degrau único: a maior variação mensal é de 3,5 pp. O fim da comparação (38,2%) já está 2 a 3 pp acima do piso, e o início (51,9%) mistura out/2024 (54,9%) com dez/2024 (49,8%); os 13,7 pp dependem das janelas escolhidas. O % de avaliadas sobre finalizadas oscilou entre cerca de 29% e 38% (início 33,4%, fim 30,7%), com queda atípica em dez/2025 (23,9%) e jan/2026 (25,4%). As finalizadas passaram de 118 mil (out/2024) para 432 mil (jul/2026). Os segmentos caem em momentos diferentes: bancos com degrau em ago/2025, telecom com queda gradual até abr/2026 e aéreo com queda já dentro da janela inicial.
* O volume menor de 2025-11 (192.038 finalizadas) confere com o CSV e com o banco, então vem da fonte e não da ingestão.
* **Cuidados:** "dentro" é a taxa percebida de empresas existentes, não prova atendimento pior (pode refletir tipo de reclamação, canal ou quem avalia). As avaliadas cresceram muito em várias empresas (ex.: Nubank 3.207 → 15.759). O início (out-dez/2024) é o começo da série e tem tempo de resposta atípico (ver "Qualidade dos dados").
* **Empresas mês a mês (outputs/mensal_empresas_*.png;*** valores lidos nos gráficos, aproximados):
* * Bancos: a queda é ampla entre as seis maiores, mas em momentos diferentes. Itaú cai cerca de 9 pp em abr/2025; Nubank vai de ~32% (abr/2025) para ~12% (ago/2025); Santander, Bradesco e Caixa caem em ago/2025. As seis caem de novo em nov/2025 (mês de menor volume e de queda de 3,5 pp na taxa geral).
* * Telecom: Claro Celular fica estável (73% a 80%); a queda está em Vivo (82% a 85% no início, ~75% a 80% em 2025, ~63% em abr-jun/2026, 70% a 72% no fim) e em Tim (~75% em 2025 para ~62% a 65% desde fev/2026). Oi Fixo cai, mas com bandas largas.
* * Aéreo: a queda se concentra na Gol (~70% a 81% em 2025, ~44% em mar/2026, 56% em set/2026). Latam e Azul ficam praticamente estáveis (~70% a 80%).
* * Out/2024 é o ponto mais alto de quase todas as séries (Caixa ~55%, Santander ~39%, BB ~47%, Itaú ~39%, Gol ~88%, Latam ~83%, Vivo ~85%), coerente com o tempo de resposta atípico registrado para esse mês. A janela "início" pode estar inflada por ele.
* **Sensibilidade ao recorte (--sensibilidade, outputs/sensibilidade_recortes.csv):** em 6 recortes (início sem out/24, início jan-mar/25, fim no piso, sem as pontas e 12 meses contra 12 meses), a variação total vai de −8,3 a −16,1 pp, mas a parcela dentro dos segmentos fica entre 62% e 76% (padrão: 64% a 71%). Ano contra ano (12 x 12 meses): 46,2% → 37,9% (−8,3 pp), com 70% a 76% dentro dos segmentos. A conclusão "cerca de dois terços dentro dos segmentos e um terço por composição" é robusta ao recorte; o valor de −13,7 pp não é.
* **Nov/2025 nas seis maiores empresas de bancos** (consulta no pgAdmin, out-dez/2024 e set-dez/2025):
* * A taxa cai em todas em nov/2025 (de 4 a 8 pp em relação a out/2025) e recupera em dez em 5 das 6.
* * As finalizadas caem de 12% a 32% em relação a out/2025 e, em dez/2025, sobem de 47% a 96% em relação a nov, com o % de avaliadas caindo nas seis (ex.: Nubank 11%, BB 15%). 
* * O % de avaliadas não muda de forma consistente em nov/2025 (sobe em BB e Nubank, cai em Bradesco e Itaú, quase não muda em Santander e Caixa).
* * Nov/2024 tem padrão parecido na taxa (cai em relação a out/2024 em 5 das 6 e recupera em dez em 4 das 6), mas com volume subindo de 51% a 100% em relação a out/2024.
* * Compatível com sazonalidade em novembro, mas só há dois novembros; sem explicação definitiva nos dados disponíveis.
* **Volume:** de out-dez/2024 para set-dez/2025, as finalizadas dos cinco bancos tradicionais cresceram cerca de 1,5 a 2,1 vezes e as do Nubank cerca de 4 vezes, enquanto a taxa caiu em todos. Mais reclamações e menor resolução percebida andam juntas, mas isso não indica causa. O tipo de reclamação (assunto e problema) é o corte seguinte natural.
* **Conclusão da pergunta 5:** a taxa de resolução percebida cai de ~55% (out/2024) para um piso de ~36% (abr/2026) e recupera parcialmente (~38% no fim). Cerca de dois terços da queda (62% a 76%, conforme o recorte) ocorrem dentro dos segmentos; o restante é mudança de composição. Dez segmentos explicam quase toda a queda (99% no recorte padrão) e, dentro deles, poucas empresas concentram o efeito (Gol no aéreo, Vivo e Tim no telecom, as seis maiores nos bancos). Os dados descrevem onde e quando a taxa caiu, não por quê.
* **Pendente (ligado às perguntas 2 e 3):** decompor por assunto, tempo de resposta e "empresa respondeu" nas empresas que mais caíram (Gol, Nubank, Santander).

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
