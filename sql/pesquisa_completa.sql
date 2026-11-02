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


-- SELECT ano_mes,
--        COUNT(*) AS respondidas,
--        COUNT(*) FILTER (WHERE tempo_resposta > 10) AS acima_10,
--        ROUND(100.0 * COUNT(*) FILTER (WHERE tempo_resposta > 10) / COUNT(*), 2) AS pct_acima_10,
--        MAX(tempo_resposta) AS maximo
-- FROM ocorrencias
-- WHERE tempo_resposta IS NOT NULL
-- GROUP BY ano_mes
-- ORDER BY ano_mes;

SELECT CASE WHEN tempo_resposta <= 10 THEN '0-10'
            WHEN tempo_resposta <= 15 THEN '11-15'
            WHEN tempo_resposta <= 30 THEN '16-30'
            ELSE '31+' END AS faixa,
       COUNT(*) AS qtd,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM ocorrencias
WHERE tempo_resposta IS NOT NULL
GROUP BY 1
ORDER BY 1;