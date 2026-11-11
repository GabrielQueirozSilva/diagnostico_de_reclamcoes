"""Pergunta 3 (diagnóstico): de onde vem a inversão do sinal e se o formato em U se mantém.

Na análise principal (associacao.py) o odds ratio por dia de espera é > 1 no bruto e < 1
ajustado por segmento e mês, e a taxa por faixa tem formato de U invertido (sobe de 0-2 para
3-5 dias e cai em 11-15). Este script investiga os dois pontos.

Etapas:
    1. Efeitos fixos em sequência (bruto -> + segmento -> + mês -> + ambos -> + prazo estendido):
       mostra qual controle inverte o sinal. Com --empresa, também compara dentro da empresa.
    2. Correlação (ponderada por avaliadas) entre tempo médio e taxa de resolução, por segmento
       e por mês: se for positiva, segmentos/meses mais lentos têm taxa maior (confusão).
    3. Curva por faixa dentro dos maiores segmentos: o formato de U se repete ou é composição?
    4. Curva por faixa dentro e fora do prazo estendido (D-006): quase todas as respostas de
       11-15 dias caem nas janelas de prazo estendido, então a faixa 11-15 mistura "demorou" com
       "foi respondida naquele período".

A faixa 16+ (poucos casos, cauda de 2024) fica de fora das etapas 3 e 4.

Uso:
    python -m src.pergunta_03.diagnostico
    python -m src.pergunta_03.diagnostico --empresa        # inclui efeito fixo de empresa (mais lento)
    python -m src.pergunta_03.diagnostico --segmentos 12   # nº de segmentos na etapa 3 (padrão: 8)

Saídas (em outputs/pergunta_03/):
    p03_diag_efeitos_fixos.csv
    p03_diag_tempo_medio_segmento.csv
    p03_diag_tempo_medio_mes.csv
    p03_diag_faixas_segmentos.csv
    p03_diag_curva_segmentos.png
    p03_diag_faixas_prazo_estendido.csv
    p03_diag_curva_prazo_estendido.png
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.db import get_engine
from src.pergunta_03.base import (
    MIN_AVALIADAS_EMP, OUT, REFERENCIA, ROTULOS, carregar, carregar_empresas, modelo,
    razao_de_chances, razoes_por_faixa, segmentos_grandes, tabela_faixas,
)

FAIXAS_DIAG = ROTULOS[:-1]    # sem a 16+
MIN_FAIXA = 200               # mínimo de avaliadas numa faixa para ela entrar no modelo da etapa 3 e 4

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 60)


# ---------- auxiliares ----------
def correlacao_ponderada(x, y, w):
    mx, my = np.average(x, weights=w), np.average(y, weights=w)
    cov = np.average((x - mx) * (y - my), weights=w)
    return cov / np.sqrt(np.average((x - mx) ** 2, weights=w) * np.average((y - my) ** 2, weights=w))


def resumo_tempo_taxa(base, chave):
    """Tempo médio (com teto de 15 dias) e taxa de resolução por segmento ou por mês."""
    g = base.assign(soma_tempo=base["tempo_lin"] * base["avaliadas"]).groupby(chave).agg(
        avaliadas=("avaliadas", "sum"),
        resolvidas=("resolvidas", "sum"),
        soma_tempo=("soma_tempo", "sum"),
    )
    g["tempo_medio"] = g["soma_tempo"] / g["avaliadas"]
    g["taxa"] = g["resolvidas"] / g["avaliadas"]
    return g.drop(columns="soma_tempo")


def faixas_validas(d):
    """Mantém só as faixas de 0-2 a 11-15 com pelo menos MIN_FAIXA avaliadas."""
    d = d[d["faixa"].isin(FAIXAS_DIAG)]
    n = d.groupby("faixa", observed=True)["avaliadas"].sum()
    return d[d["faixa"].isin(n[n >= MIN_FAIXA].index)]


def or_por_faixa(d, controles):
    """OR de cada faixa contra 0-2 dias, controlando por `controles` (fórmula do patsy)."""
    d = faixas_validas(d)
    vazio = pd.DataFrame(columns=["faixa", "OR", "or_inf", "or_sup"])
    if REFERENCIA not in set(d["faixa"]) or d["faixa"].nunique() < 2:
        return vazio
    try:
        r = modelo(d, f"C(faixa, Treatment('{REFERENCIA}')) + {controles}")
    except Exception as e:  # pouca variação em algum controle
        print(f"   [!] modelo não ajustou: {e}")
        return vazio
    return razoes_por_faixa(r)


def leitura(or_, lo, hi):
    if pd.isna(or_):
        return "sem dados"
    return "maior" if lo > 1 else "menor" if hi < 1 else "inconclusivo"


# ---------- 1) efeitos fixos em sequência ----------
def etapa_efeitos_fixos(base, engine, com_empresa):
    especificacoes = [
        ("bruto", "tempo_lin"),
        ("+ segmento", "tempo_lin + C(seg)"),
        ("+ mês", "tempo_lin + C(mes)"),
        ("+ segmento + mês", "tempo_lin + C(seg) + C(mes)"),
        ("+ segmento + mês + prazo estendido", "tempo_lin + C(seg) + C(mes) + ext"),
    ]
    linhas = []
    n = int(base["avaliadas"].sum())
    for nome, formula in especificacoes:
        or_, lo, hi = razao_de_chances(modelo(base, formula), "tempo_lin")
        linhas.append({"base": "segmentos", "especificacao": nome, "n": n,
                       "OR_por_dia": or_, "ic_inf": lo, "ic_sup": hi})

    if com_empresa:
        emp = carregar_empresas(engine)
        emp = emp[emp.groupby("emp")["avaliadas"].transform("sum") >= MIN_AVALIADAS_EMP]
        n_emp = int(emp["avaliadas"].sum())
        for nome, formula in [
            ("bruto", "tempo_lin"),
            ("+ mês", "tempo_lin + C(mes)"),
            ("+ empresa + mês", "tempo_lin + C(emp) + C(mes)"),
        ]:
            or_, lo, hi = razao_de_chances(modelo(emp, formula), "tempo_lin")
            linhas.append({"base": f"empresas (>= {MIN_AVALIADAS_EMP} aval.)", "especificacao": nome,
                           "n": n_emp, "OR_por_dia": or_, "ic_inf": lo, "ic_sup": hi})

    res = pd.DataFrame(linhas).round(4)
    res.to_csv(OUT / "p03_diag_efeitos_fixos.csv", index=False)
    print("\n=== 1) Odds ratio por dia de espera, acrescentando controles ===")
    print(res.to_string(index=False))


# ---------- 2) tempo médio x taxa ----------
def etapa_tempo_medio(base):
    print("\n=== 2) Tempo médio x taxa de resolução (correlação ponderada por avaliadas) ===")
    for chave, arquivo, rotulo in [("seg", "p03_diag_tempo_medio_segmento.csv", "segmentos"),
                                   ("mes", "p03_diag_tempo_medio_mes.csv", "meses")]:
        g = resumo_tempo_taxa(base, chave)
        g.round(4).sort_values("tempo_medio").to_csv(OUT / arquivo)
        c = correlacao_ponderada(g["tempo_medio"], g["taxa"], g["avaliadas"])
        print(f"{rotulo}: {len(g)} | correlação tempo médio x taxa = {c:+.2f}")
        if chave == "seg":
            mostra = g.assign(taxa_pct=(g["taxa"] * 100).round(1), tempo_medio=g["tempo_medio"].round(2))
            print(mostra.sort_values("tempo_medio")[["avaliadas", "tempo_medio", "taxa_pct"]].to_string())


# ---------- 3) curva por faixa nos maiores segmentos ----------
def etapa_segmentos(base, n_segmentos):
    print(f"\n=== 3) Curva por faixa nos {n_segmentos} maiores segmentos "
          f"(OR ajustado por mês, ref. {REFERENCIA} dias) ===")
    top = base.groupby("seg")["avaliadas"].sum().nlargest(n_segmentos).index.tolist()
    linhas = []
    for s in top:
        d = base[(base["seg"] == s) & base["faixa"].isin(FAIXAS_DIAG)]
        t = tabela_faixas(d)
        ors = or_por_faixa(d, "C(mes)").set_index("faixa")
        for faixa, r in t.iterrows():
            if faixa == REFERENCIA:
                or_, lo, hi = 1.0, 1.0, 1.0
            elif faixa in ors.index:
                or_, lo, hi = ors.loc[faixa, ["OR", "or_inf", "or_sup"]]
            else:
                or_, lo, hi = np.nan, np.nan, np.nan
            linhas.append({
                "seg": s, "faixa": faixa, "avaliadas": int(r["avaliadas"]),
                "taxa_pct": r["taxa"] * 100, "ic_inf_pct": r["ic_inf"] * 100, "ic_sup_pct": r["ic_sup"] * 100,
                "OR_ajust_mes": or_, "or_inf": lo, "or_sup": hi,
            })
    tab = pd.DataFrame(linhas)
    tab.round(4).to_csv(OUT / "p03_diag_faixas_segmentos.csv", index=False)

    for valor, titulo in [("taxa_pct", "Taxa bruta (%)"), ("OR_ajust_mes", "OR ajustado por mês")]:
        p = tab.pivot(index="seg", columns="faixa", values=valor).reindex(columns=FAIXAS_DIAG)
        p = p.reindex(top)
        print(f"\n{titulo}:")
        print(p.round(2 if valor == "taxa_pct" else 3).to_string())

    # leitura do formato: 3-5 e 11-15 contra 0-2
    for faixa in ["3-5", "11-15"]:
        x = tab[tab["faixa"] == faixa]
        lei = [leitura(r.OR_ajust_mes, r.or_inf, r.or_sup) for r in x.itertuples()]
        print(f"\n{faixa} vs {REFERENCIA} nos {len(x)} segmentos: " + ", ".join(
            f"{k}: {lei.count(k)}" for k in ["maior", "menor", "inconclusivo", "sem dados"] if lei.count(k)
        ))

    # gráfico: um painel por segmento
    ncols = 4
    nrows = int(np.ceil(len(top) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3.3 * nrows), sharex=True)
    axes = np.atleast_1d(axes).ravel()
    pos = {f: i for i, f in enumerate(FAIXAS_DIAG)}
    for ax, s in zip(axes, top):
        t = tab[tab["seg"] == s]
        x = t["faixa"].map(pos)
        ax.errorbar(x, t["taxa_pct"],
                    yerr=[t["taxa_pct"] - t["ic_inf_pct"], t["ic_sup_pct"] - t["taxa_pct"]],
                    fmt="o-", capsize=3)
        ax.set_title(f"{s[:38]}\n(n={format(int(t['avaliadas'].sum()), ',d').replace(',', '.')})", fontsize=8)
        ax.set_xticks(range(len(FAIXAS_DIAG)))
        ax.set_xticklabels(FAIXAS_DIAG, fontsize=8)
    for ax in axes[len(top):]:
        ax.axis("off")
    fig.supxlabel("Tempo de resposta (dias)")
    fig.supylabel("Taxa de resolução (%), IC 95% Wilson")
    plt.tight_layout(rect=(0.02, 0.02, 1, 1))
    plt.savefig(OUT / "p03_diag_curva_segmentos.png", dpi=150)
    plt.close()


# ---------- 4) dentro x fora do prazo estendido ----------
def etapa_prazo_estendido(base):
    print("\n=== 4) Curva por faixa dentro e fora do prazo estendido (D-006) ===")
    d11 = base[base["faixa"] == "11-15"]
    if d11["avaliadas"].sum():
        pct = d11.loc[d11["estendido"], "avaliadas"].sum() / d11["avaliadas"].sum()
        print(f"{pct:.1%} das avaliadas com resposta em 11-15 dias caem em dias de prazo estendido")

    linhas = []
    for ext, rotulo in [(False, "fora do prazo estendido"), (True, "dentro do prazo estendido")]:
        d = base[(base["estendido"] == ext) & base["faixa"].isin(FAIXAS_DIAG)]
        t = tabela_faixas(d)
        ors = or_por_faixa(d, "C(seg) + C(mes)").set_index("faixa")
        for faixa, r in t.iterrows():
            if faixa == REFERENCIA:
                or_, lo, hi = 1.0, 1.0, 1.0
            elif faixa in ors.index:
                or_, lo, hi = ors.loc[faixa, ["OR", "or_inf", "or_sup"]]
            else:
                or_, lo, hi = np.nan, np.nan, np.nan
            linhas.append({
                "grupo": rotulo, "faixa": faixa, "avaliadas": int(r["avaliadas"]),
                "taxa_pct": r["taxa"] * 100, "ic_inf_pct": r["ic_inf"] * 100, "ic_sup_pct": r["ic_sup"] * 100,
                "OR_ajust_seg_mes": or_, "or_inf": lo, "or_sup": hi,
            })
    tab = pd.DataFrame(linhas)
    tab.round(4).to_csv(OUT / "p03_diag_faixas_prazo_estendido.csv", index=False)
    print(tab.round(3).to_string(index=False))
    print(f"\n(OR só para faixas com pelo menos {MIN_FAIXA} avaliadas no grupo; senão aparece NaN)")

    fig, ax = plt.subplots(figsize=(8, 5))
    pos = {f: i for i, f in enumerate(FAIXAS_DIAG)}
    for rotulo, t in tab.groupby("grupo"):
        ax.errorbar(t["faixa"].map(pos), t["taxa_pct"],
                    yerr=[t["taxa_pct"] - t["ic_inf_pct"], t["ic_sup_pct"] - t["taxa_pct"]],
                    fmt="o-", capsize=4, label=rotulo)
    ax.set_xticks(range(len(FAIXAS_DIAG)))
    ax.set_xticklabels(FAIXAS_DIAG)
    ax.set_xlabel("Tempo de resposta da empresa (dias)")
    ax.set_ylabel("Taxa de resolução (%) com IC 95% (Wilson)")
    ax.set_title("Taxa de resolução por faixa, dentro e fora do prazo estendido")
    ax.legend()
    plt.tight_layout()
    plt.savefig(OUT / "p03_diag_curva_prazo_estendido.png", dpi=150)
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--empresa", action="store_true", help="inclui o efeito fixo de empresa na etapa 1 (mais lento)")
    ap.add_argument("--segmentos", type=int, default=8, help="nº de maiores segmentos na etapa 3")
    args = ap.parse_args()

    engine = get_engine()
    df = carregar(engine)
    base = segmentos_grandes(df)
    print(f"Base: {int(base['avaliadas'].sum()):,} avaliadas e respondidas em {base['seg'].nunique()} segmentos "
          f"(>= 500 avaliadas)".replace(",", "."))

    etapa_efeitos_fixos(base, engine, args.empresa)
    etapa_tempo_medio(base)
    etapa_segmentos(base, args.segmentos)
    etapa_prazo_estendido(base)
    print(f"\nSaídas gravadas em {OUT}")


if __name__ == "__main__":
    main()