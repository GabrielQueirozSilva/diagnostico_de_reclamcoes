"""Pergunta 1: quais segmentos têm maior e menor taxa de resolução?

Taxa = resolvidas / avaliadas, por segmento (24 meses), com intervalo de 95% de Wilson.
A taxa bruta engana em segmentos com poucas avaliações (ex.: 100% com 1 avaliação);
o intervalo de Wilson mostra a faixa de valores plausíveis.

Saídas:
    outputs/segmentos_ic_wilson.png
    outputs/segmentos_wilson.csv
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import text
from statsmodels.stats.proportion import proportion_confint

from db import get_engine

OUT = Path(__file__).resolve().parent.parent / "outputs"
OUT.mkdir(exist_ok=True)

engine = get_engine()

# ---------- dados ----------
df = pd.read_sql(text("""
    SELECT segmento_de_mercado,
           COUNT(*) AS avaliadas,
           COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida') AS resolvidas
    FROM ocorrencias_analise
    WHERE avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')
    GROUP BY segmento_de_mercado
"""), engine)

df["taxa"] = df["resolvidas"] / df["avaliadas"]
df["ic_inf"], df["ic_sup"] = proportion_confint(
    df["resolvidas"], df["avaliadas"], alpha=0.05, method="wilson"
)

# ---------- gráfico ----------
taxa_geral = df["resolvidas"].sum() / df["avaliadas"].sum()
d = df.sort_values("taxa").reset_index(drop=True)

fig, ax = plt.subplots(figsize=(10, 0.32 * len(d) + 1.5))
ax.errorbar(
    d["taxa"] * 100, d.index,
    xerr=[(d["taxa"] - d["ic_inf"]) * 100, (d["ic_sup"] - d["taxa"]) * 100],
    fmt="o", capsize=3,
)
ax.axvline(taxa_geral * 100, linestyle="--", color="gray", label=f"Geral: {taxa_geral * 100:.1f}%")
ax.set_yticks(d.index)
ax.set_yticklabels(
    [f"{s} (n={n:,})".replace(",", ".") for s, n in zip(d["segmento_de_mercado"], d["avaliadas"])],
    fontsize=8,
)
ax.set_ylim(-1, len(d))
ax.set_xlabel("Taxa de resolução (%) com IC de 95% (Wilson)")
ax.legend()
plt.tight_layout()
plt.savefig(OUT / "segmentos_ic_wilson.png", dpi=150)
plt.close()

# ---------- tabela ----------
tabela = df.assign(
    taxa_pct=(df["taxa"] * 100).round(1),
    ic_inf_pct=(df["ic_inf"] * 100).round(1),
    ic_sup_pct=(df["ic_sup"] * 100).round(1),
)
tabela["largura_pp"] = (tabela["ic_sup_pct"] - tabela["ic_inf_pct"]).round(1)
tabela = tabela.sort_values("ic_inf_pct", ascending=False)[
    ["segmento_de_mercado", "avaliadas", "resolvidas", "taxa_pct", "ic_inf_pct", "ic_sup_pct", "largura_pp"]
]
tabela.to_csv(OUT / "segmentos_wilson.csv", index=False)


def mostrar(t):
    """Imprime em markdown (precisa do pacote tabulate); se faltar, imprime como texto."""
    try:
        print(t.to_markdown(index=False))
    except ImportError:
        print(t.to_string(index=False))


print("\n5 melhores (ordenados pelo limite inferior do intervalo):")
mostrar(tabela.head(5))
print("\n5 piores (ordenados pelo limite superior do intervalo):")
mostrar(tabela.sort_values("ic_sup_pct").head(5))