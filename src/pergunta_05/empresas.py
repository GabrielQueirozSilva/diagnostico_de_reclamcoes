"""Pergunta 5 (parte 2): dentro dos segmentos que mais pesam na queda, o que aconteceu com as empresas?

Mesmos recortes de evolucao.py (início = até 2024-12, fim = a partir de 2026-07).
Para cada segmento, separa a variação da taxa em:
    dentro   -> empresas que já existiam e mudaram a própria taxa (piora/melhora real)
    mix      -> empresas que existiam e mudaram de peso dentro do segmento
    entrada  -> empresas que só aparecem no fim
    saida    -> empresas que só aparecem no início

Uso:
    python -m src.pergunta_05.empresas                       # 3 segmentos que mais pesam na queda
    python -m src.pergunta_05.empresas --top 5               # 5 segmentos
    python -m src.pergunta_05.empresas -s "Nome exato do segmento"   # segmento específico
    python -m src.pergunta_05.empresas --min-aval 50         # volume mínimo p/ Wilson/Newcombe

Saídas:
    outputs/pergunta_05/empresas_<segmento>.csv     tabela completa por empresa
    outputs/pergunta_05/empresas_resumo.csv         uma linha por segmento (dentro / mix / entrada / saída)
"""
import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.db import get_engine
from src.pergunta_05.decomposicao import decompor

OUT = Path(__file__).resolve().parents[2] / "outputs" / "pergunta_05"
OUT.mkdir(parents=True, exist_ok=True)

INICIO_ATE = "2024-12"
FIM_A_PARTIR = "2026-07"

SQL = text("""
    WITH base AS (
      SELECT nome_fantasia,
             CASE WHEN ano_mes <= :inicio_ate THEN 'inicio'
                  WHEN ano_mes >= :fim_a_partir THEN 'fim' END AS periodo,
             avaliacao_reclamacao
      FROM ocorrencias_analise
      WHERE segmento_de_mercado = :segmento
        AND avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')
    )
    SELECT nome_fantasia,
           COUNT(*) FILTER (WHERE periodo = 'inicio') AS avaliadas_inicio,
           COUNT(*) FILTER (WHERE periodo = 'inicio' AND avaliacao_reclamacao = 'Resolvida') AS resolvidas_inicio,
           COUNT(*) FILTER (WHERE periodo = 'fim') AS avaliadas_fim,
           COUNT(*) FILTER (WHERE periodo = 'fim' AND avaliacao_reclamacao = 'Resolvida') AS resolvidas_fim
    FROM base
    WHERE periodo IS NOT NULL
    GROUP BY nome_fantasia
""")


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"\W+", "_", s.lower()).strip("_")[:50]


def segmentos_padrao(top):
    """Segmentos com maior contribuição negativa, lidos do CSV gerado por evolucao.py."""
    caminho = OUT / "segmentos_inicio_fim.csv"
    if not caminho.exists():
        raise SystemExit(f"{caminho} não existe. Rode evolucao.py antes ou use -s.")
    seg = pd.read_csv(caminho, index_col=0)  # já ordenado por contrib_total_pp (mais negativo primeiro)
    return seg.head(top).index.tolist()


def analisar_segmento(engine, segmento, min_aval):
    df = pd.read_sql(
        SQL, engine,
        params={"inicio_ate": INICIO_ATE, "fim_a_partir": FIM_A_PARTIR, "segmento": segmento},
    )
    if df.empty:
        print(f"[!] Nenhuma linha para '{segmento}'. Confira o nome exato (acentos, espaços).")
        return None
    w, resumo = decompor(df.set_index("nome_fantasia"), min_aval=min_aval)
    return w, resumo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--segmento", action="append", help="nome exato do segmento (repetível)")
    ap.add_argument("--top", type=int, default=3, help="quantos segmentos pegar do CSV (padrão 3)")
    ap.add_argument("--min-aval", type=int, default=30, help="mín. de avaliadas nos dois períodos para Wilson/Newcombe")
    args = ap.parse_args()

    engine = get_engine()
    segmentos = args.segmento or segmentos_padrao(args.top)

    linhas = []
    for seg in segmentos:
        res = analisar_segmento(engine, seg, args.min_aval)
        if res is None:
            continue
        w, r = res

        print("\n" + "=" * 90)
        print(seg)
        print(
            f"Taxa: {r['taxa_inicio']:.1%} -> {r['taxa_fim']:.1%} (variação {r['variacao_pp']:+.1f} pp)\n"
            f"  dentro (empresas que mudaram a própria taxa): {r['dentro_pp']:+.1f} pp\n"
            f"  mix (mudança de peso entre empresas):         {r['mix_pp']:+.1f} pp\n"
            f"  entrada de empresas:                          {r['entrada_pp']:+.1f} pp\n"
            f"  saída de empresas:                            {r['saida_pp']:+.1f} pp\n"
            f"Empresas: {r['n_estaveis']} estáveis, {r['n_entraram']} entraram, {r['n_sairam']} saíram"
        )

        cols = [
            "status", "avaliadas_inicio", "avaliadas_fim", "taxa_inicio", "taxa_fim",
            "contrib_dentro_pp", "contrib_mix_pp", "contrib_entrada_pp", "contrib_saida_pp",
            "contrib_total_pp", "leitura",
        ]
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 220)
        print("\nMaiores contribuições para a queda:")
        print(w.sort_values("contrib_total_pp")[cols].head(10).round(3))

        w.sort_values("contrib_total_pp")[cols].round(4).to_csv(OUT / f"empresas_{slug(seg)}.csv")
        linhas.append({"segmento": seg, **r})

    if linhas:
        pd.DataFrame(linhas).round(4).to_csv(OUT / "empresas_resumo.csv", index=False)


if __name__ == "__main__":
    main()