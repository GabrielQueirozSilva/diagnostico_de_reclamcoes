# Atendimento ao consumidor: onde falha e o que se associa à resolução

Análise de [1,9 milhão de reclamações avaliadas] do Consumidor.gov.br (out/2024 a set/2026),
para identificar em quais segmentos o atendimento falha e o que está associado a uma
reclamação ser considerada resolvida pelo consumidor.

> Status: em andamento (pergunta 5 em análise; 4 pendente).

## Perguntas
| # | Pergunta | Status |
|---|----------|--------|
| 1 | Quais segmentos têm menor/maior taxa de resolução? | concluída |
| 2 | Quando a empresa responde, a resolução é maior? | concluída |
| 3 | O tempo de resposta se associa à resolução? | em andamento |
| 4 | Ter procurado a empresa antes muda a chance de resolução? | pendente |
| 5 | Como a taxa evolui ao longo do tempo? | em andamento |

## Dados
- Fonte: dados abertos do Consumidor.gov.br (reclamações finalizadas, um arquivo CSV por mês).
- Período: 24 meses; [5,9 milhões] de reclamações, das quais [32%] foram avaliadas pelo consumidor.
- Os CSVs não estão no repositório. Baixe-os da fonte e salve em `data/` como `finalizadas_AAAA-MM.csv`.

## Principais resultados até agora
- [Uma frase por pergunta concluída, com link para a tabela ou o gráfico.]

P3: o tempo de resposta tem associação pequena e que muda de sinal conforme o segmento (queda clara em 17 a 20 dos 38 a 39 segmentos, alta em 7 a 8; I² ≈ 100%; resultado igual sem o prazo estendido nos maiores segmentos); ver outputs/pergunta_03/p03_seg_floresta.png.

## Como reproduzir
1. Python 3.14.3 e PostgreSQL. `pip install -r requirements.txt`.
2. Copie `.env.exemple` para `.env` e preencha as credenciais do banco.
3. Na raiz do projeto, rode `python -m src.ingestao` para carregar os dados.
4. Execute as análises como módulos, por exemplo:
   - `python -m src.pergunta_01.segmentos`
   - `python -m src.pergunta_02.taxa_resolucao`
   - `python -m src.pergunta_03.associacao`
   - `python -m src.pergunta_03.diagnostico`
   - `python -m src.pergunta_03.por_segmento`
   - `python -m src.pergunta_03.por_empresa`
   - `python -m src.pergunta_05.evolucao`
   - `python -m src.pergunta_05.empresas`
   - `python -m src.pergunta_05.mensal`
   - `python -m src.tempo_resposta.graficos_tempo_resposta`

## Estrutura
- `sql/` criação das tabelas, índices, view de análise e queries
- `src/` scripts compartilhados e análises organizadas por pergunta/tema
- `outputs/` gráficos e tabelas separados por pergunta/tema
- `docs/notas.md` achados e evidências · `docs/decisoes.md` decisões e motivos

## Limitações
- Só reclamações avaliadas (mede a resolução percebida; difere do índice oficial da plataforma).
- [Lembrar de botar outras limitações depois (quando terminar tudo).]

## Tecnologias
Python 3.14.3 (pandas, SQLAlchemy, statsmodels, matplotlib), PostgreSQL, Power BI.