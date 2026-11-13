"""Pergunta 3 (por empresa): o sinal do tempo de resposta se mantém DENTRO da empresa?

Em por_segmento.py, Bancos tem OR por dia > 1 (esperar mais vem com mais resolução), ao contrário
de Telecom, Aéreo e Energia. Hipótese (não testada até aqui): composição entre empresas dentro do
segmento. Se as empresas mais lentas já têm taxa maior por outros motivos, o OR do segmento mistura
"entre empresas" com "dentro da empresa". Este script separa os dois.

Para cada segmento escolhido:
    1. OR por dia no nível do segmento (tempo_lin + C(mes)), como em por_segmento.py
    2. OR por dia DENTRO da empresa (tempo_lin + C(empresa) + C(mes)), com dois ICs:
       o do modelo e o robusto a agrupamento por empresa (reclamações da mesma empresa
       não são independentes). Com poucas empresas (< 30) o IC robusto tende a ficar estreito demais.
    3. Correlação entre empresas (ponderada por avaliadas): tempo médio x taxa
    4. OR por dia de cada empresa grande, separadamente (tempo_lin + C(mes)), com a contagem de
       empresas com queda clara, alta clara e inconclusivo
    5. Gráfico de floresta por segmento (empresas maiores + linhas dos dois ORs de referência)

Só entram empresas com pelo menos MIN_EMP avaliadas e respondidas no segmento (nos modelos 1 a 3)
e MIN_EMP_INDIVIDUAL (no item 4). O tempo tem teto de 15 dias, como nos outros scripts.

Uso:
    python -m src.pergunta_03.por_empresa
    python -m src.pergunta_03.por_empresa --sem-prazo-estendido              # sensibilidade (D-006)
    python -m src.pergunta_03.por_empresa --segmentos "Energia" "Farmácias"  # trechos do nome do segmento

Padrão: Bancos, Telecom e Transporte Aéreo. O modelo com efeito fixo de empresa é pesado em
Bancos (centenas de empresas): pode levar alguns minutos.

Saídas (em outputs/pergunta_03/; com a flag, o nome ganha o sufixo _sem_estendido):
    p03_emp_modelos.csv         um linha por segmento: OR de segmento x OR dentro da empresa
    p03_emp_por_empresa.csv     OR por dia de cada empresa grande
    p03_emp_floresta_<segmento>.png
"""
import argparse
import re
import unicodedata

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from sqlalchemy import text

from src.db import get_engine
from src.pergunta_03.base import OUT, TETO_DIAS

SEGMENTOS_PADRAO = ["Bancos, Financeiras", "Operadoras de Telecomunica", "Transporte Aéreo"]
MIN_EMP = 500               # avaliadas mínimas da empresa para entrar nos modelos do segmento
MIN_EMP_INDIVIDUAL = 5000   # avaliadas mínimas para ter OR próprio
MAX_EMP_GRAFICO = 15        # empresas mostradas no gráfico (as de maior volume)
POUCOS_CLUSTERS = 30

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 60)


# ---------- dados ----------
def carregar(engine, padroes, sem_estendido):
    """Uma linha por segmento x empresa x mês x dia de tempo (tempo limitado a TETO_DIAS)."""
    extra = "AND NOT COALESCE(periodo_prazo_estendido, FALSE)" if sem_estendido else ""
    sql = text(f"""
        SELECT segmento_de_mercado AS seg,
               nome_fantasia AS emp,
               ano_mes AS mes,
               LEAST(tempo_resposta_valido, {TETO_DIAS}) AS tempo_lin,
               COUNT(*) AS avaliadas,
               COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida') AS resolvidas
        FROM ocorrencias_analise
        WHERE avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')
          AND respondida = 'S'
          AND tempo_resposta_valido IS NOT NULL
          AND segmento_de_mercado ILIKE ANY (:padroes)
          {extra}
        GROUP BY 1, 2, 3, 4
    """)
    df = pd.read_sql(sql, engine, params={"padroes": [f"%{p}%" for p in padroes]})
    df["tempo_lin"] = df["tempo_lin"].astype(float)
    df["nao_resolvidas"] = df["avaliadas"] - df["resolvidas"]
    return df


# ---------- modelos ----------
def ajustar(d, formula, grupos=None, inicio=None):
    """GLM binomial agregado. Com `grupos`, o erro-padrão é robusto a agrupamento por empresa."""
    X = patsy.dmatrix(formula, d, return_type="dataframe")
    y = np.column_stack([d["resolvidas"], d["nao_resolvidas"]])
    m = sm.GLM(y, X, family=sm.families.Binomial())
    if grupos is None:
        return m.fit(start_params=inicio)
    return m.fit(start_params=inicio, cov_type="cluster",
                 cov_kwds={"groups": pd.factorize(np.asarray(grupos))[0]})


def razao(r, termo="tempo_lin"):
    ci = r.conf_int().loc[termo]
    return float(np.exp(r.params[termo])), float(np.exp(ci[0])), float(np.exp(ci[1]))


