"""Pergunta 4: ter procurado a empresa antes muda a chance de resolução?

Compara a taxa de resolução (resolvidas / avaliadas) entre procurou_empresa = 'S' e 'N'.
Mesma estrutura da pergunta 2 (D-013): como segmento e mês afetam tanto a taxa de resolução
quanto o hábito de procurar a empresa, a diferença bruta mistura efeito e composição.
Etapas:
    1. Bruto: taxa e Wilson em cada grupo; diferença (S - N) com intervalo de Newcombe;
       odds ratio bruto
    2. Ajustado: a mesma diferença DENTRO de estratos (segmento | mês | segmento x mês | empresa).
       Para cada estrato: odds ratio de Mantel-Haenszel, teste CMH, heterogeneidade
       (Breslow-Day) e diferença padronizada em pp (pesos = distribuição dos casos 'N':
       "se quem não procurou tivesse procurado")
    3. Por segmento: diferença S - N com Newcombe (gráfico)
    4. Decomposição da queda geral (mesmos recortes da pergunta 5, D-010): o peso de quem
       procurou mudou ao longo do tempo? Usa `decompor` da pergunta 5 com a "entidade"
       sendo procurou_empresa = S ou N (efeito DENTRO de cada grupo vs. MIX)
    5. Pendência da D-008: % de procurou = 'S' entre as "Resolvida" não respondidas, comparada
       com a base geral e com as "Não Resolvida" não respondidas

Uso:
    python -m src.pergunta_04.procurou_empresa

Saídas (em outputs/pergunta_04/):
    p04_geral.csv
    p04_ajustado.csv
    p04_segmentos.csv
    p04_meses.csv
    p04_decomposicao.csv
    p04_d008.csv
    p04_dif_por_segmento.png
    p04_taxa_por_mes.png
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sqlalchemy import text
from statsmodels.stats.contingency_tables import StratifiedTable
from statsmodels.stats.proportion import proportion_confint, proportions_ztest

from src.db import get_engine
from src.pergunta_05.decomposicao import decompor
from src.pergunta_05.evolucao import JANELAS, inverter

OUT = Path(__file__).resolve().parents[2] / "outputs" / "pergunta_04"
OUT.mkdir(parents=True, exist_ok=True)

MIN_POR_GRUPO = 30       # mínimo de avaliadas em S e em N para um estrato entrar (igual à P2)
MIN_N_GRAFICO = 100      # mínimo de avaliadas em N para o segmento aparecer no gráfico

SQL_BASE = text("""
    SELECT segmento_de_mercado, nome_fantasia, ano_mes, procurou_empresa,
           COUNT(*) AS avaliadas,
           COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida') AS resolvidas
    FROM ocorrencias_analise
    WHERE avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')
      AND procurou_empresa IN ('S', 'N')
    GROUP BY segmento_de_mercado, nome_fantasia, ano_mes, procurou_empresa
""")

# quantas avaliadas ficam fora por procurou_empresa ser nulo ou diferente de S/N
SQL_COBERTURA = text("""
    SELECT COALESCE(procurou_empresa, '(nulo)') AS procurou_empresa, COUNT(*) AS avaliadas
    FROM ocorrencias_analise
    WHERE avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')
    GROUP BY 1
""")

SQL_D008 = text("""
    SELECT 'base geral (avaliadas)' AS grupo,
           COUNT(*) AS n,
           COUNT(*) FILTER (WHERE procurou_empresa = 'S') AS procurou_s
    FROM ocorrencias_analise
    WHERE avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida') AND procurou_empresa IN ('S', 'N')
    UNION ALL
    SELECT 'não respondidas + Resolvida', COUNT(*),
           COUNT(*) FILTER (WHERE procurou_empresa = 'S')
    FROM ocorrencias_analise
    WHERE respondida = 'N' AND avaliacao_reclamacao = 'Resolvida' AND procurou_empresa IN ('S', 'N')
    UNION ALL
    SELECT 'não respondidas + Não Resolvida', COUNT(*),
           COUNT(*) FILTER (WHERE procurou_empresa = 'S')
    FROM ocorrencias_analise
    WHERE respondida = 'N' AND avaliacao_reclamacao = 'Não Resolvida' AND procurou_empresa IN ('S', 'N')
