"""Gráficos do tempo de resposta (> 10 dias) a partir do PostgreSQL.

Requisitos: pip install pandas matplotlib sqlalchemy psycopg2-binary
Grava os gráficos em outputs/tempo_resposta/.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "tempo_resposta"
OUT.mkdir(parents=True, exist_ok=True)
load_dotenv(dotenv_path=ROOT / ".env")


_PARAMS = dict(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    dbname=os.getenv("DB_NAME"),
    port=os.getenv("DB_PORT")
)




CONEXAO = f"postgresql+psycopg2://{_PARAMS['user']}:{_PARAMS['password']}@{_PARAMS['host']}:{_PARAMS['port']}/{_PARAMS['dbname']}"
MIN_RESPONDIDAS = 100  # mínimo de respostas para uma empresa entrar no ranking
TOP_N = 15

engine = create_engine(CONEXAO)


def consulta(sql):
    with engine.connect() as con:
        return pd.read_sql(text(sql), con)


# # ---------- 1) Taxa por empresa ----------
# empresas = consulta(f"""
#     SELECT nome_fantasia,
#            COUNT(*) AS respondidas,
#            COUNT(*) FILTER (WHERE tempo_resposta > 10) AS acima_10,
#            ROUND(100.0 * COUNT(*) FILTER (WHERE tempo_resposta > 10) / COUNT(*), 2) AS pct_acima_10
#     FROM ocorrencias
#     WHERE tempo_resposta IS NOT NULL
#     GROUP BY nome_fantasia
#     HAVING COUNT(*) >= {MIN_RESPONDIDAS}
# """)

# top = empresas.sort_values("pct_acima_10", ascending=False).head(TOP_N)
# top = top.iloc[::-1]  # inverte para a maior ficar no topo do gráfico

# fig, ax = plt.subplots(figsize=(10, 7))
# ax.barh(top["nome_fantasia"], top["pct_acima_10"], color="#2E75B6")
# for y, (pct, n) in enumerate(zip(top["pct_acima_10"], top["respondidas"])):
#     ax.text(pct, y, f"  {pct:.1f}%  (n={n:,})".replace(",", "."), va="center", fontsize=8)
# ax.set_xlabel("% das respostas acima de 10 dias")
# ax.set_title(f"Top {TOP_N} empresas por % de < 10 dias (mín. {MIN_RESPONDIDAS} respondidas)")
# ax.set_xlim(0, top["pct_acima_10"].max() * 1.3)
# plt.tight_layout()
# plt.savefig(OUT / "grafico_empresas_taxa.png", dpi=150)
# plt.close()

# # ---------- 2) Dispersão: volume x taxa ----------
# fig, ax = plt.subplots(figsize=(10, 7))
# ax.scatter(empresas["respondidas"], empresas["pct_acima_10"], alpha=0.6, color="#2E75B6")
# ax.set_xscale("log")
# ax.set_xlabel("Reclamações respondidas (escala log)")
# ax.set_ylabel("% acima de 10 dias")
# ax.set_title("Volume x taxa de respostas acima de 10 dias, por empresa")
# for _, r in empresas.sort_values("acima_10", ascending=False).head(8).iterrows():
#     ax.annotate(r["nome_fantasia"], (r["respondidas"], r["pct_acima_10"]), fontsize=8,
#                 xytext=(4, 4), textcoords="offset points")
# plt.tight_layout()
# plt.savefig(OUT / "grafico_dispersao.png", dpi=150)
# plt.close()

# # ---------- 3) Taxa por mês ----------
# meses = consulta("""
#     SELECT ano_mes,
#            COUNT(*) AS respondidas,
#            COUNT(*) FILTER (WHERE tempo_resposta > 10) AS acima_10,
#            ROUND(100.0 * COUNT(*) FILTER (WHERE tempo_resposta > 10) / COUNT(*), 2) AS pct_acima_10
#     FROM ocorrencias
#     WHERE tempo_resposta IS NOT NULL
#     GROUP BY ano_mes
#     ORDER BY ano_mes
# """)

# fig, ax = plt.subplots(figsize=(11, 5))
# ax.bar(meses["ano_mes"], meses["pct_acima_10"], color="#2E75B6")
# ax.set_ylabel("% acima de 10 dias")
# ax.set_title("% de respostas acima de 10 dias, por mês")
# plt.xticks(rotation=60, ha="right")
# plt.tight_layout()
# plt.savefig(OUT / "grafico_por_mes.png", dpi=150)
# plt.close()


# -------- 4) taxa por dia ---------

dias = consulta("""SELECT data_finalizacao AS dia,
       COUNT(*) AS respondidas,
       COUNT(*) FILTER (WHERE tempo_resposta > 10) AS acima_10,
       ROUND(100.0 * COUNT(*) FILTER (WHERE tempo_resposta > 10) / COUNT(*), 2) AS pct_acima_10
FROM ocorrencias
WHERE tempo_resposta >= 0
  AND ano_mes BETWEEN '2025-10' AND '2026-08'
GROUP BY data_finalizacao
ORDER BY data_finalizacao;""")

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(dias["dia"], dias["pct_acima_10"], color="#2E75B6")
ax.set_ylabel("% acima de 10 dias")
ax.set_title("% de respostas acima de 10 dias, por dia")
plt.xticks(rotation=60, ha="right")
plt.tight_layout()
plt.savefig(OUT / "grafico_por_dia.png", dpi=150)
plt.close()

print(f"Gerados em {OUT}: grafico_empresas_taxa.png, grafico_dispersao.png, grafico_por_mes.png, grafico_por_dia.png")