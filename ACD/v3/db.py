import os

from langchain_chroma import Chroma

CHROMA_DB_PATH = os.getcwd() + '/tutor_ia_acd_db'
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
DATABASE_NAME = "tutor_ia"
DATABASE_TUTOR_IA_ACD_COLLECTION = "acd_collection"

def add_chunks_to_db(chunks, embedding):
    db = get_db(embedding)
    ids = [chunk.metadata["page_id"] for chunk in chunks]
    chunks_found = db.get_by_ids(ids)
    chunks_to_add = []
    for chunk in chunks:
        if chunk.metadata["page_id"] not in [c.metadata["page_id"] for c in chunks_found]:
            chunks_to_add.append(chunk)

    if not chunks_to_add:
        print("No new chunks to add to the database.")
        return db

    ids = [chunk.metadata["page_id"] for chunk in chunks_to_add]
    db.add_documents(documents=chunks_to_add, ids=ids)

    return db

def get_db(embedding_model):
    return Chroma(
        collection_name=DATABASE_TUTOR_IA_ACD_COLLECTION,
        embedding_function=embedding_model,
        persist_directory=CHROMA_DB_PATH,
    )
