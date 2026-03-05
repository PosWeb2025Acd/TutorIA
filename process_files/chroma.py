import os

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_DB_PATH = os.path.dirname(__file__) + '/../db/tutor_ia_acd_db'
EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
DATABASE_TUTOR_IA_ACD_COLLECTION = "acd_collection"

def get_chroma_db():
    # Based on tutorial from the langchain library https://python.langchain.com/docs/tutorials/rag/
    # Embedding model: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 (Modelo especializado em busca por similaridade de texto)
    # -- Modelo cria um vetores com 384 dimensões
    embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    return Chroma(
        collection_name=DATABASE_TUTOR_IA_ACD_COLLECTION,
        embedding_function=embedding_model,
        persist_directory=CHROMA_DB_PATH,
    )
