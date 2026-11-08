"""Funções reutilizáveis: taxa, Wilson, Newcombe e decomposição início -> fim.

A entrada é uma tabela com uma linha por entidade (segmento ou empresa) e as colunas:
    avaliadas_inicio, resolvidas_inicio, avaliadas_fim, resolvidas_fim

A decomposição da variação da taxa do grupo (R_fim - R_inicio), com s = peso da entidade
(avaliadas da entidade / avaliadas do grupo no período) e r = taxa da entidade:

    estável (existe nos dois períodos)
        dentro = s0 * (r1 - r0)           mudança da taxa da própria entidade
        mix    = (s1 - s0) * (r1 - R1)    mudança do peso da entidade
    entrou (só no fim)
        entrada = s1 * (r1 - R1)
    saiu (só no início)
        saida = -s0 * (r0 - R1)

As quatro colunas somam exatamente R1 - R0 (confirmado em `resumo`).
"""
import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportion_confint


def decompor(w: pd.DataFrame, min_aval: int = 30):
    """Retorna (tabela por entidade, dict-resumo). `min_aval` vale só para a leitura estatística."""
    w = w.copy()
    n0, n1 = w["avaliadas_inicio"], w["avaliadas_fim"]
    r0n, r1n = w["resolvidas_inicio"], w["resolvidas_fim"]

    w["status"] = np.select([n0 == 0, n1 == 0], ["entrou", "saiu"], "estavel")
    w["taxa_inicio"] = r0n / n0.replace(0, np.nan)
    w["taxa_fim"] = r1n / n1.replace(0, np.nan)

    R0 = r0n.sum() / n0.sum()
    R1 = r1n.sum() / n1.sum()
    s0 = n0 / n0.sum()
    s1 = n1 / n1.sum()
    w["share_inicio"], w["share_fim"] = s0, s1

    est = w["status"] == "estavel"
    ent = w["status"] == "entrou"
    sai = w["status"] == "saiu"

    w["contrib_dentro_pp"] = np.where(est, s0 * (w.taxa_fim - w.taxa_inicio) * 100, 0.0)
    w["contrib_mix_pp"] = np.where(est, (s1 - s0) * (w.taxa_fim - R1) * 100, 0.0)
    w["contrib_entrada_pp"] = np.where(ent, s1 * (w.taxa_fim - R1) * 100, 0.0)
    w["contrib_saida_pp"] = np.where(sai, -s0 * (w.taxa_inicio - R1) * 100, 0.0)
    w["contrib_total_pp"] = (
        w.contrib_dentro_pp + w.contrib_mix_pp + w.contrib_entrada_pp + w.contrib_saida_pp
    )

    # Wilson (cada período) e Newcombe (diferença) só para estáveis com volume mínimo
    ok = est & (n0 >= min_aval) & (n1 >= min_aval)
    w["dif_pp"] = np.nan
    w["dif_inf_pp"] = np.nan
    w["dif_sup_pp"] = np.nan
    if ok.any():
        li0, ls0 = proportion_confint(r0n[ok], n0[ok], alpha=0.05, method="wilson")
        li1, ls1 = proportion_confint(r1n[ok], n1[ok], alpha=0.05, method="wilson")
        t0, t1 = w.loc[ok, "taxa_inicio"].to_numpy(), w.loc[ok, "taxa_fim"].to_numpy()
        d = t1 - t0
        w.loc[ok, "dif_pp"] = d * 100
        w.loc[ok, "dif_inf_pp"] = (d - np.sqrt((t1 - np.asarray(li1)) ** 2 + (np.asarray(ls0) - t0) ** 2)) * 100
        w.loc[ok, "dif_sup_pp"] = (d + np.sqrt((np.asarray(ls1) - t1) ** 2 + (t0 - np.asarray(li0)) ** 2)) * 100

    w["leitura"] = np.select(
        [~est, est & ~ok, w.dif_sup_pp < 0, w.dif_inf_pp > 0],
        [w["status"], "volume baixo", "queda clara", "alta clara"],
        "inconclusivo",
    )

    resumo = {
        "taxa_inicio": R0,
        "taxa_fim": R1,
        "variacao_pp": (R1 - R0) * 100,
        "dentro_pp": w.contrib_dentro_pp.sum(),
        "mix_pp": w.contrib_mix_pp.sum(),
        "entrada_pp": w.contrib_entrada_pp.sum(),
        "saida_pp": w.contrib_saida_pp.sum(),
        "total_pp": w.contrib_total_pp.sum(),
        "n_estaveis": int(est.sum()),
        "n_entraram": int(ent.sum()),
        "n_sairam": int(sai.sum()),
    }
    # checagem: as contribuições precisam fechar com a variação observada
    assert abs(resumo["total_pp"] - resumo["variacao_pp"]) < 1e-6, "decomposição não fecha"
    return w, resumo