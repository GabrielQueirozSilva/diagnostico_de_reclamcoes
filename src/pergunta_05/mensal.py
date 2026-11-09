"""Pergunta 5 (parte 3): como a taxa de resolução evolui mês a mês?

Responde duas dúvidas que os recortes início/fim não respondem:
    1. A queda foi gradual ou em degrau (e em que mês)?
    2. A proporção de reclamações avaliadas mudou? Se mudou, parte da queda pode ser
       mudança em QUEM avalia, e não em como o atendimento resolve.

Gera, para a base toda e para os segmentos que mais pesam na queda:
    taxa de resolução = resolvidas / avaliadas, com banda de 95% de Wilson
    volume de avaliadas e % de avaliadas sobre as finalizadas

Com --empresas, também mostra a série mensal das empresas que mais puxaram a queda dentro de
cada segmento (mesmo ranking do empresas.py), para ver se a queda é de várias empresas
ao mesmo tempo (algo comum ao segmento) ou de uma só.

As janelas início/fim usadas na comparação aparecem sombreadas.

Uso:
    python -m src.pergunta_05.mensal                      # base toda + 3 segmentos que mais pesam
    python -m src.pergunta_05.mensal --top 5
    python -m src.pergunta_05.mensal -s "Nome exato do segmento"
    python -m src.pergunta_05.mensal --empresas           # + as 6 empresas que mais puxaram a queda em cada segmento
    python -m src.pergunta_05.mensal --empresas --n-empresas 8

Saídas (em outputs/pergunta_05/):
    mensal_geral.png, mensal_segmentos.png, mensal_geral.csv, mensal_segmentos.csv
    com --empresas: mensal_empresas_<segmento>.png e mensal_empresas.csv
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sqlalchemy import text
from statsmodels.stats.proportion import proportion_confint

from src.db import get_engine
from src.pergunta_05.empresas import analisar_segmento, segmentos_padrao, slug
from src.pergunta_05.evolucao import FIM_A_PARTIR, INICIO_ATE

OUT = Path(__file__).resolve().parents[2] / "outputs" / "pergunta_05"
OUT.mkdir(parents=True, exist_ok=True)

COR = "#2E75B6"
MIN_AVAL_MES = 30  # nos gráficos por empresa, meses com menos avaliadas que isso não são desenhados (ruído)

SQL_GERAL = text("""
    SELECT ano_mes,
           COUNT(*) AS finalizadas,
           COUNT(*) FILTER (WHERE avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')) AS avaliadas,
           COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida') AS resolvidas
    FROM ocorrencias_analise
    GROUP BY ano_mes
    ORDER BY ano_mes
""")

SQL_SEGMENTOS = text("""
    SELECT segmento_de_mercado, ano_mes,
           COUNT(*) AS finalizadas,
           COUNT(*) FILTER (WHERE avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')) AS avaliadas,
           COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida') AS resolvidas
    FROM ocorrencias_analise
    WHERE segmento_de_mercado = ANY(:segmentos)
    GROUP BY segmento_de_mercado, ano_mes
    ORDER BY segmento_de_mercado, ano_mes
""")

SQL_EMPRESAS = text("""
    SELECT nome_fantasia, ano_mes,
           COUNT(*) AS finalizadas,
           COUNT(*) FILTER (WHERE avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')) AS avaliadas,
           COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida') AS resolvidas
    FROM ocorrencias_analise
    WHERE segmento_de_mercado = :segmento
      AND nome_fantasia = ANY(:empresas)
    GROUP BY nome_fantasia, ano_mes
    ORDER BY nome_fantasia, ano_mes
""")


def calcular(df):
    """Taxa, Wilson, % de avaliadas e variação mês a mês (em pp) para uma série mensal."""
    d = df.sort_values("ano_mes").reset_index(drop=True).copy()
    ok = d["avaliadas"] > 0  # mês sem nenhuma avaliada não tem taxa
    d["taxa"] = d["resolvidas"] / d["avaliadas"].where(ok)
    d["ic_inf"] = np.nan
    d["ic_sup"] = np.nan
    if ok.any():
        d.loc[ok, "ic_inf"], d.loc[ok, "ic_sup"] = proportion_confint(
            d.loc[ok, "resolvidas"], d.loc[ok, "avaliadas"], alpha=0.05, method="wilson"
        )
    d["pct_avaliadas"] = d["avaliadas"] / d["finalizadas"]
    d["var_pp"] = d["taxa"].diff() * 100
    return d


def _eixo_x(ax, meses, rotulos=True):
    ax.set_xticks(range(len(meses)))
    if rotulos:
        ax.set_xticklabels(meses, rotation=60, ha="right", fontsize=8)
    else:
        ax.set_xticklabels([])
    ax.set_xlim(-0.5, len(meses) - 0.5)


def _sombrear(ax, meses):
    """Marca as janelas usadas na comparação início/fim."""
    for sel in ([i for i, m in enumerate(meses) if m <= INICIO_ATE],
                [i for i, m in enumerate(meses) if m >= FIM_A_PARTIR]):
        if sel:
            ax.axvspan(min(sel) - 0.5, max(sel) + 0.5, color="gray", alpha=0.12, lw=0)


def _linha_taxa(ax, d):
    x = range(len(d))
    ax.fill_between(x, d["ic_inf"] * 100, d["ic_sup"] * 100, color=COR, alpha=0.2, lw=0)
    ax.plot(x, d["taxa"] * 100, color=COR, marker="o", ms=3)
    ax.set_ylabel("% resolvida")
    ax.grid(axis="y", alpha=0.3)


def grafico_geral(d, caminho):
    meses = d["ano_mes"].tolist()
    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True, gridspec_kw={"height_ratios": [3, 1.5, 1.5]})

    _linha_taxa(axes[0], d)
    axes[0].set_title("Taxa de resolução por mês (banda: IC 95% de Wilson; sombreado: janelas início/fim)")

    axes[1].bar(range(len(d)), d["avaliadas"], color=COR)
    axes[1].set_ylabel("Avaliadas")
    axes[1].grid(axis="y", alpha=0.3)

    axes[2].plot(range(len(d)), d["pct_avaliadas"] * 100, color=COR, marker="o", ms=3)
    axes[2].set_ylabel("% avaliadas\n/ finalizadas")
    axes[2].grid(axis="y", alpha=0.3)

    for ax in axes:
        _sombrear(ax, meses)
    _eixo_x(axes[2], meses)
    plt.tight_layout()
    plt.savefig(caminho, dpi=150)
    plt.close()


def grafico_segmentos(dseg, caminho):
    segs = list(dseg["segmento_de_mercado"].unique())
    meses = sorted(dseg["ano_mes"].unique())
    fig, axes = plt.subplots(len(segs), 1, figsize=(11, 3.2 * len(segs)), sharex=True, squeeze=False)
    for ax, seg in zip(axes[:, 0], segs):
        d = dseg[dseg["segmento_de_mercado"] == seg].set_index("ano_mes").reindex(meses).reset_index()
        _linha_taxa(ax, d)
        _sombrear(ax, meses)
        ax.set_title(seg if len(seg) <= 70 else seg[:67] + "...", fontsize=10, loc="left")
    _eixo_x(axes[-1, 0], meses)
    plt.tight_layout()
    plt.savefig(caminho, dpi=150)
    plt.close()


def grafico_empresas(demp, empresas, meses, segmento, caminho, ncols=2):
    """Um painel por empresa (mesma escala vertical, para comparar), na ordem do ranking de contribuição."""
    n = len(empresas)
    nrows = -(-n // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(6.5 * ncols, 2.7 * nrows + 0.8), sharey=True, squeeze=False)
    planos = axes.ravel()
    for ax, emp in zip(planos, empresas):
        d = demp[demp["nome_fantasia"] == emp].set_index("ano_mes").reindex(meses).reset_index()
        _linha_taxa(ax, d)
        _sombrear(ax, meses)
        ax.set_title(emp if len(emp) <= 45 else emp[:42] + "...", fontsize=10, loc="left")
    for ax in planos[n:]:
        ax.set_visible(False)
    # rótulos de mês só no último painel visível de cada coluna
    for c in range(ncols):
        visiveis = [planos[i] for i in range(c, len(planos), ncols) if i < n]
        for ax in visiveis:
            _eixo_x(ax, meses, rotulos=(ax is visiveis[-1]))
    seg_titulo = segmento if len(segmento) <= 80 else segmento[:77] + "..."
    fig.suptitle(
        f"{seg_titulo}: empresas que mais puxaram a queda "
        f"(meses com menos de {MIN_AVAL_MES} avaliadas omitidos)",
        x=0.01, ha="left", fontsize=11,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(caminho, dpi=150)
    plt.close()


def resumo_geral(d):
    pd.set_option("display.width", 200)
    t = d[["ano_mes", "finalizadas", "avaliadas", "taxa", "ic_inf", "ic_sup", "pct_avaliadas", "var_pp"]].copy()
    for c in ["taxa", "ic_inf", "ic_sup", "pct_avaliadas"]:
        t[c] = (t[c] * 100).round(1)
    t["var_pp"] = t["var_pp"].round(1)
    print(t.to_string(index=False))

    print("\nMaiores variações de um mês para o outro (em pp):")
    print(t.reindex(t["var_pp"].abs().sort_values(ascending=False).index).head(5)[["ano_mes", "taxa", "var_pp"]].to_string(index=False))

    ini = d[d["ano_mes"] <= INICIO_ATE]
    fim = d[d["ano_mes"] >= FIM_A_PARTIR]
    print(
        f"\n% de avaliadas sobre finalizadas: início {ini.avaliadas.sum() / ini.finalizadas.sum():.1%} "
        f"| fim {fim.avaliadas.sum() / fim.finalizadas.sum():.1%}"
    )


def empresas_do_segmento(engine, seg, n, meses):
    """Série mensal das n empresas que mais puxaram a queda do segmento. Retorna (DataFrame, lista ordenada)."""
    res = analisar_segmento(engine, seg, MIN_AVAL_MES)
    if res is None:
        return None, []
    w, _ = res
    empresas = w.sort_values("contrib_total_pp").head(n).index.tolist()
    bruto = pd.read_sql(SQL_EMPRESAS, engine, params={"segmento": seg, "empresas": empresas})
    if bruto.empty:
        print(f"[!] Sem dados mensais para as empresas de '{seg}'.")
        return None, []
    demp = pd.concat(
        [calcular(g).assign(nome_fantasia=e, segmento_de_mercado=seg) for e, g in bruto.groupby("nome_fantasia")],
        ignore_index=True,
    )
    # meses com pouca avaliação ficam sem taxa (ruído), mas os volumes continuam no CSV
    demp.loc[demp["avaliadas"] < MIN_AVAL_MES, ["taxa", "ic_inf", "ic_sup"]] = np.nan
    return demp, empresas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--segmento", action="append", help="nome exato do segmento (repetível)")
    ap.add_argument("--top", type=int, default=3, help="quantos segmentos pegar do CSV (padrão 3)")
    ap.add_argument("--empresas", action="store_true", help="também gera a série mensal das empresas que mais puxaram a queda em cada segmento")
    ap.add_argument("--n-empresas", type=int, default=6, help="quantas empresas por segmento com --empresas (padrão 6)")
    args = ap.parse_args()

    engine = get_engine()
    segmentos = args.segmento or segmentos_padrao(args.top)

    geral = calcular(pd.read_sql(SQL_GERAL, engine))
    resumo_geral(geral)
    geral.round(4).to_csv(OUT / "mensal_geral.csv", index=False)
    grafico_geral(geral, OUT / "mensal_geral.png")

    bruto = pd.read_sql(SQL_SEGMENTOS, engine, params={"segmentos": segmentos})
    if bruto.empty:
        raise SystemExit("Nenhuma linha para os segmentos pedidos. Confira os nomes exatos.")
    dseg = pd.concat(
        [calcular(g).assign(segmento_de_mercado=s) for s, g in bruto.groupby("segmento_de_mercado")],
        ignore_index=True,
    )
    dseg.round(4).to_csv(OUT / "mensal_segmentos.csv", index=False)
    grafico_segmentos(dseg, OUT / "mensal_segmentos.png")
    gerados = "mensal_geral.png, mensal_segmentos.png e os CSVs"

    if args.empresas:
        meses = geral["ano_mes"].tolist()
        quadros = []
        for seg in segmentos:
            demp, empresas = empresas_do_segmento(engine, seg, args.n_empresas, meses)
            if demp is None:
                continue
            grafico_empresas(demp, empresas, meses, seg, OUT / f"mensal_empresas_{slug(seg)}.png")
            quadros.append(demp)
        if quadros:
            pd.concat(quadros, ignore_index=True).round(4).to_csv(OUT / "mensal_empresas.csv", index=False)
            gerados += ", mensal_empresas_<segmento>.png e mensal_empresas.csv"

    print(f"\nGerados em {OUT}: {gerados}.")


if __name__ == "__main__":
    main()