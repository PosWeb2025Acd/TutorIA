import os
import psycopg

POSTGRES_CONNECTION = 'postgresql://' + os.getenv("DB_USER") + ':' + os.getenv("DB_PASSWORD") + '@localhost:5432/' + os.getenv("DB_NAME") + '?sslmode=disable'

def get_db_connection():
    """
    Estabelece conexão com o banco de dados PostgreSQL
    """

    try:
        conn = psycopg.connect(POSTGRES_CONNECTION)
        return conn
    except psycopg.Error as e:
        print(f"Erro ao conectar com o banco de dados: {e}")
        raise
