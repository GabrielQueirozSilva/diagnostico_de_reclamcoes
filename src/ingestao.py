from datetime import datetime
import glob
import os
import re
import unicodedata
from pathlib import Path
from dotenv import load_dotenv
import pandas as pd
import psycopg2
from psycopg2 import errors, sql
from psycopg2.extras import execute_values

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(dotenv_path=ROOT / ".env")

COLUNAS = [
    "regiao",
    "uf",
    "cidade",
    "sexo",
    "faixa_etaria",
    "data_finalizacao",
    "tempo_resposta",
    "nome_fantasia",
    "segmento_de_mercado",
    "area",
    "assunto",
    "grupo_problema",
    "problema",
    "como_comprou_contratou",
    "procurou_empresa",
    "respondida",
    "situacao",
    "avaliacao_reclamacao",
    "nota_do_consumidor",
    "ano_mes",
]

_PARAMS = dict(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)


def create_database_if_not_exists():
  db = os.getenv("DB_NAME")
  if not db:
    raise ValueError("Database name not found in environment variables.")

  conn = psycopg2.connect(**_PARAMS)
  try:
    conn.autocommit = True
    with conn.cursor() as cur:
      try:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db)))
        print(f"Database '{db}' created successfully.")
      except errors.DuplicateDatabase:
        print(f"Database '{db}' already exists.")
  finally:
    conn.close()


def create_table_database_if_not_exists():
  conn = psycopg2.connect(**_PARAMS, dbname=os.getenv("DB_NAME"))
  try:
    with conn.cursor() as cur:
      cur.execute("""
                CREATE TABLE IF NOT EXISTS ocorrencias (
                    id SERIAL PRIMARY KEY,
                    regiao VARCHAR(2),
                    uf VARCHAR(2),
                    cidade VARCHAR(255) NOT NULL,
                    sexo VARCHAR(1),
                    faixa_etaria VARCHAR(50),
                    data_finalizacao DATE,
                    tempo_resposta INT,
                    nome_fantasia VARCHAR(255),
                    segmento_de_mercado VARCHAR(255),
                    area VARCHAR(255),
                    assunto VARCHAR(255),
                    grupo_problema VARCHAR(255),
                    problema VARCHAR(255),
                    como_comprou_contratou VARCHAR(255),
                    procurou_empresa VARCHAR(1),
                    respondida VARCHAR(1),
                    situacao VARCHAR(255),
                    avaliacao_reclamacao VARCHAR(255),
                    nota_do_consumidor INT,
                    ano_mes VARCHAR(7)
                )
            """)
      cur.execute("""
        SELECT
          EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'ocorrencias'
              AND column_name = 'mes_ano'
          ),
          EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'ocorrencias'
              AND column_name = 'ano_mes'
          )
      """)
      has_mes_ano, has_ano_mes = cur.fetchone()
      if has_mes_ano and has_ano_mes:
        raise RuntimeError(
            "The 'ocorrencias' table contains both 'mes_ano' and 'ano_mes'."
        )
      if has_mes_ano:
        cur.execute(
            "ALTER TABLE ocorrencias RENAME COLUMN mes_ano TO ano_mes"
        )
      conn.commit()
      print("Table 'ocorrencias' created successfully or already exists.")
  finally:
    conn.close()


def insert_data_to_database(data, batch_size=10_000):
  df = data[COLUNAS].copy()
  df["tempo_resposta"] = (df["tempo_resposta"].astype("str").str.replace(",", ".", regex=False).astype(float).astype("Int64"))
  df["nota_do_consumidor"] = df["nota_do_consumidor"].astype("str").str.replace(",", ".", regex=False).astype(float).astype("Int64")
  df = df.astype(object).where(df.notna(), None)
  registros = list(df.itertuples(index=False, name=None))

  query = sql.SQL("INSERT INTO ocorrencias ({}) VALUES %s").format(
      sql.SQL(", ").join(map(sql.Identifier, COLUNAS))
  )

  conn = psycopg2.connect(**_PARAMS, dbname=os.getenv("DB_NAME"))
  try:
    with conn.cursor() as cur:
      execute_values(cur, query, registros, page_size=batch_size)
    conn.commit()
    print(f"{len(registros)} registros inseridos.")
  except Exception:
    conn.rollback()
    raise
  finally:
    conn.close()


if __name__ == "__main__":
  padrao_arquivos = str(ROOT / "data" / "*.csv")
  arquivos = glob.glob(padrao_arquivos)

  if not arquivos:
    print("Nenhum arquivo CSV encontrado na pasta.")
  else:
    create_database_if_not_exists()
    create_table_database_if_not_exists()

    def limpar_nome(c):
      c = unicodedata.normalize("NFKD", c).encode("ascii", "ignore").decode()
      return re.sub(r"\W+", "_", c.strip().lower()).strip("_")

    for arquivo in arquivos:
      print(f"\nProcessando arquivo: {arquivo}")

      match_data = re.search(r"(\d{4}-\d{2})", arquivo)
      if match_data:
        ano_mes_str = match_data.group(1)
      else:
        ano_mes_str = "Desconhecido"

      df = pd.read_csv(
          arquivo,
          sep=";",
          encoding="utf-8",
          decimal=",",
          low_memory=False,
      )

      df.columns = [limpar_nome(c) for c in df.columns]
      df["data_finalizacao"] = pd.to_datetime(
          df["data_finalizacao"], errors="coerce"
      )
      df["ano_mes"] = ano_mes_str
      insert_data_to_database(df)

    print("\nProcessamento e inserção de todos os meses concluídos com sucesso!")