def leitura(lo, hi):
    return "queda clara" if hi < 1 else "alta clara" if lo > 1 else "inconclusivo"


def correlacao_ponderada(x, y, w):
    mx, my = np.average(x, weights=w), np.average(y, weights=w)
    cov = np.average((x - mx) * (y - my), weights=w)
    dp = np.sqrt(np.average((x - mx) ** 2, weights=w) * np.average((y - my) ** 2, weights=w))
    return float(cov / dp) if dp > 0 else float("nan")


def slug(nome):
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:40]


def texto_leitura(or_seg, ic_seg, or_emp, ic_emp_robusto):
    """Frase curta comparando o sinal do segmento com o sinal dentro da empresa."""
    l_seg, l_emp = leitura(*ic_seg), leitura(*ic_emp_robusto)
    if l_emp == "inconclusivo":
        return ("dentro da empresa o efeito some (IC robusto inclui 1): o sinal do segmento "
                "vem, ao menos em parte, de diferenças entre empresas")
    if l_seg == l_emp:
        return f"o sinal ({l_emp}) se mantém dentro da empresa: não é só composição entre empresas"
    if l_seg == "inconclusivo":
        return (f"no segmento o efeito é inconclusivo, mas dentro da empresa há {l_emp}: "
                "diferenças entre empresas escondiam o efeito")
    return (f"o sinal INVERTE dentro da empresa (segmento: {l_seg}; dentro da empresa: {l_emp}): "
            "composição entre empresas")


# ---------- análise de um segmento ----------
def analisar_segmento(s, d_tudo):
    n_aval_total = int(d_tudo["avaliadas"].sum())
    n_emp_total = d_tudo["emp"].nunique()
    d = d_tudo[d_tudo.groupby("emp")["avaliadas"].transform("sum") >= MIN_EMP]
    n_emp = d["emp"].nunique()
    cobertura = d["avaliadas"].sum() / n_aval_total

    print(f"\n[{s}]\n  {n_emp} empresas com >= {MIN_EMP} avaliadas (de {n_emp_total}); "
          f"cobrem {cobertura:.1%} das avaliadas do segmento ({int(d['avaliadas'].sum()):,})".replace(",", "."))
    if n_emp < 2:
        print("  [!] menos de 2 empresas: o modelo com efeito fixo de empresa não se aplica")
        return None, [], d

    r_seg = ajustar(d, "tempo_lin + C(mes)")
    or_seg, lo_seg, hi_seg = razao(r_seg)

    f_emp = "tempo_lin + C(emp) + C(mes)"
    r_emp = ajustar(d, f_emp)
    or_emp, lo_emp, hi_emp = razao(r_emp)
    r_cl = ajustar(d, f_emp, grupos=d["emp"], inicio=r_emp.params)
    _, lo_cl, hi_cl = razao(r_cl)

    # correlação entre empresas: tempo médio x taxa
    e = d.assign(soma_t=d["tempo_lin"] * d["avaliadas"]).groupby("emp").agg(
        avaliadas=("avaliadas", "sum"), resolvidas=("resolvidas", "sum"), soma_t=("soma_t", "sum"))
    e["tempo_medio"] = e["soma_t"] / e["avaliadas"]
    e["taxa"] = e["resolvidas"] / e["avaliadas"]
    corr = correlacao_ponderada(e["tempo_medio"], e["taxa"], e["avaliadas"])

    print(f"  OR por dia, nível do segmento (+ mês):        {or_seg:.3f} ({lo_seg:.3f} a {hi_seg:.3f})")
    print(f"  OR por dia, dentro da empresa (+ empresa):    {or_emp:.3f} ({lo_emp:.3f} a {hi_emp:.3f})")
    print(f"     IC robusto a agrupamento por empresa:      ({lo_cl:.3f} a {hi_cl:.3f})"
          + (f"  [!] só {n_emp} empresas: IC provavelmente estreito demais" if n_emp < POUCOS_CLUSTERS else ""))
    print(f"  Correlação entre empresas, tempo médio x taxa: {corr:+.2f}")

    # OR de cada empresa grande
    linhas = []
    for emp, de in d[d.groupby("emp")["avaliadas"].transform("sum") >= MIN_EMP_INDIVIDUAL].groupby("emp"):
        if de["tempo_lin"].nunique() < 2:
            continue
        try:
            o, lo, hi = razao(ajustar(de, "tempo_lin + C(mes)"))
        except Exception as ex:
            print(f"  [!] {emp}: modelo não ajustou ({ex})")
            continue
        n = int(de["avaliadas"].sum())
        linhas.append({
            "seg": s, "emp": emp, "avaliadas": n,
            "taxa_pct": de["resolvidas"].sum() / n * 100,
            "tempo_medio": float((de["tempo_lin"] * de["avaliadas"]).sum() / n),
            "OR_por_dia": o, "or_inf": lo, "or_sup": hi, "leitura": leitura(lo, hi),
        })
    ind = pd.DataFrame(linhas)
    if len(ind):
        cont = ind["leitura"].value_counts()
        peso = ind.groupby("leitura")["avaliadas"].sum() / ind["avaliadas"].sum()
        print(f"  Empresas com OR próprio (>= {MIN_EMP_INDIVIDUAL} aval.): {len(ind)} | "
              + ", ".join(f"{k}: {v}" for k, v in cont.items()))
        print("     peso nas avaliadas delas: " + ", ".join(f"{k}: {v:.0%}" for k, v in peso.items()))
    else:
        print(f"  Nenhuma empresa com >= {MIN_EMP_INDIVIDUAL} avaliadas para OR próprio")

    frase = texto_leitura(or_seg, (lo_seg, hi_seg), or_emp, (lo_cl, hi_cl))
    print(f"  Leitura: {frase}")

    resumo = {
        "seg": s, "avaliadas": int(d["avaliadas"].sum()), "empresas": n_emp,
        "cobertura_%": round(cobertura * 100, 1),
        "OR_segmento": or_seg, "seg_inf": lo_seg, "seg_sup": hi_seg,
        "OR_dentro_empresa": or_emp, "emp_inf": lo_emp, "emp_sup": hi_emp,
        "emp_inf_robusto": lo_cl, "emp_sup_robusto": hi_cl,
        "corr_entre_empresas": corr,
        "empresas_queda": int((ind["leitura"] == "queda clara").sum()) if len(ind) else 0,
        "empresas_alta": int((ind["leitura"] == "alta clara").sum()) if len(ind) else 0,
        "empresas_inconclusivo": int((ind["leitura"] == "inconclusivo").sum()) if len(ind) else 0,
        "leitura": frase,
    }
    return resumo, ind, d


