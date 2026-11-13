"""Pergunta 5 (parte 4): nas empresas que mais caíram, a queda se explica por "empresa respondeu", por tempo
de resposta ou por assunto?

Fecha o pendente da pergunta 5 (ligação com as perguntas 2 e 3). Para cada empresa (padrão: Gol Linhas Aéreas,
Nubank e Banco Santander), nos recortes padrão de evolucao.py:

    1. Empresa respondeu (P2): a queda vem de ter mais casos sem resposta (peso dos casos N) ou de a taxa ter
       caído entre as respondidas? Decomposição dentro/mix com as entidades S e N.
    2. Tempo de resposta (P3): o tempo médio de resposta mudou do início para o fim?
    3. Assunto: a queda vem de a taxa ter caído nos mesmos assuntos (dentro) ou de ter mudado o tipo de
       reclamação (mix, entrada e saída)? Mesma decomposição, com o assunto como entidade.

Uso:
    python -m src.pergunta_05.empresas_causas
    python -m src.pergunta_05.empresas_causas -e "Nubank" -e "Banco Santander"
    python -m src.pergunta_05.empresas_causas --nivel grupo_problema     # area, assunto, grupo_problema ou problema

Saídas (outputs/pergunta_05/):
    causas_<empresa>_mensal.csv       série mensal: avaliadas, taxa, % de casos N, tempo médio
    causas_<empresa>_<nivel>.csv      decomposição por assunto (ou outro nível)
    causas_resumo.csv                 uma linha por empresa
    causas_empresas.png               taxa, % de casos N e tempo médio, mês a mês
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sqlalchemy import text
from statsmodels.stats.proportion import proportion_confint

from src.db import get_engine
from src.pergunta_05.decomposicao import decompor
from src.pergunta_05.empresas import slug
from src.pergunta_05.evolucao import FIM_A_PARTIR, FIM_ATE, INICIO_ATE, INICIO_DE

OUT = Path(__file__).resolve().parents[2] / "outputs" / "pergunta_05"
OUT.mkdir(parents=True, exist_ok=True)

EMPRESAS_PADRAO = ["Gol Linhas Aéreas", "Nubank", "Banco Santander"]
NIVEIS = ("area", "assunto", "grupo_problema", "problema")  # colunas da hierarquia (o nome vai para o SQL: lista fixa)
MIN_AVAL = 30  # mínimo de avaliadas (por mês, e por item nos dois períodos) para desenhar / calcular Wilson e Newcombe
COR = "#2E75B6"

SQL_MENSAL = text("""
    SELECT ano_mes,
           COUNT(*) AS avaliadas,
           COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida') AS resolvidas,
           COUNT(*) FILTER (WHERE respondida = 'N') AS avaliadas_n,
           COUNT(*) FILTER (WHERE respondida = 'N' AND avaliacao_reclamacao = 'Resolvida') AS resolvidas_n,
           AVG(tempo_resposta_valido) AS tempo_medio
    FROM ocorrencias_analise
    WHERE nome_fantasia = :empresa
      AND avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')
    GROUP BY ano_mes
    ORDER BY ano_mes
