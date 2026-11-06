"""Pergunta 5: como a taxa de resolução evolui? Por que ela caiu entre o início e o fim?

Compara dois recortes de 3 meses, por segmento:
    inicio = out-dez/2024      fim = jul-set/2026
Etapas:
    1. taxa e intervalo de Wilson em cada período
    2. diferença (fim - início) com intervalo de Newcombe -> queda clara / alta clara / inconclusivo
    3. decomposição da queda geral: efeito DENTRO dos segmentos vs. efeito de COMPOSIÇÃO (mix)

Saída:
    outputs/segmentos_inicio_fim.csv
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import text
from statsmodels.stats.proportion import proportion_confint

from db import get_engine

OUT = Path(__file__).resolve().parent.parent / "outputs"
OUT.mkdir(exist_ok=True)

INICIO_ATE = "2024-12"
FIM_A_PARTIR = "2026-07"

engine = get_engine()

# ---------- dados ----------
df = pd.read_sql(
    text("""
        WITH base AS (
          SELECT segmento_de_mercado,
                 CASE WHEN ano_mes <= :inicio_ate THEN 'inicio'
                      WHEN ano_mes >= :fim_a_partir THEN 'fim' END AS periodo,
                 avaliacao_reclamacao
          FROM ocorrencias_analise
          WHERE avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')
        )
        SELECT segmento_de_mercado, periodo,
               COUNT(*) AS avaliadas,
               COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida') AS resolvidas
        FROM base
        WHERE periodo IS NOT NULL
        GROUP BY segmento_de_mercado, periodo
    """),
    engine,
    params={"inicio_ate": INICIO_ATE, "fim_a_partir": FIM_A_PARTIR},
)

w = df.pivot(index="segmento_de_mercado", columns="periodo", values=["avaliadas", "resolvidas"])
w.columns = [f"{a}_{p}" for a, p in w.columns]
print("Segmentos que faltam em algum período:", w.isna().any(axis=1).sum())
w = w.dropna()

# ---------- 1) taxa e Wilson em cada período ----------
for p in ["inicio", "fim"]:
    w[f"taxa_{p}"] = w[f"resolvidas_{p}"] / w[f"avaliadas_{p}"]
    w[f"li_{p}"], w[f"ls_{p}"] = proportion_confint(
        w[f"resolvidas_{p}"], w[f"avaliadas_{p}"], alpha=0.05, method="wilson"
    )

# ---------- 2) diferença fim - início com IC de Newcombe ----------
d = w["taxa_fim"] - w["taxa_inicio"]
w["dif_pp"] = d * 100
w["dif_inf"] = (d - np.sqrt((w.taxa_fim - w.li_fim) ** 2 + (w.ls_inicio - w.taxa_inicio) ** 2)) * 100
w["dif_sup"] = (d + np.sqrt((w.ls_fim - w.taxa_fim) ** 2 + (w.taxa_inicio - w.li_inicio) ** 2)) * 100
w["leitura"] = np.select([w.dif_sup < 0, w.dif_inf > 0], ["queda clara", "alta clara"], "inconclusivo")
print(w["leitura"].value_counts())

# ---------- 3) composição: e se o mix de segmentos do fim fosse o do início? ----------
w["share_ini"] = w.avaliadas_inicio / w.avaliadas_inicio.sum()
w["share_fim"] = w.avaliadas_fim / w.avaliadas_fim.sum()

taxa_ini_geral = w.resolvidas_inicio.sum() / w.avaliadas_inicio.sum()
taxa_fim_geral = w.resolvidas_fim.sum() / w.avaliadas_fim.sum()
taxa_fim_mix_inicio = (w.share_ini * w.taxa_fim).sum()
print(
    f"Início: {taxa_ini_geral:.1%} | Fim: {taxa_fim_geral:.1%} | "
    f"Fim com o mix do início: {taxa_fim_mix_inicio:.1%}"
)

# Checagem com o outro peso de referência (a divisão dentro/mix depende do peso escolhido)
taxa_ini_mix_fim = (w.share_fim * w.taxa_inicio).sum()
print(f"Início com o mix do fim: {taxa_ini_mix_fim:.1%}")

# Contribuição de cada segmento (as colunas somam a queda total):
#   dentro = efeito da mudança da taxa dentro do segmento
#   mix    = efeito da mudança do peso do segmento
w["contrib_dentro_pp"] = w.share_ini * (w.taxa_fim - w.taxa_inicio) * 100
w["contrib_mix_pp"] = (w.share_fim - w.share_ini) * (w.taxa_fim - taxa_fim_geral) * 100
w["contrib_total_pp"] = w.contrib_dentro_pp + w.contrib_mix_pp
print(
    f"Soma dentro: {w.contrib_dentro_pp.sum():.1f} pp | "
    f"soma mix: {w.contrib_mix_pp.sum():.1f} pp | "
    f"total: {w.contrib_total_pp.sum():.1f} pp"
)

cols = [
    "avaliadas_inicio", "avaliadas_fim", "taxa_inicio", "taxa_fim",
    "contrib_dentro_pp", "contrib_mix_pp", "contrib_total_pp", "leitura",
]
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
print(w.sort_values("contrib_total_pp")[cols].head(10).round(3))

# ---------- saída ----------
w.sort_values("contrib_total_pp")[cols].round(4).to_csv(OUT / "segmentos_inicio_fim.csv")