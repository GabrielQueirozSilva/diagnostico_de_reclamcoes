CREATE VIEW ocorrencias_analise AS
SELECT o.*,
       (data_finalizacao BETWEEN '2025-11-27' AND '2026-01-26'
        OR data_finalizacao BETWEEN '2026-05-12' AND '2026-07-09') AS periodo_prazo_estendido,
       (tempo_resposta > 15) AS tempo_atipico,
       CASE WHEN tempo_resposta >= 0 THEN tempo_resposta END AS tempo_resposta_valido
FROM ocorrencias o;