"""Pergunta 2: quando a empresa responde, a resolução percebida é maior?

Compara a taxa de resolução (resolvidas / avaliadas) entre respondida = 'S' e 'N'.
Etapas:
    1. Bruto: taxa e Wilson em cada grupo; diferença (S - N) com intervalo de Newcombe
    2. Ajustado: a mesma diferença DENTRO de estratos, para tirar o efeito de
       composição (a taxa cai ao longo do tempo e varia muito por segmento):
         - segmento | mês | segmento x mês | empresa
       Para cada estrato: odds ratio de Mantel-Haenszel, teste CMH, teste de
       heterogeneidade (Breslow-Day) e diferença padronizada em pontos percentuais
       (pesos = distribuição dos casos 'N': "se os N tivessem sido respondidos")
    3. Decomposição da queda geral (mesmos recortes da pergunta 5, D-010): a taxa geral é
       (1 - w) * taxa_S + w * taxa_N, com w = peso de N. Usa `decompor` da pergunta 5 com a
       "entidade" sendo respondida = S ou N: o efeito DENTRO de cada grupo (a taxa do próprio
       grupo mudou) vs. o MIX (o peso de N mudou). Reporta o mix com o peso do início e do fim.
    4. Gráficos: diferença por segmento e taxa S x N por mês

Saídas:
    outputs/pergunta_02/p02_segmentos.csv
    outputs/pergunta_02/p02_meses.csv
    outputs/pergunta_02/p02_decomposicao.csv
    outputs/pergunta_02/p02_dif_por_segmento.png
    outputs/pergunta_02/p02_taxa_por_mes.png

Obs.: a view serve apenas para filtrar avaliadas; a pergunta não usa tempo_resposta,
então as flags de prazo estendido não entram aqui (entram na pergunta 3).
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sqlalchemy import text
from statsmodels.stats.contingency_tables import StratifiedTable
from statsmodels.stats.proportion import proportion_confint

from src.db import get_engine
from src.pergunta_05.decomposicao import decompor
from src.pergunta_05.evolucao import FIM_ATE, FIM_A_PARTIR, INICIO_ATE, INICIO_DE, JANELAS, inverter

OUT = Path(__file__).resolve().parents[2] / "outputs" / "pergunta_02"
OUT.mkdir(parents=True, exist_ok=True)

MIN_POR_GRUPO = 30       # mínimo de avaliadas em S e em N para um estrato entrar
MIN_N_GRAFICO = 100      # mínimo de avaliadas em N para o segmento aparecer no gráfico

engine = get_engine()

# ---------- dados (menor granularidade; o resto agrega no pandas) ----------
df = pd.read_sql(text("""
    SELECT segmento_de_mercado, nome_fantasia, ano_mes, respondida,
           COUNT(*) AS avaliadas,
           COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida') AS resolvidas
    FROM ocorrencias_analise
    WHERE avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')
      AND respondida IN ('S', 'N')
    GROUP BY segmento_de_mercado, nome_fantasia, ano_mes, respondida
