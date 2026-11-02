--TAXA DE RESOLVIDAS (TEM COMO DENOMINADOR O TOTAL DE RECLAMAÇÕES, INCUSLO OS NULOS)
SELECT
    segmento_de_mercado,
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida') AS resolvidas,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida')
        / COUNT(*), 1
    ) AS taxa_resolucao_pct
FROM ocorrencias
GROUP BY segmento_de_mercado
ORDER BY taxa_resolucao_pct DESC;