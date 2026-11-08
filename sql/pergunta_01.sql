--COMPARAÇÃO DE RECORTE DE 3 MESES INICIAIS E FINAIS ENTRE SEGMENTOS

-- WITH base AS (
--   SELECT segmento_de_mercado,
--          CASE WHEN ano_mes <= '2024-12' THEN 'inicio'
--               WHEN ano_mes >= '2026-07' THEN 'fim' END AS periodo,
--          avaliacao_reclamacao
--   FROM ocorrencias_analise
--   WHERE avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')
-- )
-- SELECT segmento_de_mercado, periodo,
--        COUNT(*) AS avaliadas,
--        ROUND(100.0 * COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida') / COUNT(*), 1) AS pct_resolvida
-- FROM base
-- WHERE periodo IS NOT NULL
-- GROUP BY segmento_de_mercado, periodo
-- ORDER BY segmento_de_mercado, periodo;

-- CONTAGEM DAS AVALIAS E RESOLVIDAS (UTILZIADA PARA A ANÁLISE WILSON)

-- SELECT segmento_de_mercado,
-- 	   COUNT(*) AS avaliadas,
-- 	   COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida') AS resolvidas
-- FROM ocorrencias_analise
-- WHERE avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')
-- GROUP BY segmento_de_mercado

-- SELECT COUNT(*)
-- FROM ocorrencias
-- WHERE avaliacao_reclamacao = 'Resolvida' OR 
-- avaliacao_reclamacao = 'Nao Resolvida'
