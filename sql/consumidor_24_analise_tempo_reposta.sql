-- Taxa por empresa acima de 10

-- SELECT nome_fantasia,
--        COUNT(*) AS respondidas,
--        COUNT(*) FILTER (WHERE tempo_resposta > 10) AS acima_10,
--        ROUND(100.0 * COUNT(*) FILTER (WHERE tempo_resposta > 10) / COUNT(*), 2) AS pct_acima_10
-- FROM ocorrencias
-- WHERE tempo_resposta IS NOT NULL
-- GROUP BY nome_fantasia
-- HAVING COUNT(*) >= 100
-- ORDER BY pct_acima_10 DESC, acima_10 DESC;


-- DIVISÃO POR MES

-- SELECT ano_mes,
--        COUNT(*) AS respondidas,
--        COUNT(*) FILTER (WHERE tempo_resposta > 10) AS acima_10,
--        ROUND(100.0 * COUNT(*) FILTER (WHERE tempo_resposta > 10) / COUNT(*), 2) AS pct_acima_10,
--        MAX(tempo_resposta) AS maximo
-- FROM ocorrencias
-- WHERE tempo_resposta IS NOT NULL
-- GROUP BY ano_mes
-- ORDER BY ano_mes;


-- DIVISÃO POR GRUPO

-- SELECT CASE WHEN tempo_resposta <= 10 THEN '0-10'
--             WHEN tempo_resposta <= 15 THEN '11-15'
--             WHEN tempo_resposta <= 30 THEN '16-30'
--             ELSE '31+' END AS faixa,
--        COUNT(*) AS qtd,
--        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
-- FROM ocorrencias
-- WHERE tempo_resposta IS NOT NULL
-- GROUP BY 1
-- ORDER BY 1;


--Em cada mês, quanto das respostas acima de 10 dias vem das 5 maiores empresas nesse quesito

-- WITH m AS (
--   SELECT ano_mes, nome_fantasia,
--          COUNT(*) FILTER (WHERE tempo_resposta > 10) AS acima_10
--   FROM ocorrencias
--   WHERE tempo_resposta IS NOT NULL
--   GROUP BY ano_mes, nome_fantasia
-- ),
-- r AS (
--   SELECT *,
--          ROW_NUMBER() OVER (PARTITION BY ano_mes ORDER BY acima_10 DESC) AS rn,
--          SUM(acima_10) OVER (PARTITION BY ano_mes) AS total
--   FROM m
-- )
-- SELECT ano_mes,
--        MAX(total) AS total_acima_10,
--        ROUND(100.0 * SUM(acima_10) FILTER (WHERE rn <= 5) / NULLIF(MAX(total), 0), 1) AS pct_top5
-- FROM r
-- GROUP BY ano_mes
-- ORDER BY ano_mes;

--DISTRIBUIÇÃO DE UM MÊS NO PICO

-- SELECT tempo_resposta, COUNT(*) AS qtd
-- FROM ocorrencias
-- WHERE ano_mes = '2026-06' AND tempo_resposta IS NOT NULL
-- GROUP BY tempo_resposta
-- ORDER BY tempo_resposta;


--Vendo se a taxa muda de forma abrupta em alguma data:

-- SELECT data_finalizacao AS dia,
--        COUNT(*) AS respondidas,
--        COUNT(*) FILTER (WHERE tempo_resposta > 10) AS acima_10,
--        ROUND(100.0 * COUNT(*) FILTER (WHERE tempo_resposta > 10) / COUNT(*), 2) AS pct_acima_10
-- FROM ocorrencias
-- WHERE tempo_resposta >= 0
--   AND ano_mes BETWEEN '2025-10' AND '2026-08'
-- GROUP BY data_finalizacao
-- ORDER BY data_finalizacao;


--Verificação das data de inicio e fim de cada janel

-- SELECT MIN(data_finalizacao) AS inicio, MAX(data_finalizacao) AS fim
-- FROM (
--   SELECT data_finalizacao,
--          100.0 * COUNT(*) FILTER (WHERE tempo_resposta > 10) / COUNT(*) AS pct
--   FROM ocorrencias
--   WHERE tempo_resposta >= 0
--   GROUP BY data_finalizacao
-- ) t
-- WHERE pct > 5 AND data_finalizacao BETWEEN '2025-10-01' AND '2026-03-01';