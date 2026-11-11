"""Pergunta 3: o tempo de resposta se associa à resolução?

Base: reclamações avaliadas e respondidas (respondida = 'S') com tempo_resposta_valido.
Etapas:
    1. Taxa de resolução por faixa de tempo de resposta, com IC de Wilson (bruta)
    2. Tempo médio de resposta em resolvidas vs. não resolvidas
    3. Associação AJUSTADA: regressão logística binomial com efeito fixo de segmento e de mês
       (controla o "o período/segmento afeta as duas variáveis ao mesmo tempo", ver notas.md)
    4. Sensibilidade (D-006): refazer sem os dias de prazo estendido e só com tempo <= 10

Uso:
    python -m src.pergunta_03.associacao
    (depois, para entender de onde vem a diferença bruto x ajustado: python -m src.pergunta_03.diagnostico)

Saídas (em outputs/pergunta_03/):
    p03_faixas.csv              taxa bruta por faixa
    p03_faixas_ajustadas.csv    OR por faixa (ref. 0-2 dias), ajustado por segmento e mês
    p03_modelos.csv             OR por dia de espera, bruto e ajustado, em 3 cenários
    p03_tempo_vs_resolucao.png
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.db import get_engine
from src.pergunta_03.base import (
    OUT, REFERENCIA, carregar, modelo, razao_de_chances, razoes_por_faixa,
    segmentos_grandes, tabela_faixas,
)


def main():
    engine = get_engine()
    df = carregar(engine)
    print(f"Base: {df['avaliadas'].sum():,} avaliadas e respondidas".replace(",", "."))

    # ---------- 1) taxa por faixa (bruta) ----------
    f = tabela_faixas(df)
    f.round(4).to_csv(OUT / "p03_faixas.csv")
    print("\nTaxa de resolução por faixa de tempo (bruta):")
    print((f[["avaliadas", "taxa", "ic_inf", "ic_sup"]] * [1, 100, 100, 100]).round(1).to_string())

    # ---------- 2) tempo médio: resolvidas vs. não resolvidas ----------
    media_res = (df["tempo"] * df["resolvidas"]).sum() / df["resolvidas"].sum()
    media_nao = (df["tempo"] * df["nao_resolvidas"]).sum() / df["nao_resolvidas"].sum()
    print(f"\nTempo médio: resolvidas {media_res:.2f} d | não resolvidas {media_nao:.2f} d")

    # ---------- 3) e 4) modelos ----------
    base = segmentos_grandes(df)
    cenarios = {
        "todos": base,
        "sem prazo estendido": base[~base["estendido"]],
        "só tempo <= 10": base[base["tempo"] <= 10],
    }
    linhas = []
    for nome, d in cenarios.items():
        for ajuste, formula in [
            ("bruto", "tempo_lin"),
            ("ajustado seg+mês", "tempo_lin + C(seg) + C(mes)"),
        ]:
            or_, lo, hi = razao_de_chances(modelo(d, formula), "tempo_lin")
            linhas.append({"cenario": nome, "ajuste": ajuste, "n": int(d["avaliadas"].sum()),
                           "OR_por_dia": or_, "ic_inf": lo, "ic_sup": hi})
    modelos = pd.DataFrame(linhas).round(4)
    modelos.to_csv(OUT / "p03_modelos.csv", index=False)
    print("\nOdds ratio de resolução por dia adicional de espera (OR < 1 = menos resolução):")
    print(modelos.to_string(index=False))

    # faixas ajustadas (referência 0-2 dias)
    r = modelo(base, f"C(faixa, Treatment('{REFERENCIA}')) + C(seg) + C(mes)")
    adj = razoes_por_faixa(r).round(4)
    adj.to_csv(OUT / "p03_faixas_ajustadas.csv", index=False)
    print(f"\nOR ajustado por faixa (ref. {REFERENCIA} dias):")
    print(adj.round(3).to_string(index=False))

    # ---------- gráfico ----------
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(f))
    ax.errorbar(x, f["taxa"] * 100,
                yerr=[(f["taxa"] - f["ic_inf"]) * 100, (f["ic_sup"] - f["taxa"]) * 100],
                fmt="o-", capsize=4)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{i}\n(n={n:,})".replace(",", ".") for i, n in zip(f.index, f["avaliadas"])])
    ax.set_xlabel("Tempo de resposta da empresa (dias)")
    ax.set_ylabel("Taxa de resolução (%) com IC 95% (Wilson)")
    ax.set_title("Taxa de resolução por faixa de tempo de resposta (bruta)")
    plt.tight_layout()
    plt.savefig(OUT / "p03_tempo_vs_resolucao.png", dpi=150)
    plt.close()

    print("\nGerados: p03_faixas.csv, p03_faixas_ajustadas.csv, p03_modelos.csv, p03_tempo_vs_resolucao.png")


if __name__ == "__main__":
    main()