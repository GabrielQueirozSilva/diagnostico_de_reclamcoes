import re
import unicodedata
import pandas as pd

ARQUIVO = r"data\finalizadas_2026-08.csv"

df = pd.read_csv(
    ARQUIVO,
    sep=";",
    encoding="utf-8",  
    decimal=",",
    low_memory=False,
)

def limpar_nome(c):
    c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode()
    return re.sub(r"\W+", "_", c.strip().lower()).strip("_")

df.columns = [limpar_nome(c) for c in df.columns]


#VERIFICANDO O TAMANHO DE CADA COLUNA

# print(df.select_dtypes(include="object")
#         .apply(lambda s: s.dropna().astype(str).str.len().max()))

#VALORES PADÕRES DE COLUNAS

print(df["tempo_resposta"].value_counts(dropna=False).sort_index().to_string())

print(list(df.columns))
print(df.dtypes)
print(df.isna().mean().sort_values(ascending=False).round(3))
print(df["situacao"].value_counts())
print(df["avaliacao_reclamacao"].value_counts())


# print(df["data_finalizacao"].head().tolist())
# df["data_finalizacao"] = pd.to_datetime(df["data_finalizacao"], format="ISO8601")

# print(df["data_finalizacao"].min(), df["data_finalizacao"].max())
# print(df["data_finalizacao"].isna().mean())  

# av = df[df["situacao"] == "Finalizada avaliada"]
# seg = (av.groupby("segmento_de_mercado")["avaliacao_reclamacao"]
#          .agg(n="size", resolvida=lambda s: (s == "Resolvida").mean()))
# print(seg[seg["n"] >= 500].sort_values("resolvida"))

# print(pd.crosstab(av["respondida"], av["avaliacao_reclamacao"], normalize="index").round(3))
# print(av.groupby("avaliacao_reclamacao")["tempo_resposta"].describe())

# print(df["data_finalizacao"].head())  


# print(df.head(1000))


#Verificação da hiótese 2

# from scipy.stats import chi2_contingency
# a = chi2_contingency([[35, 295], [535, 3274]])

# print(a)


#Verificação de cabeçalhos dos dados

# import glob
# import pandas as pd

# # Defina o caminho para a pasta onde estão seus arquivos CSV
# # Exemplo: 'dados/*.csv' para todos os arquivos CSV em uma pasta
# caminho_padrao = r"C:\Users\gabri\Desktop\projeto02\data\*.csv"

# arquivos = glob.glob(caminho_padrao)

# if not arquivos:
#   print("Nenhum arquivo CSV encontrado.")
# else:
#   # Dicionário para mapear arquivo -> lista de colunas
#   cabecalhos = {}

#   for arquivo in arquivos:
#     # nrows=0 lê apenas o cabeçalho, economizando memória e tempo
#     df = pd.read_csv(arquivo, nrows=0, sep=';', encoding='utf-8', decimal=',')
#     cabecalhos[arquivo] = list(df.columns)

#   # o primeiro arquivo como referência
#   primeiro_arquivo = list(cabecalhos.keys())[0]
#   referencia = cabecalhos[primeiro_arquivo]

#   print(f"--- Arquivo de Referência ---")
#   print(f"Nome: {primeiro_arquivo}")
#   print(f"Colunas: {referencia}\n")

#   print(f"--- Comparação com os demais arquivos ---")
#   todos_iguais = True

#   for arquivo, cols in cabecalhos.items():
#     if arquivo == primeiro_arquivo:
#       continue

#     if cols == referencia:
#       print(f"[OK] {arquivo}: Perfeito (mesmas colunas e ordem).")
#     else:
#       todos_iguais = False
#       print(f"[DIFERENTE] {arquivo}: Divergência encontrada!")
#       print(f"   Encontrado: {cols}")

#       # Dicas extras do que mudou:
#       faltando = set(referencia) - set(cols)
#       extras = set(cols) - set(referencia)
#       if faltando:
#         print(f"   -> Faltando colunas em relação à referência: {faltando}")
#       if extras:
#         print(f"   -> Colunas extras em relação à referência: {extras}")
#       if cols != referencia and not faltando and not extras:
#         print(
#             "   -> As colunas são as mesmas, mas estão em uma **ordem"
#             " diferente**."
#         )
#       print("-" * 40)

#   if todos_iguais:
#     print(
#         "\nSucesso! Todos os arquivos possuem exatamente o mesmo cabeçalho e"
#         " ordem."
#     )
    
    
    
## DESCARTANDO COLUNAS ADICIONAIS

# import pandas as pd

# # Caminho do arquivo que tem as colunas a mais
# caminho_arquivo = (
#     r"C:\Users\gabri\Desktop\projeto02\data\finalizadas_2025-09.csv"
# )

# df = pd.read_csv(caminho_arquivo, sep=";")


# colunas_para_remover = ["Interação com Judiciario", "Último Complemento Consumidor"]


# df = df.drop(columns=colunas_para_remover, errors="ignore")

# df.to_csv(caminho_arquivo, sep=";", index=False, encoding="utf-8")

# print("Colunas removidas e arquivo salvo com sucesso!")


