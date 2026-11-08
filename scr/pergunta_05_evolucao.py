"""Pergunta 5: como a taxa de resolução evolui? Por que ela caiu entre o início e o fim?

Compara dois recortes de meses, por segmento. Recorte padrão:
    inicio = até dez/2024 (a série começa em out/2024)      fim = a partir de jul/2026
Etapas (a conta está em decomposicao.py, compartilhada com pergunta_05_empresas.py):
    1. taxa de cada segmento em cada período
    2. diferença (fim - início) com intervalo de Newcombe -> queda clara / alta clara / inconclusivo
    3. decomposição da queda geral: efeito DENTRO dos segmentos vs. efeito de COMPOSIÇÃO (mix),
       com entrada/saída de segmentos tratada à parte (em vez de descartá-los)

Uso:
    python scr/pergunta_05_evolucao.py                   # recorte padrão; grava outputs/segmentos_inicio_fim.csv
    python scr/pergunta_05_evolucao.py --sensibilidade   # repete a decomposição em vários recortes e compara
    python scr/pergunta_05_evolucao.py --inicio-de 2024-11 --inicio-ate 2025-01 --fim-de 2026-07
        recorte avulso (qualquer um dos 4 limites, formato AAAA-MM): grava em
        outputs/segmentos_inicio_fim_<recorte>.csv e NÃO sobrescreve o CSV padrão, que é o que
        pergunta_05_empresas.py e pergunta_05_mensal.py leem.

Saídas (em outputs/):
    segmentos_inicio_fim.csv        (recorte padrão)
    sensibilidade_recortes.csv      (com --sensibilidade)
"""
import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import get_engine
from decomposicao import decompor

OUT = Path(__file__).resolve().parent.parent / "outputs"
OUT.mkdir(exist_ok=True)

# Limites dos recortes (AAAA-MM, inclusive). Outros scripts importam INICIO_ATE e FIM_A_PARTIR daqui.
INICIO_DE = "0000-00"      # sem limite inferior: começa no primeiro mês da base
INICIO_ATE = "2024-12"
FIM_A_PARTIR = "2026-07"
FIM_ATE = "9999-12"        # sem limite superior: vai até o último mês da base
MIN_AVAL = 30              # mínimo de avaliadas nos dois períodos para calcular Newcombe

PADRAO = (INICIO_DE, INICIO_ATE, FIM_A_PARTIR, FIM_ATE)

# Recortes comparados em --sensibilidade: (nome, inicio_de, inicio_ate, fim_de, fim_ate). Edite à vontade.
JANELAS = [
    ("padrão: out-dez/24 -> jul-set/26", *PADRAO),
    ("início sem out/24: nov/24-jan/25 -> jul-set/26", "2024-11", "2025-01", "2026-07", FIM_ATE),
    ("início jan-mar/25 -> jul-set/26", "2025-01", "2025-03", "2026-07", FIM_ATE),
    ("fim no piso: out-dez/24 -> abr-jun/26", INICIO_DE, INICIO_ATE, "2026-04", "2026-06"),
    ("sem as pontas: nov/24-jan/25 -> abr-jun/26", "2024-11", "2025-01", "2026-04", "2026-06"),
    ("12 meses x 12 meses: out/24-set/25 -> out/25-set/26", "2024-10", "2025-09", "2025-10", "2026-09"),
]

