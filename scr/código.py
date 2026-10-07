import re
import unicodedata
import pandas as pd

ARQUIVO = "finalizadas_2026-08.csv"

df = pd.read_csv(
    ARQUIVO,
    sep=";",
    encoding="utf-8",   # se aparecerem símbolos estranhos, teste "utf-8"
    decimal=",",
    low_memory=False,
)

def limpar_nome(c):
    c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode()
    return re.sub(r"\W+", "_", c.strip().lower()).strip("_")

df.columns = [limpar_nome(c) for c in df.columns]

# print(list(df.columns))
# print(df.dtypes)
# print(df.isna().mean().sort_values(ascending=False).round(3))
# print(df["situacao"].value_counts())
# print(df["avaliacao_reclamacao"].value_counts())


print(df["data_finalizacao"].head().tolist())
df["data_finalizacao"] = pd.to_datetime(df["data_finalizacao"], format="ISO8601")

# tempo_resposta nulo coincide com não respondida?
print(df["data_finalizacao"].min(), df["data_finalizacao"].max())
print(df["data_finalizacao"].isna().mean())  

# taxa de resolução entre avaliadas, por segmento (volume mínimo de 500)
av = df[df["situacao"] == "Finalizada avaliada"]
seg = (av.groupby("segmento_de_mercado")["avaliacao_reclamacao"]
         .agg(n="size", resolvida=lambda s: (s == "Resolvida").mean()))
print(seg[seg["n"] >= 500].sort_values("resolvida"))

print(pd.crosstab(av["respondida"], av["avaliacao_reclamacao"], normalize="index").round(3))
print(av.groupby("avaliacao_reclamacao")["tempo_resposta"].describe())