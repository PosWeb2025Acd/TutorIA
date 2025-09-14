import os
import psycopg

from psycopg.rows import dict_row

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
POSTGRES_CONNECTION = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=disable"

def get_postgres_connection():
    """
    Estabelece conexão com o banco de dados PostgreSQL
    """

    try:
        conn = psycopg.connect(conninfo=POSTGRES_CONNECTION, row_factory=dict_row)
        return conn
    except psycopg.Error as e:
        print(f"Erro ao conectar com o banco de dados: {e}")
        raise
