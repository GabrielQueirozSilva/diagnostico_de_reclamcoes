"""Pergunta 3 (por segmento): o efeito do tempo de resposta muda de sinal conforme o segmento?

O diagnóstico mostrou que o OR bruto (> 1) inverte para < 1 ao controlar por segmento, e que
a curva por faixa tem formato diferente em cada segmento. Este script quantifica isso.

Etapas:
    1. OR por dia de espera DENTRO de cada segmento, ajustado por mês
       (modelo binomial: tempo_lin + C(mes)), com IC de 95% e leitura
       (queda clara / alta clara / inconclusivo)
    2. Heterogeneidade entre segmentos:
         - teste de razão de verossimilhança da interação segmento x tempo
           (modelo com e sem tempo_lin:C(seg), ambos com efeito fixo de segmento e de mês)
         - Q de Cochran, I² e tau² sobre os OR por segmento, com o OR de efeitos aleatórios e o
           intervalo de predição ("o OR por dia de um segmento novo cairia aqui")
    3. Gráfico de floresta (um ponto por segmento)

O termo é linear em tempo_lin (dias, com teto de 15). Como a curva por faixa nem sempre é
monótona (ver diagnostico.py), o OR por dia resume a tendência média do segmento.

Uso:
    python -m src.pergunta_03.por_segmento
    python -m src.pergunta_03.por_segmento --sem-prazo-estendido    # sensibilidade (D-006)

Saídas (em outputs/pergunta_03/; com a flag, o nome ganha o sufixo _sem_estendido):
    p03_seg_or_por_dia.csv
    p03_seg_heterogeneidade.csv
    p03_seg_floresta.png
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2

from src.db import get_engine
from src.pergunta_03.base import OUT, carregar, modelo, segmentos_grandes

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 70)


def texto_p(p):
    """p-valor legível: com este volume de dados ele costuma ser praticamente zero."""
    return "p < 0,001" if p < 0.001 else f"p = {p:.3f}".replace(".", ",")


def or_por_segmento(base):
    """Ajusta tempo_lin + C(mes) dentro de cada segmento. Devolve uma linha por segmento."""
    linhas = []
    for s, d in base.groupby("seg"):
        try:
            r = modelo(d, "tempo_lin + C(mes)")
            b, se = float(r.params["tempo_lin"]), float(r.bse["tempo_lin"])
        except Exception as e:  # pouca variação no tempo ou nos meses
            print(f"[!] {s}: modelo não ajustou ({e})")
            continue
        if not np.isfinite(b) or not np.isfinite(se) or se <= 0:
            print(f"[!] {s}: estimativa inválida, segmento ignorado")
            continue
        n = int(d["avaliadas"].sum())
        linhas.append({
            "seg": s,
            "avaliadas": n,
            "taxa_pct": d["resolvidas"].sum() / n * 100,
            "tempo_medio": (d["tempo_lin"] * d["avaliadas"]).sum() / n,
            "beta": b,
            "se": se,
            "OR_por_dia": np.exp(b),
            "or_inf": np.exp(b - 1.96 * se),
            "or_sup": np.exp(b + 1.96 * se),
        })
    res = pd.DataFrame(linhas)
    res["leitura"] = np.select(
        [res["or_sup"] < 1, res["or_inf"] > 1], ["queda clara", "alta clara"], "inconclusivo"
    )
    return res.sort_values("OR_por_dia").reset_index(drop=True)


def teste_interacao(base):
    """Razão de verossimilhança: o efeito do tempo difere entre segmentos (tempo_lin:C(seg))?"""
    r0 = modelo(base, "tempo_lin + C(seg) + C(mes)")
    r1 = modelo(base, "tempo_lin * C(seg) + C(mes)")
    estat = r0.deviance - r1.deviance
    gl = int(round(r0.df_resid - r1.df_resid))
    return estat, gl, chi2.sf(estat, gl)


def heterogeneidade(res):
    """Q de Cochran, I², tau² (DerSimonian-Laird) e efeito aleatório com intervalo de predição."""
    b, se = res["beta"].to_numpy(), res["se"].to_numpy()
    k = len(b)
    w = 1 / se ** 2
    mu_f = np.sum(w * b) / np.sum(w)
    q = float(np.sum(w * (b - mu_f) ** 2))
    gl = k - 1
    i2 = max(0.0, (q - gl) / q) if q > 0 else 0.0
    c = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    tau2 = max(0.0, (q - gl) / c)
    wr = 1 / (se ** 2 + tau2)
    mu_r = np.sum(wr * b) / np.sum(wr)
    se_r = np.sqrt(1 / np.sum(wr))
    margem = 1.96 * np.sqrt(tau2 + se_r ** 2)
    return {
        "segmentos": k,
        "OR_efeito_fixo": np.exp(mu_f),
        "Q": q, "gl": gl, "p_Q": chi2.sf(q, gl),
        "I2_%": i2 * 100,
        "tau": np.sqrt(tau2),
        "OR_efeitos_aleatorios": np.exp(mu_r),
        "OR_re_ic_inf": np.exp(mu_r - 1.96 * se_r),
        "OR_re_ic_sup": np.exp(mu_r + 1.96 * se_r),
        "predicao_inf": np.exp(mu_r - margem),
        "predicao_sup": np.exp(mu_r + margem),
    }


def floresta(res, caminho, or_re):
    fig, ax = plt.subplots(figsize=(10, 0.3 * len(res) + 1.8))
    ax.errorbar(
        res["OR_por_dia"], res.index,
        xerr=[res["OR_por_dia"] - res["or_inf"], res["or_sup"] - res["OR_por_dia"]],
        fmt="o", capsize=3,
    )
    ax.axvline(1, linestyle="--", color="gray", label="sem associação (OR = 1)")
    ax.axvline(or_re, linestyle=":", color="C1", label=f"efeitos aleatórios: {or_re:.3f}")
    ax.set_yticks(res.index)
    ax.set_yticklabels(
        [f"{s[:55]} (n={format(n, ',d').replace(',', '.')})" for s, n in zip(res["seg"], res["avaliadas"])],
        fontsize=8,
    )
    ax.set_ylim(-1, len(res))
    ax.set_xlabel("Odds ratio de resolução por dia de espera, ajustado por mês (IC 95%)")
    ax.legend(loc="lower right", fontsize=8)
    plt.tight_layout()
    plt.savefig(caminho, dpi=150)
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-prazo-estendido", action="store_true",
                    help="repete tudo sem os dias de prazo estendido (D-006)")
    args = ap.parse_args()
    sufixo = "_sem_estendido" if args.sem_prazo_estendido else ""

    engine = get_engine()
    df = carregar(engine)
    if args.sem_prazo_estendido:
        df = df[~df["estendido"]]
    base = segmentos_grandes(df)
    print(f"Base: {int(base['avaliadas'].sum()):,} avaliadas e respondidas em {base['seg'].nunique()} segmentos "
          f"(>= 500 avaliadas){' | sem prazo estendido' if args.sem_prazo_estendido else ''}".replace(",", "."))

    # ---------- 1) OR por segmento ----------
    res = or_por_segmento(base)
    saida = res.drop(columns=["beta", "se"]).round(4)
    saida.to_csv(OUT / f"p03_seg_or_por_dia{sufixo}.csv", index=False)
    mostra = saida.assign(avaliadas=saida["avaliadas"].map("{:,}".format).str.replace(",", "."))
    print("\n=== 1) OR por dia de espera dentro de cada segmento (ajustado por mês) ===")
    print(mostra[["seg", "avaliadas", "taxa_pct", "tempo_medio", "OR_por_dia", "or_inf", "or_sup", "leitura"]]
          .round(3).to_string(index=False))
    print("\n" + ", ".join(f"{k}: {v}" for k, v in res["leitura"].value_counts().items()))
    peso = res.groupby("leitura")["avaliadas"].sum() / res["avaliadas"].sum()
    print("Peso nas avaliadas: " + ", ".join(f"{k}: {v:.0%}" for k, v in peso.items()))

    # ---------- 2) heterogeneidade ----------
    estat, gl, p = teste_interacao(base)
    h = heterogeneidade(res)
    print("\n=== 2) Heterogeneidade entre segmentos ===")
    estat_txt = f"{estat:,.0f}".replace(",", ".")
    print(f"Interação segmento x tempo (razão de verossimilhança): chi2 = {estat_txt} com {gl} gl, {texto_p(p)}")
    print(f"Q de Cochran = {h['Q']:.1f} ({h['gl']} gl, {texto_p(h['p_Q'])}) | I² = {h['I2_%']:.0f}% | "
          f"tau = {h['tau']:.3f} (escala log-OR)")
    print(f"OR de efeito fixo = {h['OR_efeito_fixo']:.3f} | OR de efeitos aleatórios = {h['OR_efeitos_aleatorios']:.3f} "
          f"(IC 95% {h['OR_re_ic_inf']:.3f} a {h['OR_re_ic_sup']:.3f})")
    print(f"Intervalo de predição para um segmento novo: {h['predicao_inf']:.3f} a {h['predicao_sup']:.3f}")
    het = pd.DataFrame([{**h, "chi2_interacao": estat, "gl_interacao": gl, "p_interacao": p}]).round(4)
    het.to_csv(OUT / f"p03_seg_heterogeneidade{sufixo}.csv", index=False)

    # ---------- 3) gráfico ----------
    floresta(res, OUT / f"p03_seg_floresta{sufixo}.png", h["OR_efeitos_aleatorios"])
    print(f"\nGerados: p03_seg_or_por_dia{sufixo}.csv, p03_seg_heterogeneidade{sufixo}.csv, p03_seg_floresta{sufixo}.png")


if __name__ == "__main__":
    main()