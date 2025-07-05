import os

from langchain_core.vectorstores import InMemoryVectorStore

DB_PATH = os.getcwd() + '/rag_db'

def add_chunks_to_db_and_return_db(chunks, embedding):
    if os.path.exists(DB_PATH):
        db = InMemoryVectorStore.load(path=DB_PATH, embedding=embedding)
        print(f"Loaded existing database from {DB_PATH}")
    else:
        db = InMemoryVectorStore(embedding=embedding)
        ids = [chunk.metadata["page_id"] for chunk in chunks]
        db.add_documents(chunks, ids)
        db.dump(DB_PATH)

    return db