"""), engine)


# ---------- funções ----------
def newcombe(r1, n1, r0, n0):
    """Diferença p1 - p0 (em pp) com IC de 95% de Newcombe (Wilson nos dois lados)."""
    p1, p0 = r1 / n1, r0 / n0
    l1, u1 = proportion_confint(r1, n1, alpha=0.05, method="wilson")
    l0, u0 = proportion_confint(r0, n0, alpha=0.05, method="wilson")
    d = p1 - p0
    inf = d - np.sqrt((p1 - l1) ** 2 + (u0 - p0) ** 2)
    sup = d + np.sqrt((u1 - p1) ** 2 + (p0 - l0) ** 2)
    return d * 100, inf * 100, sup * 100


def agrupar(base, chaves):
    g = base.groupby(chaves + ["respondida"])[["avaliadas", "resolvidas"]].sum()
    g = g.unstack("respondida", fill_value=0)
    g.columns = [f"{a}_{r}" for a, r in g.columns]
    return g


def comparar(g, minimo=MIN_POR_GRUPO):
    g = g[(g.avaliadas_S >= minimo) & (g.avaliadas_N >= minimo)].copy()
    g["taxa_S"] = g.resolvidas_S / g.avaliadas_S
    g["taxa_N"] = g.resolvidas_N / g.avaliadas_N
    g["dif_pp"], g["dif_inf"], g["dif_sup"] = newcombe(
        g.resolvidas_S, g.avaliadas_S, g.resolvidas_N, g.avaliadas_N
    )
    g["leitura"] = np.select(
        [g.dif_inf > 0, g.dif_sup < 0], ["S maior", "N maior"], "inconclusivo"
    )
    return g


def resumo(nome, g, total_N):
    """Resumo ajustado por estratos."""
    tabs = [
        np.array([[r.resolvidas_S, r.avaliadas_S - r.resolvidas_S],
                  [r.resolvidas_N, r.avaliadas_N - r.resolvidas_N]])
        for r in g.itertuples()
    ]
    st = StratifiedTable(tabs)
    or_mh = st.oddsratio_pooled
    or_inf, or_sup = st.oddsratio_pooled_confint()
    p_cmh = st.test_null_odds(correction=True).pvalue
    try:
        p_het = st.test_equal_odds(adjust=True).pvalue
    except Exception:
        p_het = float("nan")

    # diferença padronizada: pesos = distribuição dos casos N entre os estratos
    w = g.avaliadas_N / g.avaliadas_N.sum()
    dif = (w * (g.taxa_S - g.taxa_N)).sum() * 100
    var = (w ** 2 * (g.taxa_S * (1 - g.taxa_S) / g.avaliadas_S
                     + g.taxa_N * (1 - g.taxa_N) / g.avaliadas_N)).sum()
    ep = np.sqrt(var) * 100
    cobertura = g.avaliadas_N.sum() / total_N

    print(
        f"\n[{nome}] estratos usados: {len(g):,} | cobre {cobertura:.1%} das avaliadas N\n"
        f"  diferença padronizada (S - N): {dif:+.1f} pp  (IC 95%: {dif - 1.96 * ep:+.1f} a {dif + 1.96 * ep:+.1f})\n"
        f"  odds ratio Mantel-Haenszel: {or_mh:.2f}  (IC 95%: {or_inf:.2f} a {or_sup:.2f}) | p CMH = {p_cmh:.3g}\n"
        f"  heterogeneidade entre estratos (Breslow-Day): p = {p_het:.3g}\n"
        f"  estratos com S maior / N maior / inconclusivo: "
        f"{(g.leitura == 'S maior').sum()} / {(g.leitura == 'N maior').sum()} / {(g.leitura == 'inconclusivo').sum()}"
    )


# ---------- 1) bruto ----------
tot = df.groupby("respondida")[["avaliadas", "resolvidas"]].sum()
tot["taxa_pct"] = (tot.resolvidas / tot.avaliadas * 100).round(1)
tot["ic_inf_pct"], tot["ic_sup_pct"] = [
    (x * 100).round(1)
    for x in proportion_confint(tot.resolvidas, tot.avaliadas, alpha=0.05, method="wilson")
]
print("Bruto, por respondida:")
print(tot)
d, i, s = newcombe(tot.loc["S", "resolvidas"], tot.loc["S", "avaliadas"],
                   tot.loc["N", "resolvidas"], tot.loc["N", "avaliadas"])
print(f"Diferença bruta (S - N): {d:+.1f} pp (IC 95% de Newcombe: {i:+.1f} a {s:+.1f})")
print(f"Casos N: {tot.loc['N', 'avaliadas'] / tot.avaliadas.sum():.1%} das avaliadas")

total_N = tot.loc["N", "avaliadas"]

# ---------- 2) ajustado ----------
seg = comparar(agrupar(df, ["segmento_de_mercado"]))
mes = comparar(agrupar(df, ["ano_mes"]))
seg_mes = comparar(agrupar(df, ["segmento_de_mercado", "ano_mes"]))
emp = comparar(agrupar(df, ["nome_fantasia"]))

resumo("por segmento", seg, total_N)
resumo("por mês", mes, total_N)
resumo("por segmento x mês", seg_mes, total_N)
resumo("por empresa", emp, total_N)

# volume de N ao longo do tempo (mudou o peso de N no tempo?)
share_n = agrupar(df, ["ano_mes"])
share_n["pct_N_das_avaliadas"] = (
    share_n.avaliadas_N / (share_n.avaliadas_N + share_n.avaliadas_S) * 100
).round(2)
print("\n% de avaliadas que são 'N', por mês:")
print(share_n["pct_N_das_avaliadas"].to_string())

# ---------- 3) decomposição da queda geral: peso de N x taxa de cada grupo ----------
def decompor_por_grupo(base, inicio_de, inicio_ate, fim_de, fim_ate):
    """Mesma conta da pergunta 5 (`decompor`), com a entidade sendo respondida = S ou N.
    dentro = mudança da taxa do próprio grupo; mix = mudança do peso de N na base."""
    periodo = np.where(
        base.ano_mes.between(inicio_de, inicio_ate), "inicio",
        np.where(base.ano_mes.between(fim_de, fim_ate), "fim", ""),
    )
    b = base.assign(periodo=periodo)
    g = (b[b.periodo != ""].groupby(["respondida", "periodo"])[["avaliadas", "resolvidas"]]
         .sum().unstack("periodo", fill_value=0))
    g.columns = [f"{a}_{p}" for a, p in g.columns]
    w = g[["avaliadas_inicio", "resolvidas_inicio", "avaliadas_fim", "resolvidas_fim"]].astype(int)
    t, r = decompor(w)
    _, r_inv = decompor(inverter(w))  # inverte início e fim: repete a conta com o peso do fim
    return w, t, r, r_inv


linhas = []
for nome, a, b, c, d in JANELAS:
    w, t, r, r_inv = decompor_por_grupo(df, a, b, c, d)
    v = r["variacao_pp"]
    mix_ini, mix_fim = r["mix_pp"], -r_inv["mix_pp"]
    linhas.append({
        "janela": nome,
        "taxa_inicio_%": r["taxa_inicio"] * 100,
        "taxa_fim_%": r["taxa_fim"] * 100,
        "variacao_pp": v,
        "peso_N_inicio_%": w.loc["N", "avaliadas_inicio"] / w.avaliadas_inicio.sum() * 100,
        "peso_N_fim_%": w.loc["N", "avaliadas_fim"] / w.avaliadas_fim.sum() * 100,
        "dentro_S_pp": t.loc["S", "contrib_dentro_pp"],
        "dentro_N_pp": t.loc["N", "contrib_dentro_pp"],
        "mix_peso_inicio_pp": mix_ini,
        "mix_peso_fim_pp": mix_fim,
        "mix_%_da_variacao_min": min(mix_ini / v, mix_fim / v) * 100,
        "mix_%_da_variacao_max": max(mix_ini / v, mix_fim / v) * 100,
    })
decomp = pd.DataFrame(linhas).round(2)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 60)
print("\nDecomposição da queda geral: efeito do peso de N (mix) vs. efeito dentro de S e de N")
print("(dentro_S e dentro_N com o peso do início; mix com o peso do início e do fim)")
print(decomp.to_string(index=False))

# ---------- saídas ----------
decomp.to_csv(OUT / "p02_decomposicao.csv", index=False)
cols =["avaliadas_S", "avaliadas_N", "taxa_S", "taxa_N", "dif_pp", "dif_inf", "dif_sup", "leitura"]
seg.sort_values("dif_pp")[cols].round(4).to_csv(OUT / "p02_segmentos.csv")
mes[cols].round(4).to_csv(OUT / "p02_meses.csv")

# ---------- gráfico 1: diferença por segmento ----------
g1 = seg[seg.avaliadas_N >= MIN_N_GRAFICO].sort_values("dif_pp").reset_index()
fig, ax = plt.subplots(figsize=(10, 0.32 * len(g1) + 1.5))
ax.errorbar(
    g1["dif_pp"], g1.index,
    xerr=[g1["dif_pp"] - g1["dif_inf"], g1["dif_sup"] - g1["dif_pp"]],
    fmt="o", capsize=3,
)
ax.axvline(0, linestyle="--", color="gray")
ax.set_yticks(g1.index)
ax.set_yticklabels(
    [f"{s} (n_N={format(n, ',d').replace(',', '.')})" for s, n in zip(g1["segmento_de_mercado"], g1["avaliadas_N"])],
    fontsize=8,
)
ax.set_ylim(-1, len(g1))
ax.set_xlabel("Diferença na taxa de resolução, S − N (pp, IC 95%)")
plt.tight_layout()
plt.savefig(OUT / "p02_dif_por_segmento.png", dpi=150)
plt.close()

# ---------- gráfico 2: taxa S x N por mês ----------
m = agrupar(df, ["ano_mes"])
m = m[(m.avaliadas_S >= MIN_POR_GRUPO) & (m.avaliadas_N >= MIN_POR_GRUPO)]  # mesmo filtro do CSV (tira 2024-10)
fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(m.index, m.resolvidas_S / m.avaliadas_S * 100, marker="o", label="Respondida (S)")
ax.plot(m.index, m.resolvidas_N / m.avaliadas_N * 100, marker="o", label="Não respondida (N)")
ax.set_ylabel("Taxa de resolução (%)")
ax.set_title("Taxa de resolução por mês, segundo a empresa ter respondido")
ax.legend()
plt.xticks(rotation=60, ha="right")
plt.tight_layout()
plt.savefig(OUT / "p02_taxa_por_mes.png", dpi=150)
plt.close()

print("\nGerados: p02_segmentos.csv, p02_meses.csv, p02_decomposicao.csv, p02_dif_por_segmento.png, p02_taxa_por_mes.png")