""")


def sql_nivel(nivel):
    """Contagens por item do nível escolhido (assunto etc.) e período. `nivel` vem da lista NIVEIS."""
    assert nivel in NIVEIS
    return text(f"""
        WITH base AS (
          SELECT COALESCE({nivel}, '(sem informação)') AS item,
                 CASE WHEN ano_mes BETWEEN :inicio_de AND :inicio_ate THEN 'inicio'
                      WHEN ano_mes BETWEEN :fim_de AND :fim_ate THEN 'fim' END AS periodo,
                 avaliacao_reclamacao
          FROM ocorrencias_analise
          WHERE nome_fantasia = :empresa
            AND avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')
        )
        SELECT item,
               COUNT(*) FILTER (WHERE periodo = 'inicio') AS avaliadas_inicio,
               COUNT(*) FILTER (WHERE periodo = 'inicio' AND avaliacao_reclamacao = 'Resolvida') AS resolvidas_inicio,
               COUNT(*) FILTER (WHERE periodo = 'fim') AS avaliadas_fim,
               COUNT(*) FILTER (WHERE periodo = 'fim' AND avaliacao_reclamacao = 'Resolvida') AS resolvidas_fim
        FROM base
        WHERE periodo IS NOT NULL
        GROUP BY item
    """)


def mensal(engine, empresa):
    d = pd.read_sql(SQL_MENSAL, engine, params={"empresa": empresa})
    if d.empty:
        return None
    d["tempo_medio"] = pd.to_numeric(d["tempo_medio"], errors="coerce")
    d["avaliadas_s"] = d["avaliadas"] - d["avaliadas_n"]
    d["resolvidas_s"] = d["resolvidas"] - d["resolvidas_n"]
    d["taxa"] = d["resolvidas"] / d["avaliadas"]
    d["ic_inf"], d["ic_sup"] = proportion_confint(d["resolvidas"], d["avaliadas"], alpha=0.05, method="wilson")
    d["pct_n"] = d["avaliadas_n"] / d["avaliadas"]
    return d


def resumo_periodo(j):
    """Taxa, % de casos N, taxa de S e de N e tempo médio (ponderado) de um conjunto de meses."""
    av, res = j["avaliadas"].sum(), j["resolvidas"].sum()
    avn, resn = j["avaliadas_n"].sum(), j["resolvidas_n"].sum()
    avs, ress = av - avn, res - resn
    ok = j["tempo_medio"].notna() & (j["avaliadas_s"] > 0)
    tempo = np.average(j.loc[ok, "tempo_medio"], weights=j.loc[ok, "avaliadas_s"]) if ok.any() else np.nan
    return {
        "avaliadas": int(av), "resolvidas": int(res), "taxa": res / av,
        "pct_n": avn / av, "taxa_s": ress / avs if avs else np.nan,
        "taxa_n": resn / avn if avn else np.nan, "tempo_medio": tempo,
        "avaliadas_s": int(avs), "resolvidas_s": int(ress), "avaliadas_n": int(avn), "resolvidas_n": int(resn),
    }


def tabela_sn(ini, fim):
    """Entidades S (respondida) e N (não respondida) no formato de decompor()."""
    return pd.DataFrame(
        {
            "avaliadas_inicio": [ini["avaliadas_s"], ini["avaliadas_n"]],
            "resolvidas_inicio": [ini["resolvidas_s"], ini["resolvidas_n"]],
            "avaliadas_fim": [fim["avaliadas_s"], fim["avaliadas_n"]],
            "resolvidas_fim": [fim["resolvidas_s"], fim["resolvidas_n"]],
        },
        index=["S (respondida)", "N (não respondida)"],
    )


def por_nivel(engine, empresa, nivel):
    df = pd.read_sql(
        sql_nivel(nivel), engine,
        params={"empresa": empresa, "inicio_de": INICIO_DE, "inicio_ate": INICIO_ATE,
                "fim_de": FIM_A_PARTIR, "fim_ate": FIM_ATE},
    )
    if df.empty:
        return None
    w = df.set_index("item").astype(int)
    if w["avaliadas_inicio"].sum() == 0 or w["avaliadas_fim"].sum() == 0:
        return None
    return decompor(w, min_aval=MIN_AVAL)


def pct_da_queda(parte, variacao):
    return f"{parte / variacao:.0%}" if variacao else "n/d"


def analisar(engine, empresa, nivel):
    d = mensal(engine, empresa)
    if d is None:
        print(f"[!] Nenhuma avaliada para '{empresa}'. Confira o nome exato (acentos, espaços).")
        return None
    ini = d[(d["ano_mes"] >= INICIO_DE) & (d["ano_mes"] <= INICIO_ATE)]
    fim = d[(d["ano_mes"] >= FIM_A_PARTIR) & (d["ano_mes"] <= FIM_ATE)]
    if ini.empty or fim.empty:
        print(f"[!] '{empresa}' não tem avaliadas nos dois períodos; nada a comparar.")
        return None
    ri, rf = resumo_periodo(ini), resumo_periodo(fim)
    var = (rf["taxa"] - ri["taxa"]) * 100

    # 1) empresa respondeu
    _, r_sn = decompor(tabela_sn(ri, rf), min_aval=MIN_AVAL)
    # 3) assunto (ou outro nível)
    res_nivel = por_nivel(engine, empresa, nivel)

    print("\n" + "=" * 90)
    print(empresa)
    print(f"Taxa: {ri['taxa']:.1%} -> {rf['taxa']:.1%} (variação {var:+.1f} pp) | avaliadas: {ri['avaliadas']} -> {rf['avaliadas']}")

    print("\n1) Empresa respondeu")
    print(
        f"   % de casos N: {ri['pct_n']:.1%} -> {rf['pct_n']:.1%} | taxa S: {ri['taxa_s']:.1%} -> {rf['taxa_s']:.1%}"
        f" | taxa N: {ri['taxa_n']:.1%} -> {rf['taxa_n']:.1%}"
    )
    print(
        f"   dentro (taxas de S e N): {r_sn['dentro_pp']:+.1f} pp ({pct_da_queda(r_sn['dentro_pp'], var)} da variação)"
        f" | mix (peso de N): {r_sn['mix_pp']:+.1f} pp ({pct_da_queda(r_sn['mix_pp'], var)})"
    )

    print("\n2) Tempo de resposta (casos respondidos)")
    print(f"   tempo médio: {ri['tempo_medio']:.2f} -> {rf['tempo_medio']:.2f} dias")

    linha_nivel = {}
    if res_nivel is None:
        print(f"\n3) Por {nivel}: sem dados nos dois períodos.")
    else:
        t, r = res_nivel
        print(f"\n3) Por {nivel} ({r['n_estaveis']} nos dois períodos, {r['n_entraram']} só no fim, {r['n_sairam']} só no início)")
        print(
            f"   dentro (taxa de cada {nivel}): {r['dentro_pp']:+.1f} pp ({pct_da_queda(r['dentro_pp'], var)})"
            f" | mix (peso): {r['mix_pp']:+.1f} pp ({pct_da_queda(r['mix_pp'], var)})"
            f" | entrada: {r['entrada_pp']:+.1f} pp | saída: {r['saida_pp']:+.1f} pp"
        )
        cols = ["status", "avaliadas_inicio", "avaliadas_fim", "taxa_inicio", "taxa_fim",
                "contrib_dentro_pp", "contrib_mix_pp", "contrib_entrada_pp", "contrib_saida_pp",
                "contrib_total_pp", "leitura"]
        t = t.sort_values("contrib_total_pp")[cols]
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 220)
        print(f"\n   Itens que mais puxaram a queda ({nivel}):")
        print(t.head(8).round(3).to_string())
        t.round(4).to_csv(OUT / f"causas_{slug(empresa)}_{nivel}.csv")
        linha_nivel = {f"{nivel}_{k}": r[k] for k in ("dentro_pp", "mix_pp", "entrada_pp", "saida_pp")}

    d.round(4).to_csv(OUT / f"causas_{slug(empresa)}_mensal.csv", index=False)
    resumo = {
        "empresa": empresa, "variacao_pp": var,
        "taxa_inicio": ri["taxa"], "taxa_fim": rf["taxa"],
        "pct_n_inicio": ri["pct_n"], "pct_n_fim": rf["pct_n"],
        "taxa_s_inicio": ri["taxa_s"], "taxa_s_fim": rf["taxa_s"],
        "taxa_n_inicio": ri["taxa_n"], "taxa_n_fim": rf["taxa_n"],
        "sn_dentro_pp": r_sn["dentro_pp"], "sn_mix_pp": r_sn["mix_pp"],
        "tempo_inicio": ri["tempo_medio"], "tempo_fim": rf["tempo_medio"],
        **linha_nivel,
    }
    return d, resumo


def _sombrear(ax, meses):
    for sel in ([i for i, m in enumerate(meses) if INICIO_DE <= m <= INICIO_ATE],
                [i for i, m in enumerate(meses) if FIM_A_PARTIR <= m <= FIM_ATE]):
        if sel:
            ax.axvspan(min(sel) - 0.5, max(sel) + 0.5, color="gray", alpha=0.12, lw=0)


def grafico(series, caminho):
    """Por empresa (coluna): taxa com banda de Wilson, % de casos N e tempo médio de resposta."""
    meses = sorted({m for d in series.values() for m in d["ano_mes"]})
    n = len(series)
    fig, axes = plt.subplots(3, n, figsize=(5.4 * n, 8.5), sharex=True, squeeze=False)
    x = range(len(meses))
    for j, (emp, d) in enumerate(series.items()):
        d = d.set_index("ano_mes").reindex(meses).reset_index()
        d.loc[d["avaliadas"].fillna(0) < MIN_AVAL, ["taxa", "ic_inf", "ic_sup", "pct_n", "tempo_medio"]] = np.nan
        a0, a1, a2 = axes[0, j], axes[1, j], axes[2, j]
        a0.fill_between(x, d["ic_inf"] * 100, d["ic_sup"] * 100, color=COR, alpha=0.2, lw=0)
        a0.plot(x, d["taxa"] * 100, color=COR, marker="o", ms=3)
        a0.set_title(emp, fontsize=11, loc="left")
        a1.plot(x, d["pct_n"] * 100, color=COR, marker="o", ms=3)
        a2.plot(x, d["tempo_medio"], color=COR, marker="o", ms=3)
        if j == 0:
            a0.set_ylabel("% resolvida")
            a1.set_ylabel("% de casos N\n(não respondidos)")
            a2.set_ylabel("tempo médio\nde resposta (dias)")
        for ax in (a0, a1, a2):
            _sombrear(ax, meses)
            ax.grid(axis="y", alpha=0.3)
        a2.set_xticks(list(x))
        a2.set_xticklabels(meses, rotation=60, ha="right", fontsize=7)
        a2.set_xlim(-0.5, len(meses) - 0.5)
    fig.suptitle(f"Meses com menos de {MIN_AVAL} avaliadas omitidos; sombreado: janelas início/fim",
                 x=0.01, ha="left", fontsize=10)
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    plt.savefig(caminho, dpi=150)
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-e", "--empresa", action="append", help="nome exato da empresa (repetível)")
    ap.add_argument("--nivel", choices=NIVEIS, default="assunto", help="nível da hierarquia para a decomposição (padrão: assunto)")
    args = ap.parse_args()

    engine = get_engine()
    empresas = args.empresa or EMPRESAS_PADRAO

    series, linhas = {}, []
    for emp in empresas:
        res = analisar(engine, emp, args.nivel)
        if res is None:
            continue
        series[emp] = res[0]
        linhas.append(res[1])

    if not linhas:
        raise SystemExit("Nenhuma empresa analisada.")
    pd.DataFrame(linhas).round(4).to_csv(OUT / "causas_resumo.csv", index=False)
    grafico(series, OUT / "causas_empresas.png")
    print(f"\nGerados em {OUT}: causas_resumo.csv, causas_empresas.png e os CSVs por empresa.")


if __name__ == "__main__":
    main()