# ---------- gráfico ----------
def floresta(s, ind, or_seg, or_emp, caminho):
    g = ind.nlargest(MAX_EMP_GRAFICO, "avaliadas").sort_values("OR_por_dia").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10, 0.32 * len(g) + 2))
    ax.errorbar(g["OR_por_dia"], g.index,
                xerr=[g["OR_por_dia"] - g["or_inf"], g["or_sup"] - g["OR_por_dia"]],
                fmt="o", capsize=3)
    ax.axvline(1, linestyle="--", color="gray", label="sem associação (OR = 1)")
    ax.axvline(or_seg, linestyle=":", color="C1", label=f"segmento: {or_seg:.3f}")
    ax.axvline(or_emp, linestyle="-.", color="C2", label=f"dentro da empresa (todas): {or_emp:.3f}")
    ax.set_yticks(g.index)
    ax.set_yticklabels([f"{e[:40]} (n={format(n, ',d').replace(',', '.')})"
                        for e, n in zip(g["emp"], g["avaliadas"])], fontsize=8)
    ax.set_ylim(-1, len(g))
    ax.set_xlabel("Odds ratio de resolução por dia de espera, ajustado por mês (IC 95%)")
    ax.set_title(f"{s[:70]}: as {len(g)} maiores empresas", fontsize=10)
    ax.legend(loc="lower right", fontsize=8)
    plt.tight_layout()
    plt.savefig(caminho, dpi=150)
    plt.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segmentos", nargs="+", default=SEGMENTOS_PADRAO,
                    help="trechos do nome dos segmentos (padrão: Bancos, Telecom e Transporte Aéreo)")
    ap.add_argument("--sem-prazo-estendido", action="store_true",
                    help="repete tudo sem os dias de prazo estendido (D-006)")
    args = ap.parse_args()
    sufixo = "_sem_estendido" if args.sem_prazo_estendido else ""

    engine = get_engine()
    df = carregar(engine, args.segmentos, args.sem_prazo_estendido)
    if df.empty:
        raise SystemExit(f"Nenhum segmento encontrado para {args.segmentos}")
    print("Segmentos encontrados: " + "; ".join(sorted(df["seg"].unique()))
          + (" | sem prazo estendido" if args.sem_prazo_estendido else ""))

    resumos, individuais = [], []
    for s in sorted(df["seg"].unique()):
        resumo, ind, _ = analisar_segmento(s, df[df["seg"] == s])
        if resumo is None:
            continue
        resumos.append(resumo)
        if len(ind):
            individuais.append(ind)
            floresta(s, ind, resumo["OR_segmento"], resumo["OR_dentro_empresa"],
                     OUT / f"p03_emp_floresta_{slug(s)}{sufixo}.png")

    if resumos:
        pd.DataFrame(resumos).round(4).to_csv(OUT / f"p03_emp_modelos{sufixo}.csv", index=False)
    if individuais:
        pd.concat(individuais).round(4).to_csv(OUT / f"p03_emp_por_empresa{sufixo}.csv", index=False)
    print(f"\nSaídas gravadas em {OUT} (p03_emp_*{sufixo})")


if __name__ == "__main__":
    main()