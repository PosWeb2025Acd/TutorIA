import os

from langchain_core.vectorstores import InMemoryVectorStore
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from process_files import load_pages, create_pages_chunks, create_chunk_ids

CHROMA_DB_PATH = os.getcwd() + '/tutor_ia_acd_db'
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
DATABASE_NAME = "tutor_ia"
DATABASE_TUTOR_IA_ACD_COLLECTION = "acd_collection"
MEMORY_DB_PATH = os.getcwd() + '/rag_db'
HUGGING_FACE_TOKEN_PATH = os.getcwd() + '/hugging_face_token'

def load_huggingface_token():
    with open(HUGGING_FACE_TOKEN_PATH, 'r') as file:
        return file.read().strip()

os.environ["HUGGINGFACEHUB_API_TOKEN"] = load_huggingface_token()

def _create_in_memory_db(chunks, embedding):
    if os.path.exists(MEMORY_DB_PATH):
        db = InMemoryVectorStore.load(path=MEMORY_DB_PATH, embedding=embedding)
        print(f"Loaded existing database from {MEMORY_DB_PATH}")
    else:
        db = InMemoryVectorStore(embedding=embedding)
        ids = [chunk.metadata["page_id"] for chunk in chunks]
        db.add_documents(chunks, ids)
        db.dump(MEMORY_DB_PATH)

def _create_chroma_db(chunks, embedding):
    db = Chroma(
        collection_name=DATABASE_TUTOR_IA_ACD_COLLECTION,
        embedding_function=embedding,
        persist_directory=CHROMA_DB_PATH,
    )
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

def _add_chunks_to_db(chunks, embedding, in_memory=True):
    if in_memory:
        return _create_in_memory_db(chunks, embedding)

    return _create_chroma_db(chunks, embedding)

def _get_in_memory_db(embedding):
    if os.path.exists(MEMORY_DB_PATH):
        db = InMemoryVectorStore.load(path=MEMORY_DB_PATH, embedding=embedding)
        print(f"Loaded existing database from {MEMORY_DB_PATH}")
    else:
        db = InMemoryVectorStore(embedding=embedding)

    return db

def _get_chroma_db(embedding):
    return Chroma(
        collection_name=DATABASE_TUTOR_IA_ACD_COLLECTION,
        embedding_function=embedding,
        persist_directory=CHROMA_DB_PATH,
    )

def get_db(in_memory=True):
    emebedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    if in_memory:
        return _get_in_memory_db(emebedding_model)
    
    return _get_chroma_db(emebedding_model)

if __name__ == "__main__":
    emebedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    print("Loading pages...")
    pages = load_pages()
    print("Creating chunks...")
    chunks = create_pages_chunks(pages)
    chunks = create_chunk_ids(chunks)

    print("Adding chunks to database...")
    _add_chunks_to_db(chunks, emebedding_model, in_memory=False)
    print("Database created successfully.")
