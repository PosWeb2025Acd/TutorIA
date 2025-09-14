import os
from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from psycopg import Connection

load_dotenv(os.path.dirname(__file__) + '/../.env')

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
POSTGRES_CONNECTION = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=disable"

with Connection.connect(POSTGRES_CONNECTION) as conn:
    conn.autocommit = True
    checkpointer = PostgresSaver(conn)
    store = PostgresStore(conn)

    print ("Initialization of postgres rag checkpointer and store")
    checkpointer.setup()
    store.setup()

    conn.close()