""")


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
    """Uma linha por estrato, com colunas avaliadas_S, avaliadas_N, resolvidas_S, resolvidas_N."""
    g = base.groupby(chaves + ["procurou_empresa"])[["avaliadas", "resolvidas"]].sum()
    g = g.unstack("procurou_empresa", fill_value=0)
    g.columns = [f"{a}_{p}" for a, p in g.columns]
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
    """Resumo ajustado por estratos; imprime e devolve uma linha para o CSV."""
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
    except Exception:  # estratos com células zero podem quebrar o teste
        p_het = float("nan")

    # diferença padronizada: pesos = distribuição dos casos N entre os estratos
    w = g.avaliadas_N / g.avaliadas_N.sum()
    dif = (w * (g.taxa_S - g.taxa_N)).sum() * 100
    var = (w ** 2 * (g.taxa_S * (1 - g.taxa_S) / g.avaliadas_S
                     + g.taxa_N * (1 - g.taxa_N) / g.avaliadas_N)).sum()
    ep = np.sqrt(var) * 100
    cobertura = g.avaliadas_N.sum() / total_N
    contagem = g.leitura.value_counts()

    print(
        f"\n[{nome}] estratos usados: {len(g):,} | cobre {cobertura:.1%} das avaliadas N\n"
        f"  diferença padronizada (S - N): {dif:+.1f} pp  (IC 95%: {dif - 1.96 * ep:+.1f} a {dif + 1.96 * ep:+.1f})\n"
        f"  odds ratio Mantel-Haenszel: {or_mh:.2f}  (IC 95%: {or_inf:.2f} a {or_sup:.2f}) | p CMH = {p_cmh:.3g}\n"
        f"  heterogeneidade entre estratos (Breslow-Day): p = {p_het:.3g}\n"
        f"  estratos com S maior / N maior / inconclusivo: "
        f"{contagem.get('S maior', 0)} / {contagem.get('N maior', 0)} / {contagem.get('inconclusivo', 0)}"
    )
    return {
        "estrato": nome, "n_estratos": len(g), "cobertura_N_%": cobertura * 100,
        "dif_padronizada_pp": dif, "dif_inf": dif - 1.96 * ep, "dif_sup": dif + 1.96 * ep,
        "OR_MH": or_mh, "or_inf": or_inf, "or_sup": or_sup,
        "p_CMH": p_cmh, "p_Breslow_Day": p_het,
        "S_maior": int(contagem.get("S maior", 0)), "N_maior": int(contagem.get("N maior", 0)),
        "inconclusivo": int(contagem.get("inconclusivo", 0)),
    }


def decompor_por_grupo(base, inicio_de, inicio_ate, fim_de, fim_ate):
    """Mesma conta da pergunta 5 (`decompor`), com a entidade sendo procurou_empresa = S ou N.
    dentro = mudança da taxa do próprio grupo; mix = mudança do peso de cada grupo na base."""
    periodo = np.where(
        base.ano_mes.between(inicio_de, inicio_ate), "inicio",
        np.where(base.ano_mes.between(fim_de, fim_ate), "fim", ""),
    )
    b = base.assign(periodo=periodo)
    g = (b[b.periodo != ""].groupby(["procurou_empresa", "periodo"])[["avaliadas", "resolvidas"]]
         .sum().unstack("periodo", fill_value=0))
    g.columns = [f"{a}_{p}" for a, p in g.columns]
    w = g[["avaliadas_inicio", "resolvidas_inicio", "avaliadas_fim", "resolvidas_fim"]].astype(int)
    t, r = decompor(w)
    _, r_inv = decompor(inverter(w))  # inverte início e fim: repete a conta com o peso do fim
    return w, t, r, r_inv


def main():
    engine = get_engine()
    df = pd.read_sql(SQL_BASE, engine)

    # ---------- cobertura ----------
    cob = pd.read_sql(SQL_COBERTURA, engine).set_index("procurou_empresa")["avaliadas"]
    print("Avaliadas por procurou_empresa (o que não é S/N fica fora da análise):")
    print((cob / cob.sum() * 100).round(2).to_string())

    # ---------- 1) bruto ----------
    tot = df.groupby("procurou_empresa")[["avaliadas", "resolvidas"]].sum()
    tot["taxa_pct"] = (tot.resolvidas / tot.avaliadas * 100).round(1)
    inf, sup = proportion_confint(tot.resolvidas, tot.avaliadas, alpha=0.05, method="wilson")
    tot["ic_inf_pct"] = (np.asarray(inf) * 100).round(1)
    tot["ic_sup_pct"] = (np.asarray(sup) * 100).round(1)
    print("\nBruto, por procurou_empresa:")
    print(tot)

    rS, nS = int(tot.loc["S", "resolvidas"]), int(tot.loc["S", "avaliadas"])
    rN, nN = int(tot.loc["N", "resolvidas"]), int(tot.loc["N", "avaliadas"])
    d, i, s = newcombe(rS, nS, rN, nN)
    or_bruto = (rS / (nS - rS)) / (rN / (nN - rN))
    ep_log = np.sqrt(1 / rS + 1 / (nS - rS) + 1 / rN + 1 / (nN - rN))
    print(f"Diferença bruta (S - N): {d:+.1f} pp (IC 95% de Newcombe: {i:+.1f} a {s:+.1f})")
    print(f"Odds ratio bruto (S vs N): {or_bruto:.2f} "
          f"(IC 95%: {np.exp(np.log(or_bruto) - 1.96 * ep_log):.2f} a {np.exp(np.log(or_bruto) + 1.96 * ep_log):.2f})")
    print(f"Casos N: {nN / (nS + nN):.1%} das avaliadas")
    tot.assign(dif_bruta_pp=d, dif_inf=i, dif_sup=s, OR_bruto=or_bruto).round(3).to_csv(OUT / "p04_geral.csv")

    # ---------- 2) ajustado ----------
    seg = comparar(agrupar(df, ["segmento_de_mercado"]))
    mes = comparar(agrupar(df, ["ano_mes"]))
    seg_mes = comparar(agrupar(df, ["segmento_de_mercado", "ano_mes"]))
    emp = comparar(agrupar(df, ["nome_fantasia"]))

    linhas = [
        resumo("por segmento", seg, nN),
        resumo("por mês", mes, nN),
        resumo("por segmento x mês", seg_mes, nN),
        resumo("por empresa", emp, nN),
    ]
    pd.DataFrame(linhas).round(4).to_csv(OUT / "p04_ajustado.csv", index=False)

    # o hábito de procurar a empresa mudou no tempo?
    peso = agrupar(df, ["ano_mes"])
    peso["pct_N_das_avaliadas"] = (
        peso.avaliadas_N / (peso.avaliadas_N + peso.avaliadas_S) * 100
    ).round(2)
    print("\n% de avaliadas que NÃO procuraram a empresa (N), por mês:")
    print(peso["pct_N_das_avaliadas"].to_string())

    # ---------- 3) por segmento ----------
    cols = ["avaliadas_S", "avaliadas_N", "taxa_S", "taxa_N", "dif_pp", "dif_inf", "dif_sup", "leitura"]
    seg.sort_values("dif_pp")[cols].round(4).to_csv(OUT / "p04_segmentos.csv")
    mes[cols].round(4).to_csv(OUT / "p04_meses.csv")
    print(f"\nSegmentos comparados: {len(seg)}")
    print(seg["leitura"].value_counts().to_string())

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
        [f"{s} (n_S={format(a, ',d').replace(',', '.')}; n_N={format(b, ',d').replace(',', '.')})"
         for s, a, b in zip(g1["segmento_de_mercado"], g1["avaliadas_S"], g1["avaliadas_N"])],
        fontsize=8,
    )
    ax.set_ylim(-1, len(g1))
    ax.set_xlabel("Diferença na taxa de resolução, procurou (S) − não procurou (N) (pp, IC 95%)")
    plt.tight_layout()
    plt.savefig(OUT / "p04_dif_por_segmento.png", dpi=150)
    plt.close()

    m = agrupar(df, ["ano_mes"])
    m = m[(m.avaliadas_S >= MIN_POR_GRUPO) & (m.avaliadas_N >= MIN_POR_GRUPO)]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(m.index, m.resolvidas_S / m.avaliadas_S * 100, marker="o", label="Procurou a empresa (S)")
    ax.plot(m.index, m.resolvidas_N / m.avaliadas_N * 100, marker="o", label="Não procurou (N)")
    ax.set_ylabel("Taxa de resolução (%)")
    ax.set_title("Taxa de resolução por mês, segundo o consumidor ter procurado a empresa antes")
    ax.legend()
    plt.xticks(rotation=60, ha="right")
    plt.tight_layout()
    plt.savefig(OUT / "p04_taxa_por_mes.png", dpi=150)
    plt.close()

    # ---------- 4) decomposição da queda geral: peso de S/N x taxa de cada grupo ----------
    linhas = []
    for nome, a, b, c, e in JANELAS:
        w, t, r, r_inv = decompor_por_grupo(df, a, b, c, e)
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
    decomp.to_csv(OUT / "p04_decomposicao.csv", index=False)

    # ---------- 5) pendência da D-008 ----------
    ref = pd.read_sql(SQL_D008, engine)
    ref["pct_procurou_s"] = (ref.procurou_s / ref.n * 100).round(2)
    inf, sup = proportion_confint(ref.procurou_s, ref.n, alpha=0.05, method="wilson")
    ref["ic_inf_pct"] = (np.asarray(inf) * 100).round(2)
    ref["ic_sup_pct"] = (np.asarray(sup) * 100).round(2)
    print("\nD-008: % que já tinha procurado a empresa")
    print(ref.to_string(index=False))

    r_ref = ref.set_index("grupo")
    alvo = r_ref.loc["não respondidas + Resolvida"]
    for comp in ["base geral (avaliadas)", "não respondidas + Não Resolvida"]:
        c = r_ref.loc[comp]
        z, p = proportions_ztest([alvo.procurou_s, c.procurou_s], [alvo.n, c.n])
        print(f"  'não respondidas + Resolvida' vs '{comp}': z = {z:.2f}, "
              f"{'p < 0,001' if p < 0.001 else f'p = {p:.3f}'}")
    ref.to_csv(OUT / "p04_d008.csv", index=False)

    print("\nGerados em outputs/pergunta_04/: p04_geral.csv, p04_ajustado.csv, p04_segmentos.csv, "
          "p04_meses.csv, p04_decomposicao.csv, p04_d008.csv, p04_dif_por_segmento.png, p04_taxa_por_mes.png")


if __name__ == "__main__":
    main()