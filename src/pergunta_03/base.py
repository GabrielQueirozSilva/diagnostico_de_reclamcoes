"""Pergunta 3: o tempo de resposta se associa à resolução?

Módulo compartilhado por associacao.py e diagnostico.py: constantes, carga dos dados e
funções de modelo.

Base: reclamações avaliadas E respondidas (respondida = 'S') com tempo_resposta_valido
(a view já transforma os negativos em NULL, D-007). A flag periodo_prazo_estendido também
vem da view (D-006).
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from sqlalchemy import text
from statsmodels.stats.proportion import proportion_confint

OUT = Path(__file__).resolve().parents[2] / "outputs" / "pergunta_03"
OUT.mkdir(parents=True, exist_ok=True)

MIN_AVALIADAS_SEG = 500   # segmentos menores ficam fora dos modelos (evita separação perfeita)
MIN_AVALIADAS_EMP = 500   # idem para empresas (só no diagnóstico com --empresa)
TETO_DIAS = 15            # no termo linear, tempos acima disso valem 15 (cauda longa de 2024)
FAIXAS = [-1, 2, 5, 10, 15, np.inf]
ROTULOS = ["0-2", "3-5", "6-10", "11-15", "16+"]
REFERENCIA = "0-2"

_FILTRO = """
    FROM ocorrencias_analise
    WHERE avaliacao_reclamacao IN ('Resolvida', 'Não Resolvida')
      AND respondida = 'S'
      AND tempo_resposta_valido IS NOT NULL
"""

SQL_BASE = text(f"""
    SELECT segmento_de_mercado AS seg,
           ano_mes AS mes,
           COALESCE(periodo_prazo_estendido, FALSE) AS estendido,
           tempo_resposta_valido AS tempo,
           COUNT(*) AS avaliadas,
           COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida') AS resolvidas
    {_FILTRO}
    GROUP BY 1, 2, 3, 4
""")

SQL_EMPRESA = text(f"""
    SELECT nome_fantasia AS emp,
           ano_mes AS mes,
           LEAST(tempo_resposta_valido, {TETO_DIAS}) AS tempo_lin,
           COUNT(*) AS avaliadas,
           COUNT(*) FILTER (WHERE avaliacao_reclamacao = 'Resolvida') AS resolvidas
    {_FILTRO}
    GROUP BY 1, 2, 3
""")


def carregar(engine):
    """Uma linha por segmento x mês x prazo estendido x dia de tempo de resposta."""
    df = pd.read_sql(SQL_BASE, engine)
    df["nao_resolvidas"] = df["avaliadas"] - df["resolvidas"]
    df["estendido"] = df["estendido"].astype(bool)
    df["ext"] = df["estendido"].astype(int)
    df["tempo_lin"] = df["tempo"].clip(upper=TETO_DIAS)
    df["faixa"] = pd.cut(df["tempo"], bins=FAIXAS, labels=ROTULOS)
    return df


def carregar_empresas(engine):
    """Uma linha por empresa x mês x dia de tempo (tempo já limitado a TETO_DIAS)."""
    df = pd.read_sql(SQL_EMPRESA, engine)
    df["nao_resolvidas"] = df["avaliadas"] - df["resolvidas"]
    return df


def segmentos_grandes(df):
    return df[df.groupby("seg")["avaliadas"].transform("sum") >= MIN_AVALIADAS_SEG]


def tabela_faixas(d):
    """Taxa bruta de resolução por faixa de tempo, com IC de 95% de Wilson."""
    t = d.groupby("faixa", observed=True)[["avaliadas", "resolvidas"]].sum()
    t["taxa"] = t["resolvidas"] / t["avaliadas"]
    t["ic_inf"], t["ic_sup"] = proportion_confint(
        t["resolvidas"], t["avaliadas"], alpha=0.05, method="wilson"
    )
    return t


def modelo(d, formula):
    """GLM binomial agregado (sucessos, fracassos) com a fórmula do patsy."""
    d = d.copy()
    if "faixa" in d.columns and isinstance(d["faixa"].dtype, pd.CategoricalDtype):
        d["faixa"] = d["faixa"].cat.remove_unused_categories()
    X = patsy.dmatrix(formula, d, return_type="dataframe")
    y = np.column_stack([d["resolvidas"], d["nao_resolvidas"]])
    return sm.GLM(y, X, family=sm.families.Binomial()).fit()


def razao_de_chances(r, termo):
    """Odds ratio e IC de 95% de um termo do modelo."""
    ci = r.conf_int().loc[termo]
    return float(np.exp(r.params[termo])), float(np.exp(ci[0])), float(np.exp(ci[1]))


def razoes_por_faixa(r):
    """OR de cada faixa contra a referência, em modelos com C(faixa, Treatment('0-2'))."""
    ci = r.conf_int()
    linhas = []
    for nome in r.params.index:
        m = re.match(r"^C\(faixa.*\)\[T\.(.+)\]$", nome)
        if m:
            linhas.append({
                "faixa": m.group(1),
                "OR": float(np.exp(r.params[nome])),
                "or_inf": float(np.exp(ci.loc[nome, 0])),
                "or_sup": float(np.exp(ci.loc[nome, 1])),
            })
    return pd.DataFrame(linhas, columns=["faixa", "OR", "or_inf", "or_sup"])