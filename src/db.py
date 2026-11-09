""" Script resposável pela conexão com o PostgreSQL.
"""
import os
from pathlib import Path
 
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
 
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")
 
 
def get_engine():
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME"),
    )
    return create_engine(url)
 
