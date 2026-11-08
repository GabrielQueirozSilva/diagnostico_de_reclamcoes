"""Pergunta 5: como a taxa de resolução evolui? Por que ela caiu entre o início e o fim?

Compara dois recortes de 3 meses, por segmento:
    inicio = out-dez/2024      fim = jul-set/2026
Etapas (a conta está em decomposicao.py, compartilhada com pergunta_05_empresas.py):
    1. taxa de cada segmento em cada período
    2. diferença (fim - início) com intervalo de Newcombe -> queda clara / alta clara / inconclusivo
    3. decomposição da queda geral: efeito DENTRO dos segmentos vs. efeito de COMPOSIÇÃO (mix),
       com entrada/saída de segmentos tratada à parte (em vez de descartá-los)

Saída:
    outputs/segmentos_inicio_fim.csv
"""
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import get_engine
from decomposicao import decompor

OUT = Path(__file__).resolve().parent.parent / "outputs"
OUT.mkdir(exist_ok=True)

INICIO_ATE = "2024-12"
FIM_A_PARTIR = "2026-07"
MIN_AVAL = 30  # mínimo de avaliadas nos dois períodos para calcular Newcombe

SQL = text("""
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
""")


def carregar(engine):
    df = pd.read_sql(SQL, engine, params={"inicio_ate": INICIO_ATE, "fim_a_partir": FIM_A_PARTIR})
    w = df.pivot(index="segmento_de_mercado", columns="periodo", values=["avaliadas", "resolvidas"])
    w.columns = [f"{a}_{p}" for a, p in w.columns]
    return w.fillna(0).astype(int)  # segmento ausente em um período vira 0 (entrou/saiu), não é descartado


def inverter(w):
    """Troca início e fim: serve para repetir a decomposição usando o outro peso de referência."""
    return w.rename(columns={
        "avaliadas_inicio": "avaliadas_fim", "avaliadas_fim": "avaliadas_inicio",
        "resolvidas_inicio": "resolvidas_fim", "resolvidas_fim": "resolvidas_inicio",
    })


def main():
    w = carregar(get_engine())

    t, r = decompor(w, min_aval=MIN_AVAL)

    print(f"Segmentos: {r['n_estaveis']} nos dois períodos, {r['n_entraram']} só no fim, {r['n_sairam']} só no início")
    print(t["leitura"].value_counts())
    print(f"\nTaxa geral: {r['taxa_inicio']:.1%} -> {r['taxa_fim']:.1%} (variação {r['variacao_pp']:+.1f} pp)")
    print(
        f"dentro: {r['dentro_pp']:+.1f} pp | mix: {r['mix_pp']:+.1f} pp | "
        f"entrada: {r['entrada_pp']:+.1f} pp | saída: {r['saida_pp']:+.1f} pp | total: {r['total_pp']:+.1f} pp"
    )

    # A divisão dentro/composição depende do peso de referência (mix do início ou do fim).
    # Repetindo com os períodos invertidos obtemos o outro peso; reportar a faixa.
    _, r_inv = decompor(inverter(w), min_aval=MIN_AVAL)
    dentro_peso_inicio = r["dentro_pp"]
    dentro_peso_fim = -r_inv["dentro_pp"]
    v = r["variacao_pp"]
    faixa = sorted([dentro_peso_inicio / v, dentro_peso_fim / v])
    print(
        f"Efeito dentro dos segmentos: {dentro_peso_inicio:+.1f} pp (peso do início) | "
        f"{dentro_peso_fim:+.1f} pp (peso do fim) -> entre {faixa[0]:.0%} e {faixa[1]:.0%} da queda"
    )

    cols = [
        "status", "avaliadas_inicio", "avaliadas_fim", "taxa_inicio", "taxa_fim",
        "contrib_dentro_pp", "contrib_mix_pp", "contrib_entrada_pp", "contrib_saida_pp",
        "contrib_total_pp", "leitura",
    ]
    t = t.sort_values("contrib_total_pp")[cols]
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 220)
    print("\nSegmentos que mais puxaram a queda:")
    print(t.head(10).round(3))

    dez = t.contrib_total_pp.head(10).sum() / t.contrib_total_pp.sum()
    print(f"\nOs 10 primeiros respondem por {dez:.0%} da variação total")

    t.round(4).to_csv(OUT / "segmentos_inicio_fim.csv")


if __name__ == "__main__":
    main()