SQL = text("""
    WITH base AS (
      SELECT segmento_de_mercado,
             CASE WHEN ano_mes BETWEEN :inicio_de AND :inicio_ate THEN 'inicio'
                  WHEN ano_mes BETWEEN :fim_de AND :fim_ate THEN 'fim' END AS periodo,
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

COLUNAS = ["avaliadas_inicio", "resolvidas_inicio", "avaliadas_fim", "resolvidas_fim"]


def carregar(engine, inicio_de, inicio_ate, fim_de, fim_ate):
    df = pd.read_sql(
        SQL, engine,
        params={"inicio_de": inicio_de, "inicio_ate": inicio_ate, "fim_de": fim_de, "fim_ate": fim_ate},
    )
    if df.empty:
        raise ValueError("nenhuma linha nos recortes informados")
    w = df.pivot(index="segmento_de_mercado", columns="periodo", values=["avaliadas", "resolvidas"])
    w.columns = [f"{a}_{p}" for a, p in w.columns]
    for c in COLUNAS:
        if c not in w.columns:
            w[c] = 0
    w = w[COLUNAS].fillna(0).astype(int)  # segmento ausente em um período vira 0 (entrou/saiu), não é descartado
    if w["avaliadas_inicio"].sum() == 0 or w["avaliadas_fim"].sum() == 0:
        raise ValueError("um dos períodos não tem reclamações avaliadas")
    return w


def inverter(w):
    """Troca início e fim: serve para repetir a decomposição usando o outro peso de referência."""
    return w.rename(columns={
        "avaliadas_inicio": "avaliadas_fim", "avaliadas_fim": "avaliadas_inicio",
        "resolvidas_inicio": "resolvidas_fim", "resolvidas_fim": "resolvidas_inicio",
    })


def analisar(w):
    """Decomposição + faixa do efeito dentro (a divisão dentro/composição depende do peso de referência)."""
    t, r = decompor(w, min_aval=MIN_AVAL)
    _, r_inv = decompor(inverter(w), min_aval=MIN_AVAL)
    dentro_peso_inicio = r["dentro_pp"]
    dentro_peso_fim = -r_inv["dentro_pp"]
    v = r["variacao_pp"]
    faixa = sorted([dentro_peso_inicio / v, dentro_peso_fim / v]) if v else [float("nan")] * 2
    return t, r, dentro_peso_inicio, dentro_peso_fim, faixa


def parcela_top10(t):
    """Parcela da variação total explicada pelos 10 segmentos que mais puxaram na direção da variação."""
    total = t["contrib_total_pp"].sum()
    if not total:
        return float("nan")
    ordem = t["contrib_total_pp"].sort_values(ascending=total < 0)
    return ordem.head(10).sum() / total


def relatorio(w):
    t, r, di, df_, faixa = analisar(w)

    print(f"Segmentos: {r['n_estaveis']} nos dois períodos, {r['n_entraram']} só no fim, {r['n_sairam']} só no início")
    print(t["leitura"].value_counts())
    print(f"\nTaxa geral: {r['taxa_inicio']:.1%} -> {r['taxa_fim']:.1%} (variação {r['variacao_pp']:+.1f} pp)")
    print(
        f"dentro: {r['dentro_pp']:+.1f} pp | mix: {r['mix_pp']:+.1f} pp | "
        f"entrada: {r['entrada_pp']:+.1f} pp | saída: {r['saida_pp']:+.1f} pp | total: {r['total_pp']:+.1f} pp"
    )
    print(
        f"Efeito dentro dos segmentos: {di:+.1f} pp (peso do início) | "
        f"{df_:+.1f} pp (peso do fim) -> entre {faixa[0]:.0%} e {faixa[1]:.0%} da queda"
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
    print(f"\nOs 10 primeiros respondem por {parcela_top10(t):.0%} da variação total")
    return t


def sensibilidade(engine):
    linhas = []
    for nome, a, b, c, d in JANELAS:
        try:
            t, r, di, df_, faixa = analisar(carregar(engine, a, b, c, d))
        except ValueError as e:
            print(f"[!] {nome}: {e}")
            continue
        linhas.append({
            "janela": nome,
            "taxa_inicio_%": r["taxa_inicio"] * 100,
            "taxa_fim_%": r["taxa_fim"] * 100,
            "variacao_pp": r["variacao_pp"],
            "dentro_peso_inicio_pp": di,
            "dentro_peso_fim_pp": df_,
            "dentro_%_da_queda_min": faixa[0] * 100,
            "dentro_%_da_queda_max": faixa[1] * 100,
            "top10_%_da_variacao": parcela_top10(t) * 100,
        })
    res = pd.DataFrame(linhas).round(1)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 60)
    print(res.to_string(index=False))
    res.to_csv(OUT / "sensibilidade_recortes.csv", index=False)
    print(f"\nSalvo em {OUT / 'sensibilidade_recortes.csv'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sensibilidade", action="store_true", help="compara a decomposição em vários recortes (lista JANELAS)")
    ap.add_argument("--inicio-de", help="primeiro mês do período inicial (AAAA-MM)")
    ap.add_argument("--inicio-ate", help="último mês do período inicial (AAAA-MM)")
    ap.add_argument("--fim-de", help="primeiro mês do período final (AAAA-MM)")
    ap.add_argument("--fim-ate", help="último mês do período final (AAAA-MM)")
    args = ap.parse_args()

    engine = get_engine()

    if args.sensibilidade:
        sensibilidade(engine)
        return

    recorte = (
        args.inicio_de or INICIO_DE,
        args.inicio_ate or INICIO_ATE,
        args.fim_de or FIM_A_PARTIR,
        args.fim_ate or FIM_ATE,
    )
    try:
        w = carregar(engine, *recorte)
    except ValueError as e:
        raise SystemExit(f"Recorte {recorte}: {e}")
    t = relatorio(w)

    if recorte == PADRAO:
        destino = OUT / "segmentos_inicio_fim.csv"
    else:
        destino = OUT / ("segmentos_inicio_fim_" + "_".join(recorte) + ".csv")
        print(f"\n[recorte avulso] não sobrescrevi segmentos_inicio_fim.csv; gravei em {destino.name}")
    t.round(4).to_csv(destino)


if __name__ == "__main__":
    main()